from jirafs.exceptions import JirafsError
from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Get the status of the current ticketfolder """
    TRY_SUBFOLDERS = True
    MIN_VERSION = '1.0a1'
    MAX_VERSION = '1.99.99'

    def handle(self, args, folder, **kwargs):
        return self.field(folder, args.field_name)

    def add_arguments(self, parser):
        parser.add_argument(
            'field_name',
        )

    def field(self, folder, field_name):
        fields = folder.get_fields()

        if field_name not in fields:
            raise JirafsError("Field '%s' does not exist.")

        print(fields[field_name])
