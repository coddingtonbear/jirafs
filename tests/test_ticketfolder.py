import json
import os
import shutil
import tempfile
from unittest import TestCase

import mock
from mock import patch
from jira.resources import Issue

from jirafs.ticketfolder import TicketFolder


class BaseTestCase(TestCase):
    def get_asset_path(self, filename):
        return os.path.join(
            os.path.dirname(__file__),
            'assets',
            filename
        )

    def get_asset_contents(self, filename, mode='rb'):
        path = self.get_asset_path(filename)

        with open(path, mode) as r:
            return r.read()

    def rehydrate_issue(self, filename):
        stored = json.loads(self.get_asset_contents(filename, mode='r'))
        return Issue(
            stored['options'],
            None,
            stored['raw'],
        )


class TestTicketFolderClone(BaseTestCase):
    def setUp(self):
        self.arbitrary_ticket_number = 'ALPHA-123'
        self.root_folder = tempfile.mkdtemp()
        self.mock_jira = mock.MagicMock()
        self.mock_jira.issue.return_value = self.rehydrate_issue('basic.json')
        self.mock_get_jira = lambda: self.mock_jira

    @patch('jirafs.ticketfolder.TicketFolder.get_remotely_changed')
    def test_clone_issue(self, get_remotely_changed):
        issue = TicketFolder.clone(
            os.path.join(
                self.root_folder,
                self.arbitrary_ticket_number
            ),
            jira=self.mock_get_jira
        )

        get_remotely_changed.return_value = []
        issue.sync()

        paths = [
            'comments.read_only.jira.rst',
            'fields.jira.rst',
            'description.jira.rst',
            'new_comment.jira.rst',
            '.jirafs/gitignore',
            '.jirafs/issue.json',
            '.jirafs/operation.log',
            '.jirafs/remote_files.json',
            '.jirafs/version',
        ]
        for path in paths:
            self.assertTrue(
                os.path.isfile(
                    issue.get_local_path(path)
                ),
                '%s does not exist' % path
            )

    def tearDown(self):
        shutil.rmtree(self.root_folder)
