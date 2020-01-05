import webbrowser

from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Open the current ticketfolder's issue in your web browser """

    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"

    def main(self, folder, *args, **kwargs):
        return webbrowser.open(folder.cached_issue.permalink())
