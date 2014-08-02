from jirafs.plugin import CommandPlugin
from jirafs.ticketfolder import TicketFolder


class Command(CommandPlugin):
    """ Print the log for this issue """

    def handle(self, args, jira, path, **kwargs):
        folder = TicketFolder(path, jira)
        return self.log(folder)

    def log(self, folder):
        print(folder.get_log())
