from jirafs.plugin import CommandPlugin
from jirafs import __version__


class Command(CommandPlugin):
    """ Print the current version number to the console """

    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"
    AUTOMATICALLY_INSTANTIATE_FOLDER = False

    def handle(self, args, *vargs, **kwargs):
        print(f"Jirafs version {__version__}")
