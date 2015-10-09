import webbrowser

from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Open the current ticketfolder's issue in your web browser """
    MIN_VERSION = '1.15'
    MAX_VERSION = '1.99.99'

    def main(self, folder, *args, **kwargs):
        return webbrowser.open(folder.cached_issue.permalink())
