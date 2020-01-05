import configparser

from jirafs import utils
from jirafs.exceptions import NotTicketFolderException
from jirafs.plugin import CommandResult, DirectOutputCommandPlugin
from jirafs.ticketfolder import TicketFolder


class Command(DirectOutputCommandPlugin):
    """ Get, set, or list global or per-folder configuration values """

    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"
    AUTOMATICALLY_INSTANTIATE_FOLDER = False

    def main(self, args, jira, path, parser, **kwargs):
        if args.global_config:
            config = utils.get_config()
        else:
            try:
                folder = TicketFolder(path, jira)
                config = folder.get_config()
            except NotTicketFolderException:
                config = utils.get_config()

        return_value = None
        if args.list:
            if len(args.params) != 0:
                parser.error("--list requires no parameters.")
            return_value = self.list(config)
        elif args.get:
            if len(args.params) != 1:
                parser.error(
                    "--get requires exactly one parameter, the configuration "
                    "value to display."
                )
            section, key = self.get_section_and_key(args.params[0])
            return_value = self.get(config, section, key)
        elif args.set:
            if len(args.params) != 2:
                parser.error(
                    "--set requires exactly two parameters, the configuration "
                    "key, and the configuration value."
                )
            section, key = self.get_section_and_key(args.params[0])
            value = args.params[1]

            if args.global_config:
                return_value = self.set_global(section, key, value)
            else:
                try:
                    folder = TicketFolder(path, jira)
                    return_value = self.set_local(folder, section, key, value)
                except NotTicketFolderException:
                    parser.error(
                        "Not currently within a ticket folder.  To set a "
                        "global configuration value, use the --global option."
                    )

        return return_value

    def get_section_and_key(self, string):
        return string.rsplit(".", 1)

    def set_global(self, section, key, value):
        return utils.set_global_config_value(section, key, value)

    def set_local(self, folder, section, key, value):
        return folder.set_config_value(section, key, value)

    def get(self, config, section, key):
        try:
            value = config.get(section, key)
            return CommandResult(value)
        except configparser.Error:
            pass

    def list(self, config):
        lines = CommandResult()

        for section in config.sections():
            parameters = config.items(section)
            for key, value in parameters:
                lines = lines.add_line(
                    u"{section}.{key}={value}", section=section, key=key, value=value
                )

        return lines

    def add_arguments(self, parser):
        parser.add_argument("--list", action="store_true")
        parser.add_argument("--get", action="store_true")
        parser.add_argument("--set", action="store_true")
        parser.add_argument(
            "--global", dest="global_config", default=False, action="store_true"
        )
        parser.add_argument("params", nargs="*")

    def parse_arguments(self, parser, args):
        args = super(Command, self).parse_arguments(parser, args)

        if not args.list and not args.get and not args.set:
            args.list = True

        return args
