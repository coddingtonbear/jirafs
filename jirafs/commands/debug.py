import ipdb

from jirafs.plugin import CommandPlugin
from jirafs.ticketfolder import TicketFolder


class Command(CommandPlugin):
    """ Open a debug console """
    NAME = 'debug'

    def handle(self, args, jira, path, **kwargs):
        folder = TicketFolder(path, jira, migrate=args.migrate)
        self.debug(folder)

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-migrate', dest='migrate', default=True, action='store_false'
        )

    def debug(self, folder):
        ipdb.set_trace()
