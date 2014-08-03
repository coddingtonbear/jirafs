import webbrowser

from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Open the current ticketfolder's issue in your web browser """
    MIN_VERSION = '1.0a1'
    MAX_VERSION = '1.99.99'

    def handle(self, folder, **kwargs):
        return self.open(folder)

    def open(self, folder):
        return webbrowser.open(folder.cached_issue.permalink())
