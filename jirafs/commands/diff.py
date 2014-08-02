from jirafs.plugin import CommandPlugin
from jirafs.ticketfolder import TicketFolder


class Command(CommandPlugin):
    """ Print a diff of locally-changed files """

    def handle(self, args, jira, path, **kwargs):
        folder = TicketFolder(path, jira)

        self.diff(folder)

    def diff(self, folder):
        result = folder.run_git_command('diff')
        if result:
            print(result.strip())
