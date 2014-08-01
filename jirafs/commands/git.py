from jirafs.plugin import CommandPlugin
from jirafs.ticketfolder import TicketFolder


class Command(CommandPlugin):
    """ Run a git command against this ticketfolder's underlying GIT repo """
    NAME = 'git'

    def handle(self, args, jira, path, **kwargs):
        folder = TicketFolder(path, jira, migrate=args.migrate)
        return self.git(folder, args.git_arguments)

    def add_arguments(self, parser):
        parser.add_argument(
            'git_arguments', nargs='*'
        )
        parser.add_argument(
            '--no-migrate', dest='migrate', default=True, action='store_false'
        )

    def git(self, folder, *git_arguments):
        print(folder.run_git_command(*git_arguments))
