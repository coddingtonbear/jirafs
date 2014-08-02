from jirafs import exceptions
from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Commit local changes for later submission to JIRA """
    MIN_VERSION = '1.0'
    MAX_VERSION = '1.99.99'

    def handle(self, args, folder, **kwargs):
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
            return folder.run_git_command(
                'commit', '-m', message, *args
            )
        except exceptions.GitCommandError:
            print("Nothing to commit")
