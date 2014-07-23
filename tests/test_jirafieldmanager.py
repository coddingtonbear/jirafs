from textwrap import dedent
from unittest import TestCase

from mock import patch

from jirafs.jirafieldmanager import LocalFileJiraFieldManager


class TestJiraFieldManager(TestCase):
    def setUp(self):
        with patch(
            'jirafs.jirafieldmanager.JiraFieldManager.load'
        ):
            self.jirafieldmanager = LocalFileJiraFieldManager(None, None)

    def test_decode(self):
        encoded_values = dedent("""
            * summary:
                This is a test summary
            * longer_message:
                This is a much
                longer message that happens
                to contain newlines.
        """)

        expected_result = {
            'summary': 'This is a test summary',
            'longer_message': (
                'This is a much\n'
                'longer message that happens\n'
                'to contain newlines.'
            )
        }

        actual_result = self.jirafieldmanager.get_fields_from_string(
            encoded_values
        )

        self.assertEqual(
            expected_result,
            actual_result
        )
