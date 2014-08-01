from jirafs.plugin import CommandPlugin
from jirafs.ticketfolder import TicketFolder
from jirafs.utils import get_installed_commands


class Command(CommandPlugin):
    """ Fetch and merge remote changes """
    NAME = 'fetch'
    TRY_SUBFOLDERS = True

    def handle(self, args, jira, path, **kwargs):
        folder = TicketFolder(path, jira)
        return self.pull(folder)

    def pull(self, folder):
        commands = get_installed_commands()

        commands['fetch']().fetch(folder)
        commands['merge']().merge(folder)
