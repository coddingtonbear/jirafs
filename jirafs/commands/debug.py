from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Open a debug console """
    MIN_VERSION = '1.0a1'
    MAX_VERSION = '1.99.99'

    def handle(self, folder, **kwargs):
        return self.debug(folder)

    def debug(self, folder):
        import ipdb
        return ipdb.set_trace()
