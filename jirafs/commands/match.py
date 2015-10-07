import json

from jirafs.exceptions import JirafsError
from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Check whether a given dotpath matches an expected value """
    TRY_SUBFOLDERS = True
    MIN_VERSION = '1.14'
    MAX_VERSION = '1.99.99'

    def handle(self, args, folder, **kwargs):
        return self.match(
            folder,
            args.field_name,
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
