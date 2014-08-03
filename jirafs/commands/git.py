import pydoc

from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Run a git command against this ticketfolder's underlying GIT repo """
    MIN_VERSION = '1.0a1'
    MAX_VERSION = '1.99.99'

    def handle(self, args, folder, **kwargs):
        return self.git(folder, *self.git_arguments)

    def parse_arguments(self, parser, extra_args):
        args, git_arguments = parser.parse_known_args(extra_args)
        self.git_arguments = git_arguments
        return args

    def git(self, folder, *git_arguments):
        result = folder.run_git_command(*git_arguments)
        pydoc.pager(result)
        return result
