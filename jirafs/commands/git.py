from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Run a git command against this ticketfolder's underlying GIT repo """
    MIN_VERSION = '1.0'
    MAX_VERSION = '1.99.99'

    def handle(self, args, folder, **kwargs):
        return self.git(folder, args.git_arguments)

    def add_arguments(self, parser):
        parser.add_argument(
            'git_arguments', nargs='*'
        )

    def git(self, folder, *git_arguments):
        result = folder.run_git_command(*git_arguments)
        print(result)
        return result
