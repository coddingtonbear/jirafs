import pydoc

from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Run a git command against this ticketfolder's underlying GIT repo """

    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"

    def handle(self, args, folder, **kwargs):
        return self.cmd(folder, *self.git_arguments)

    def parse_arguments(self, parser, extra_args):
        args, git_arguments = parser.parse_known_args(extra_args)
        self.git_arguments = git_arguments
        return args

    def main(self, folder, *git_arguments):
        result = folder.run_git_command(*git_arguments)
        pydoc.pager(result)
        return result
