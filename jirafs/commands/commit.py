from jirafs import exceptions
from jirafs.plugin import CommandPlugin
from jirafs.ticketfolder import TicketFolder


class Command(CommandPlugin):
    """ Commit local changes for later submission to JIRA """

    def handle(self, args, jira, path, **kwargs):
        folder = TicketFolder(path, jira)
        return self.commit(folder, args.message, *args.git_arguments)

    def add_arguments(self, parser):
        parser.add_argument(
            '-m', '--message', dest='message', default='Untitled'
        )
        parser.add_argument(
            'git_arguments', nargs='*'
        )

    def commit(self, folder, message, *args):
        folder.run_git_command(
            'add', '-A'
        )
        try:
            folder.run_git_command(
                'commit', '-m', message, *args
            )
        except exceptions.GitCommandError:
            print("Nothing to commit")
