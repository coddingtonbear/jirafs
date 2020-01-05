from jirafs.plugin import CommandPlugin

try:
    import ipdb as pdb  # noqa
except ImportError:
    import pdb


class Command(CommandPlugin):
    """ Open a debug console """

    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"

    def main(self, folder, **kwargs):
        return pdb.set_trace()
