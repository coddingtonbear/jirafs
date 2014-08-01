import webbrowser

from jirafs.plugin import CommandPlugin
from jirafs.ticketfolder import TicketFolder


class Command(CommandPlugin):
    """ Open the current ticketfolder's issue in your web browser """
    name = 'open'

    def handle(self, args, jira, path, **kwargs):
        folder = TicketFolder(path, jira)

        self.open(folder)

    def open(self, folder):
        webbrowser.open(folder.cached_issue.permalink())
