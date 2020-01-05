import pydoc

from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Print the log for this issue """

    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"

    def main(self, folder, **kwargs):
        results = folder.get_log()
        pydoc.pager(results)
        return results
