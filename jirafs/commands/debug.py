from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Open a debug console """
    MIN_VERSION = '1.15'
    MAX_VERSION = '1.99.99'

    def main(self, folder, **kwargs):
        import ipdb
        return ipdb.set_trace()
