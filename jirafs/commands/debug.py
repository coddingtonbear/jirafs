from jirafs.plugin import CommandPlugin

try:
    import ipdb as pdb  # noqa
except ImportError:
    import pdb


class Command(CommandPlugin):
    """ Open a debug console """

    MIN_VERSION = "1.15"
    MAX_VERSION = "2.99.99"

    def main(self, folder, **kwargs):
        return pdb.set_trace()
