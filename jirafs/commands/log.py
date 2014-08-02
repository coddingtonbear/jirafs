from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Print the log for this issue """
    MIN_VERSION = '1.0'
    MAX_VERSION = '1.99.99'

    def handle(self, folder, **kwargs):
        return self.log(folder)

    def log(self, folder):
        results = folder.get_log()
        print(results)
        return results
