from mock import patch

from jirafs.plugin import CommandResult

from .base import BaseTestCase


class TestCommandResult(BaseTestCase):
    def test_echo_cursor(self):
        with patch.object(CommandResult, "_echo") as out:
            lines = [
                "Line 1",
                "Line 2",
            ]
            result = CommandResult(lines[0]).echo()
            result = result.add_line(lines[1]).echo()

            self.assertTrue(len(out.call_args_list), 2)

            for idx, line in enumerate(lines):
                args, _ = out.call_args_list[idx]

                self.assertEqual(args[0], line + "\n")
