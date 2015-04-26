import os

from .base import IntegrationTestBase


class TestCloneIssue(IntegrationTestBase):
    def test_cloning_issue(self):
        issue_path = os.path.join(self.path, 'issue')
        data = {
            'description': 'This is a test description',
            'summary': 'This is a test summary',
        }

        issue = self.create_issue(data)

        self.run_command(
            'clone',
            path=issue_path,
            url=issue.permalink(),
            jira=self.get_jira
        )

        folder = self.get_ticket_folder_for_path(issue_path)
        fields = folder.get_fields()

        # Assert that the field data is on-disk as expected
        for key, value in data.items():
            self.assertEqual(value, fields.get(key))
