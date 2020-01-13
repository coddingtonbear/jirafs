from mock import call, patch

from jirafs.utils import run_command_method_with_kwargs

from .base import BaseCommandTestCase


class TestPushCommand(BaseCommandTestCase):
    def setUp(self):
        super(TestPushCommand, self).setUp()

    def test_push_no_changes(self):
        with patch.object(self.ticketfolder.issue, "update") as update:
            with patch("jirafs.commands.pull.Command.main") as pull:
                pull.return_value = True, True
                run_command_method_with_kwargs(
                    "push", folder=self.ticketfolder,
                )

            self.assertEqual(0, len(update.call_args_list))

    def test_push_basic(self):
        status_result = {
            "ready": {
                "files": [],
                "fields": {
                    "somefield": ("one", "two", "two",),
                    "otherfield": ("one", "three", "three",),
                },
                "links": {},
                "deleted": [],
            }
        }

        with patch.object(self.ticketfolder, "status") as status:
            status.return_value = status_result
            with patch.object(self.ticketfolder.issue, "update") as update:
                with patch("jirafs.commands.pull.Command.main") as pull:
                    pull.return_value = True, True
                    run_command_method_with_kwargs(
                        "push", folder=self.ticketfolder,
                    )

                self.assertEqual(1, len(update.call_args_list))
                self.assertEqual(
                    update.call_args,
                    call(
                        **{
                            field_name: value[1]
                            for field_name, value in status_result["ready"][
                                "fields"
                            ].items()
                        }
                    ),
                )
