from textwrap import dedent
from unittest import TestCase

from jirafs.jirafieldmanager import JiraFieldManager


class TestJiraFieldManager(TestCase):
    def test_decode(self):
        encoded_values = dedent(
            """
            * summary (summary):
                This is a test summary
            * Longer Message (longer_message):
                This is a much
                longer message that happens
                to contain newlines.
        """
        )

        expected_result = {
            "summary": "This is a test summary",
            "longer_message": (
                "This is a much\n"
                "longer message that happens\n"
                "to contain newlines."
            ),
        }

        actual_result = JiraFieldManager(encoded_values)

        self.assertEqual(expected_result, actual_result)

    def test_decode_with_json_values(self):
        encoded_values = dedent(
            """
            * Dictionary Field (dictionary_field):
                {
                    "name": "Adam Coddington"
                }
            * Integer Field (integer_field):
                10
            * String Field (string_field):
                Hello
            * List Field (list_field):
                [
                    "Alphabet",
                    {
                        "One": "Two"
                    }
                ]
        """
        )

        expected_result = {
            "dictionary_field": {"name": "Adam Coddington"},
            "integer_field": 10,
            "string_field": "Hello",
            "list_field": ["Alphabet", {"One": "Two",}],
        }

        actual_result = JiraFieldManager(encoded_values)

        self.assertEqual(
            expected_result, actual_result,
        )
