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


class TestTicketFolder(BaseTestCase):
    def setUp(self):
        self.arbitrary_ticket_number = 'ALPHA-123'
        self.root_folder = tempfile.mkdtemp()
        self.mock_jira = mock.MagicMock()
        self.mock_jira.issue.return_value = self.rehydrate_issue('basic.json')
        self.mock_get_jira = lambda: self.mock_jira

        with patch(
            'jirafs.ticketfolder.TicketFolder.get_remotely_changed'
        ) as get_remotely_changed:
            get_remotely_changed.return_value = []
            self.ticketfolder = TicketFolder.clone(
                os.path.join(
                    self.root_folder,
                    self.arbitrary_ticket_number,
                ),
                jira=self.mock_get_jira
            )

    def test_cloned_issue_successfully(self):
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
                    self.ticketfolder.get_local_path(path)
                ),
                '%s does not exist' % path
            )

    def test_get_local_fields(self):
        actual_result = self.ticketfolder.get_local_fields()

        expected_result = json.loads(
            self.get_asset_contents('basic_status.json', 'r')
        )

        self.assertEquals(
            actual_result,
            expected_result
        )

    def tearDown(self):
        shutil.rmtree(self.root_folder)
