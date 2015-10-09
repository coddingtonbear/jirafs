import json

from jirafs.exceptions import JirafsError
from jirafs.plugin import CommandPlugin, CommandResult
from jirafs.utils import run_command_method_with_kwargs


class Command(CommandPlugin):
    """ Check whether a given dotpath matches an expected value """
    TRY_SUBFOLDERS = True
    MIN_VERSION = '1.15'
    MAX_VERSION = '1.99.99'

    def handle(self, args, folder, **kwargs):
        return self.cmd(
            folder,
            args.field_name,
            args.field_value,
            isjson=args.json,
            negate=args.negate,
            raw=args.raw,
            quiet=args.quiet,
        )

    def add_arguments(self, parser):
        parser.add_argument(
            'field_name',
        )
        parser.add_argument(
            'field_value',
        )
        parser.add_argument(
            '--json',
            help=(
                'Process the provided field value as JSON'
            ),
            action='store_true',
            default=False
        )
        parser.add_argument(
            '--negate',
            help=(
                'Compare the field value without applying '
                'plugin transformations'
            ),
            action='store_true',
            default=False
        )
        parser.add_argument(
            '--raw',
            help=(
                'Return the field value without applying '
                'plugin transformations'
            ),
            action='store_true',
            default=False
        )
        parser.add_argument(
            '--quiet',
            help=(
                'Print no message to stdout indicating success or failure'
            ),
            action='store_true',
            default=False
        )

    def main(self, folder, field_name, field_value, isjson, negate, raw, quiet):
        actual_value = run_command_method_with_kwargs(
            'field',
            method='get_field_value_by_dotpath',
            folder=folder,
            field_name=field_name,
            raw=raw,
        )

        if isjson:
            field_value = json.loads(field_value)

        success = actual_value == field_value

        comparison_result = u" != "
        if success:
            comparison_result = u" == "
        message = u"{left} {comparison} {right}".format(
            left=actual_value,
            comparison=comparison_result,
            right=field_value,
        )

        if negate:
            result = not result

        return (
            message if not quiet else None,
            0 if success else 1,
        )

    def cmd(self, *args, **kwargs):
        message, return_code = self.main(*args, **kwargs)

        return CommandResult(message, return_code)
