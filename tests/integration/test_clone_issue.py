import os

from .base import IntegrationTestBase

from jirafs import constants


class TestCloneIssue(IntegrationTestBase):
    def test_cloning_issue_basic(self):
        issue_path = os.path.join(self.path, "issue")
        data = {
            "description": "This is a test description",
            "summary": "This is a test summary",
        }

        issue = self.create_issue(data)

        self.run_command(
            "clone", path=issue_path, url=issue.permalink(), jira=self.get_jira
        )

        folder = self.get_ticket_folder_for_path(issue_path)
        fields = folder.get_fields()

        # Assert that the field data is on-disk as expected
        for key, value in data.items():
            self.assertEqual(value, fields.get(key))

    def test_cloning_issue_unicode_fields(self):
        issue_path = os.path.join(self.path, "issue")
        data = {
            "description": u"\u041f\u0440\u0438\u0432\u0435\u0442",
            "summary": u"\u0410\u043b\u043e",
        }

        issue = self.create_issue(data)

        self.run_command(
            "clone", path=issue_path, url=issue.permalink(), jira=self.get_jira
        )

        folder = self.get_ticket_folder_for_path(issue_path)
        fields = folder.get_fields()

        # Assert that the field data is on-disk as expected
        for key, value in data.items():
            self.assertEqual(value, fields.get(key))

    def test_cloning_issue_files_exist(self):
        issue_path = os.path.join(self.path, "issue")
        data = {
            "description": "This is a test description",
            "summary": "This is a test summary",
        }

        issue = self.create_issue(data)

        self.run_command(
            "clone", path=issue_path, url=issue.permalink(), jira=self.get_jira
        )

        folder = self.get_ticket_folder_for_path(issue_path)

        description_filename = constants.TICKET_FILE_FIELD_TEMPLATE.format(
            field_name="description"
        )
        expected_files = [
            constants.TICKET_DETAILS,
            constants.TICKET_COMMENTS,
            constants.TICKET_NEW_COMMENT,
            constants.TICKET_LINKS,
            description_filename,
        ]
        all_files = os.listdir(issue_path)

        for filename in expected_files:
            self.assertIn(filename, all_files)

        with open(folder.get_path(description_filename), "r") as handle:
            self.assertEqual(
                data["description"], handle.read().strip(),
            )

    def test_post_cloning_status(self):
        issue_path = os.path.join(self.path, "issue")
        data = {
            "description": "This is a test description",
            "summary": "This is a test summary",
        }

        issue = self.create_issue(data)

        self.run_command(
            "clone", path=issue_path, url=issue.permalink(), jira=self.get_jira
        )

        stdout = self.run_command(
            "status", method="cmd", folder=self.get_ticket_folder_for_path(issue_path)
        )

        assert_strings = [
            "On ticket %s" % issue.key,
            "browse/%s" % issue.key,
            "No changes found",
        ]
        for expectation in assert_strings:
            self.assertIn(
                expectation, stdout,
            )
