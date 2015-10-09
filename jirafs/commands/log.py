import pydoc

from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Print the log for this issue """
    MIN_VERSION = '1.15'
    MAX_VERSION = '1.99.99'

    def main(self, folder, **kwargs):
        results = folder.get_log()
        pydoc.pager(results)
        return results
