import json

from jirafs.exceptions import JirafsError
from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Get the status of the current ticketfolder """

    TRY_SUBFOLDERS = True
    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"

    def handle(self, args, folder, **kwargs):
        return self.cmd(folder, args.field_name, args.value, as_json=args.json)

    def add_arguments(self, parser):
        parser.add_argument("field_name",)
        parser.add_argument("value",)
        parser.add_argument(
            "--json",
            help=("Interpret value argument as JSON data."),
            action="store_true",
            default=False,
        )

    def main(self, folder, field_name, value, as_json=False):
        fields = folder.get_fields()

        if as_json:
            try:
                value = json.loads(value)
            except ValueError:
                raise JirafsError("Value '%s' could not be decoded as JSON." % (value,))

        key_dotpath = None
        if "." in field_name:
            field_name, key_dotpath = field_name.split(".", 1)

        if field_name not in fields:
            raise JirafsError("Field '%s' does not exist." % field_name)

        if key_dotpath:
            data = fields[field_name]
            try:
                cursor = data
                dotpath_parts = key_dotpath.split(".")
                last_key = len(dotpath_parts) - 1
                for idx, component in enumerate(dotpath_parts):
                    if idx == last_key:
                        cursor[component] = value
                        break
                    elif not isinstance(cursor.get(component), dict):
                        raise JirafsError(
                            "Key '%s' (of dotpath '%s') is not an object "
                            "in field '%s'." % (component, key_dotpath, field_name,)
                        )
                    else:
                        if component not in data:
                            raise JirafsError(
                                "Key '%s' (of dotpath '%s') could not be found "
                                "in field '%s'." % (component, key_dotpath, field_name,)
                            )
                        cursor = cursor[component]
            except (ValueError, TypeError):
                raise JirafsError(
                    "Field '%s' could not be parsed as JSON for retrieving "
                    "dotpath '%s'." % (field_name, key_dotpath,)
                )
            value = data
        else:
            data = value

        fields[field_name] = data
        fields.write()
