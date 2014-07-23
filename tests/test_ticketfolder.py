import json
import os
import shutil
import tempfile
from unittest import TestCase

import mock
from mock import patch
from jira.resources import Issue

from jirafs import exceptions
from jirafs.ticketfolder import TicketFolder


class BaseTestCase(TestCase):
    def get_asset_path(self, filename):
        return os.path.join(
            os.path.dirname(__file__),
            'assets',
            filename
        )

    def get_asset_contents(self, filename, mode='r'):
        path = self.get_asset_path(filename)

        with open(path, mode) as r:
            return r.read()

    def rehydrate_issue(self, filename):
        stored = json.loads(self.get_asset_contents(filename))
        return Issue(
            stored['options'],
            None,
            stored['raw'],
        )

    def get_empty_status(self):
        return {
            'ready': {
                'files': [],
                'fields': {},
                'new_comment': '',
            },
            'uncommitted': {
                'files': [],
                'fields': {},
                'new_comment': '',
            },
            'up_to_date': True,
        }


class TestTicketFolder(BaseTestCase):
    def setUp(self):
        self.arbitrary_ticket_number = 'ALPHA-123'
        self.root_folder = tempfile.mkdtemp()
        self.mock_jira = mock.MagicMock()
        self.mock_jira.issue.return_value = self.rehydrate_issue(
            'basic.issue.json'
        )
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
            'comments.read_only.jira',
            'fields.jira',
            'description.jira',
            'new_comment.jira',
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

    def test_get_fields(self):
        actual_result = self.ticketfolder.get_fields()

        expected_result = json.loads(
            self.get_asset_contents('basic.status.json')
        )

        self.assertEquals(
            actual_result,
            expected_result
        )

    def test_fetch(self):
        self.ticketfolder._issue = (
            self.rehydrate_issue('test_fetch/fetched.json')
        )
        self.ticketfolder.fetch()

        expected_result = self.get_asset_contents('test_fetch/fetched.jira')
        with open(self.ticketfolder.get_shadow_path('fields.jira')) as _in:
            actual_result = _in.read()

        self.assertEqual(actual_result, expected_result)

    def test_push(self):
        changed_field = 'description'
        changed_value = 'Something Else'

        status = self.get_empty_status()
        status['ready']['fields'][changed_field] = (
            'Something', changed_value,
        )
        with patch.object(self.ticketfolder, 'status') as status_method:
            status_method.return_value = status
            with patch.object(self.ticketfolder.issue, 'update') as out:
                self.ticketfolder.push()
                out.assert_called_with(
                    **{
                        'description': changed_value
                    }
                )

    def test_push_rejected_if_updated(self):
        src_path = self.get_asset_path('test_fetch/fetched.jira')
        dst_path = self.ticketfolder.get_shadow_path('fields.jira')
        shutil.copyfile(
            src_path,
            dst_path,
        )

        self.ticketfolder.run_git_command('add', '-A', shadow=True)
        self.ticketfolder.run_git_command(
            'commit', '-m', 'Changed', shadow=True
        )
        self.ticketfolder.run_git_command(
            'push', 'origin', 'jira', shadow=True
        )
        with self.assertRaises(exceptions.LocalCopyOutOfDate):
            self.ticketfolder.push()

    def test_status_new_file(self):
        src_path = self.get_asset_path('test_status_local_changes/alpha.svg')
        dst_path = self.ticketfolder.get_local_path('alpha.svg')
        shutil.copyfile(
            src_path,
            dst_path,
        )

        expected_output = self.get_empty_status()
        expected_output['uncommitted']['files'] = ['alpha.svg']
        actual_output = self.ticketfolder.status()

        self.assertEqual(expected_output, actual_output)

    def test_status_local_changes(self):
        src_path = self.get_asset_path('test_fetch/fetched.jira')
        dst_path = self.ticketfolder.get_local_path('fields.jira')
        shutil.copyfile(
            src_path,
            dst_path,
        )

        expected_output = self.get_empty_status()
        expected_output['uncommitted']['fields']['assignee'] = (
            '', 'Coddington, Adam (ArbitraryCorp-Atlantis)'
        )
        actual_output = self.ticketfolder.status()

        self.assertEqual(expected_output, actual_output)

    def test_status_new_comment(self):
        arbitrary_comment = 'New Comment'

        comment = self.ticketfolder.get_local_path('new_comment.jira')
        with open(comment, 'w') as out:
            out.write(arbitrary_comment)

        expected_output = self.get_empty_status()
        expected_output['uncommitted']['new_comment'] = arbitrary_comment
        actual_output = self.ticketfolder.status()

        self.assertEqual(expected_output, actual_output)

    def tearDown(self):
        shutil.rmtree(self.root_folder)
