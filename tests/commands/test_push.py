import io
from unittest import SkipTest

from mock import call, Mock, patch

from jirafs.utils import run_command_method_with_kwargs

from .base import BaseCommandTestCase


class TestPushCommand(BaseCommandTestCase):
    def setUp(self):
        super(TestPushCommand, self).setUp()

    def test_push_no_changes(self):
        with patch.object(self.ticketfolder.issue, 'update') as update:
            with patch('jirafs.commands.pull.Command.main') as pull:
                pull.return_value = True, True
                run_command_method_with_kwargs(
                    'push',
                    folder=self.ticketfolder,
                )

            self.assertEqual(0, len(update.call_args_list))

    def test_push_basic(self):
        status_result = {
            'ready': {
                'files': [],
                'fields': {
                    'somefield': ('one', 'two', 'two', ),
                    'otherfield': ('one', 'three', 'three', )
                },
                'links': {},
            }
        }

        with patch.object(self.ticketfolder, 'status') as status:
            status.return_value = status_result
            with patch.object(self.ticketfolder.issue, 'update') as update:
                with patch('jirafs.commands.pull.Command.main') as pull:
                    pull.return_value = True, True
                    run_command_method_with_kwargs(
                        'push',
                        folder=self.ticketfolder,
                    )

                self.assertEqual(1, len(update.call_args_list))
                self.assertEqual(
                    update.call_args,
                    call(
                        **{
                            field_name: value[1]
                            for field_name, value
                            in status_result['ready']['fields'].items()
                        }
                    )
                )


class TestPushCommandWithMacropatch(BaseCommandTestCase):
    def setUp(self):
        try:
            import jirafs_list_table  # noqa
        except ImportError:
            raise SkipTest(
                "Push command macropatch tests require the "
                "jira-list-table package to be installed."
            )
        super(TestPushCommandWithMacropatch, self).setUp()
        run_command_method_with_kwargs(
            'plugins',
            folder=self.ticketfolder,
            args=Mock(
                enable='list_table',
            )
        )

    def test_push_change_patched_content(self):
        # First, let's write out a patch
        description_one = u"""
            {list-table}
            * -
            ** Location
            ** Company
            * @coddingtonbear
            ** Portland, OR
            ** Urban Airship
            {list-table}
        """
        description_path = self.ticketfolder.get_path('description.jira')

        with io.open(description_path, 'w', encoding='utf-8') as out:
            out.write(description_one)

        run_command_method_with_kwargs(
            'commit',
            folder=self.ticketfolder,
            message='No me importa',
        )
        with patch.object(self.ticketfolder.issue, 'update'):
            with patch('jirafs.commands.pull.Command.pull') as pull:
                pull.return_value = True, True
                run_command_method_with_kwargs(
                    'push',
                    folder=self.ticketfolder,
                )

        description_two = u"""
            {list-table:horizontal}
            * -
            ** Location
            ** Company
            * @coddingtonbear
            ** Portland, OR
            ** Urban Airship
            * @ralphbean
            ** New York, NY
            ** RedHat
            {list-table}
        """

        with io.open(description_path, 'w', encoding='utf-8') as out:
            out.write(description_two)

        run_command_method_with_kwargs(
            'commit',
            folder=self.ticketfolder,
            message='No me importa',
        )
        with patch.object(self.ticketfolder.issue, 'update'):
            with patch('jirafs.commands.pull.Command.pull') as pull:
                pull.return_value = True, True
                run_command_method_with_kwargs(
                    'push',
                    folder=self.ticketfolder,
                )

