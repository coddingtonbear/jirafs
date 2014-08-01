from six.moves import configparser

from jirafs import utils
from jirafs.exceptions import NotTicketFolderException
from jirafs.plugin import CommandPlugin
from jirafs.ticketfolder import TicketFolder


class Command(CommandPlugin):
    """ Get, set, or list global or per-folder configuration values """
    NAME = 'config'

    def handle(self, args, jira, path, parser, **kwargs):
        if args.global_config:
            config = utils.get_config()
        else:
            try:
                folder = TicketFolder(path, jira)
                config = folder.get_config()
            except NotTicketFolderException:
                config = utils.get_config()

        if args.list:
            if len(args.params) != 0:
                parser.error(
                    "--list requires no parameters."
                )
            self.list(config)
        elif args.get:
            if len(args.params) != 1:
                parser.error(
                    "--get requires exactly one parameter, the configuration "
                    "value to display."
                )
            section, key = self.get_section_and_key(args.params[0])
            self.get(config, section, key)
        elif args.set:
            if len(args.params) != 2:
                parser.error(
                    "--set requires exactly two parameters, the configuration "
                    "key, and the configuration value."
                )
            section, key = self.get_section_and_key(args.params[0])
            value = args.params[1]

            if args.global_config:
                self.set_global(section, key, value)
            else:
                try:
                    folder = TicketFolder(path, jira)
                    self.set_local(folder, section, key, value)
                except NotTicketFolderException:
                    parser.error(
                        "Not currently within a ticket folder.  To set a "
                        "global configuration value, use the --global option."
                    )

    def get_section_and_key(self, string):
        return string.rsplit('.', 1)

    def set_global(self, section, key, value):
        utils.set_global_config_value(section, key, value)

    def set_local(self, folder, section, key, value):
        folder.set_config_value(section, key, value)

    def get(self, config, section, key):
        try:
            print(config.get(section, key))
        except configparser.Error:
            pass

    def list(self, config):
        for section in config.sections():
            parameters = config.items(section)
            for key, value in parameters:
                line = (
                    "{section}.{key}={value}".format(
                        section=section,
                        key=key,
                        value=value
                    )
                )
                print(line)

    def add_arguments(self, parser):
        parser.add_argument('--list', action='store_true')
        parser.add_argument('--get', action='store_true')
        parser.add_argument('--set', action='store_true')
        parser.add_argument(
            '--global',
            dest='global_config',
            default=False,
            action='store_true'
        )
        parser.add_argument('params', nargs='*')

    def parse_arguments(self, parser, args):
        args = super(Command, self).parse_arguments(parser, args)

        if not args.list and not args.get and not args.set:
            parser.error(
                'Please specify action using either --list, '
                '--set, or --get.'
            )

        return args
