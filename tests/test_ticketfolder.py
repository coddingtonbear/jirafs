import io
import json
import os
import shutil
import tempfile

import mock
from mock import patch
import six

from jirafs import exceptions
from jirafs.utils import run_command_method_with_kwargs
from jirafs.jirafieldmanager import JiraFieldManager

from .base import BaseTestCase


class TestTicketFolder(BaseTestCase):
    def setUp(self):
        self.arbitrary_ticket_number = "ALPHA-123"
        self.root_folder = tempfile.mkdtemp()
        self.mock_jira = mock.MagicMock()
        self.mock_jira.issue.return_value = self.rehydrate_issue("basic.issue.json")
        self.mock_get_jira = lambda _, config=None: self.mock_jira

        with patch(
            "jirafs.ticketfolder.TicketFolder.get_remotely_changed"
        ) as get_remotely_changed:
            get_remotely_changed.return_value = []
            self.ticketfolder = run_command_method_with_kwargs(
                "clone",
                url="http://arbitrary.com/browse/ALPHA-123",
                jira=self.mock_get_jira,
                path=os.path.join(self.root_folder, self.arbitrary_ticket_number,),
            )

    def test_cloned_issue_successfully(self):
        paths = [
            "comments.read_only.jira",
            "fields.jira",
            "description.jira",
            "new_comment.jira",
            ".jirafs/issue.json",
            ".jirafs/remote_files.json",
            ".jirafs/version",
        ]
        for path in paths:
            self.assertTrue(
                os.path.isfile(self.ticketfolder.get_local_path(path)),
                "%s does not exist" % path,
            )
            # Ensure that the file is tracked in git
            try:
                self.ticketfolder.run_git_command("ls-files", path, "--error-unmatch")
            except exceptions.GitCommandError:
                self.fail("File %s is not tracked in the git repository.")

    def test_get_fields(self):
        actual_result = self.ticketfolder.get_fields()

        expected_result = json.loads(self.get_asset_contents("basic.status.json"))

        self.assertEquals(actual_result, expected_result)

    def test_fetch(self):
        self.ticketfolder._issue = self.rehydrate_issue("test_fetch/fetched.json")
        with patch.object(self.ticketfolder, "clear_cache") as clear_cache:
            run_command_method_with_kwargs(
                "fetch", folder=self.ticketfolder,
            )
            self.assertTrue(clear_cache.called)

        expected_result = JiraFieldManager(
            self.get_asset_contents("test_fetch/fetched.jira")
        )
        with io.open(
            self.ticketfolder.get_shadow_path("fields.jira"), encoding="utf-8"
        ) as _in:
            actual_result = JiraFieldManager(_in.read())

        self.assertEqual(actual_result, expected_result)

    def test_push(self):
        changed_field = u"description"
        changed_value = u"Something Else"

        status = self.get_empty_status()
        status["ready"]["fields"][changed_field] = (
            u"Something",
            changed_value,
            changed_value,
        )
        with patch("jirafs.commands.pull.Command.main") as pull:
            with patch.object(self.ticketfolder, "status") as status_method:
                status_method.return_value = status
                with patch.object(self.ticketfolder.issue, "update") as out:
                    run_command_method_with_kwargs("push", folder=self.ticketfolder)
                    self.assertTrue(pull.called)
                    out.assert_called_with(**{"description": changed_value})

    def test_push_rejected_if_updated(self):
        src_path = self.get_asset_path("test_fetch/fetched.jira")
        dst_path = self.ticketfolder.get_shadow_path("fields.jira")
        shutil.copyfile(
            src_path, dst_path,
        )

        self.ticketfolder.run_git_command("add", "-A", shadow=True)
        self.ticketfolder.run_git_command("commit", "-m", "Changed", shadow=True)
        self.ticketfolder.run_git_command("push", "origin", "jira", shadow=True)
        with self.assertRaises(exceptions.LocalCopyOutOfDate):
            run_command_method_with_kwargs("push", folder=self.ticketfolder)

    def test_status_new_file(self):
        src_path = self.get_asset_path("test_status_local_changes/alpha.svg")
        dst_path = self.ticketfolder.get_local_path("alpha.svg")
        shutil.copyfile(
            src_path, dst_path,
        )

        expected_output = self.get_empty_status()
        expected_output["uncommitted"]["files"] = ["alpha.svg"]
        actual_output = self.ticketfolder.status()

        self.assertEqual(expected_output, actual_output)

    def test_status_local_changes(self):
        src_path = self.get_asset_path("test_fetch/fetched.jira")
        dst_path = self.ticketfolder.get_local_path("fields.jira")
        shutil.copyfile(
            src_path, dst_path,
        )

        expected_output = self.get_empty_status()
        expected_output["uncommitted"]["fields"]["assignee"] = (
            "",
            {
                "active": True,
                "displayName": (
                    u"Coddington, Adam (\u0410\u0440\u0431\u0438\u0442"
                    u"\u0440\u0430\u0440\u0438\u041a\u043e\u0440\u043f"
                    u"-Atlantis)"
                ),
                "name": "acoddington",
            },
            {
                "active": True,
                "displayName": (
                    u"Coddington, Adam (\u0410\u0440\u0431\u0438\u0442"
                    u"\u0440\u0430\u0440\u0438\u041a\u043e\u0440\u043f"
                    u"-Atlantis)"
                ),
                "name": "acoddington",
            },
        )
        actual_output = self.ticketfolder.status()

        for field in expected_output:
            if expected_output[field] != actual_output[field]:
                self.fail(
                    "Field %s does not match; Actual: %s != Expected: %s"
                    % (field, actual_output[field], expected_output[field],)
                )

        self.assertEqual(expected_output, actual_output)

    def test_status_new_comment(self):
        arbitrary_comment = six.text_type("New Comment")

        comment = self.ticketfolder.get_local_path("new_comment.jira")
        with io.open(comment, "w", encoding="utf-8") as out:
            out.write(arbitrary_comment)

        expected_output = self.get_empty_status()
        expected_output["uncommitted"]["new_comment"] = arbitrary_comment
        actual_output = self.ticketfolder.status()

        self.assertEqual(expected_output, actual_output)

    def tearDown(self):
        shutil.rmtree(self.root_folder)
