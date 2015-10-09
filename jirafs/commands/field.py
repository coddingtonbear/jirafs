import json

from jirafs.exceptions import JirafsError
from jirafs.plugin import CommandPlugin, CommandResult


class Command(CommandPlugin):
    """ Get the status of the current ticketfolder """
    TRY_SUBFOLDERS = True
    MIN_VERSION = '1.15'
    MAX_VERSION = '1.99.99'

    def handle(self, args, folder, **kwargs):
        return self.cmd(
            folder, args.field_name, raw=args.raw, formatted=args.formatted
        )

    def add_arguments(self, parser):
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
            '--formatted',
            help=(
                'Format JSON output with indentation and sorted keys.'
            ),
            action='store_true',
            default=False
        )
        parser.add_argument(
            'field_name',
        )

    def get_field_value_by_dotpath(
        self, folder, field_name, raw=False, formatted=False
    ):
        fields = folder.get_fields()

        key_dotpath = None
        if '.' in field_name:
            field_name, key_dotpath = field_name.split('.', 1)

        if field_name not in fields:
            raise JirafsError("Field '%s' does not exist." % field_name)

        if raw:
            data = fields[field_name]
        else:
            data = fields.get_transformed(field_name)

        if key_dotpath:
            try:
                for component in key_dotpath.split('.'):
                    if not isinstance(data, dict):
                        raise JirafsError(
                            "Key '%s' (of dotpath '%s') is not an object "
                            "in field '%s'." % (
                                component,
                                key_dotpath,
                                field_name,
                            )
                        )
                    elif component not in data:
                        data = ''
                        break
                    else:
                        data = data[component]
            except (ValueError, TypeError):
                raise JirafsError(
                    "Field '%s' could not be parsed as JSON for retrieving "
                    "dotpath '%s'." % (
                        field_name,
                        key_dotpath,
                    )
                )

        return data

    def main(
        self, folder, field_name, raw=False, formatted=False
    ):
        data = self.get_field_value_by_dotpath(
            folder, field_name, raw, formatted
        )

        if isinstance(data, (list, dict)):
            kwargs = {}
            if formatted:
                kwargs = {
                    'indent': 4,
                    'sort_keys': True,
                }
            data = json.dumps(data, **kwargs)

        return data

    def cmd(self, *args, **kwargs):
        data = self.main(*args, **kwargs)

        return CommandResult(data)
