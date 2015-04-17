from textwrap import dedent
from unittest import TestCase

from mock import patch

from jirafs.jirafieldmanager import JiraFieldManager


class TestJiraFieldManager(TestCase):
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

        actual_result = JiraFieldManager(
            encoded_values
        )

        self.assertEqual(
            expected_result,
            actual_result
        )

    def test_decode_with_json_values(self):
        encoded_values = dedent("""
            * dictionary_field:
                {
                    "name": "Adam Coddington"
                }
            * integer_field:
                10
            * string_field:
                Hello
            * list_field:
                [
                    "Alphabet",
                    {
                        "One": "Two"
                    }
                ]
        """)

        expected_result = {
            "dictionary_field": {
                "name": "Adam Coddington"
            },
            "integer_field": 10,
            "string_field": "Hello",
            "list_field": [
                "Alphabet",
                {
                    "One": "Two",
                }
            ]
        }

        actual_result = JiraFieldManager(
            encoded_values
        )

        self.assertEqual(
            expected_result,
            actual_result,
        )

    def test_decode_with_human_readable_field_names(self):
        encoded_values = dedent("""
            * Summary:
                This is a test summary
            * Longer Message:
                This is a much
                longer message that happens
                to contain newlines.
            * Something(s) that are Company-Specific (customfield_108234):
                This is something else
        """)

        expected_result = {
            'Summary': 'This is a test summary',
            'Longer_Message': (
                'This is a much\n'
                'longer message that happens\n'
                'to contain newlines.'
            ),
            'customfield_108234': (
                'This is something else'
            )
        }

        actual_result = JiraFieldManager(
            encoded_values
        )

        self.assertEqual(
            expected_result,
            actual_result
        )

