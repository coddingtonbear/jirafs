from jirafs import utils
from jirafs.plugin import CommandPlugin
from jirafs.ticketfolder import TicketFolder


class Command(CommandPlugin):
    """ Merge remote changes into your local copy """
    TRY_SUBFOLDERS = True

    def handle(self, args, jira, path, **kwargs):
        folder = TicketFolder(path, jira)
        return self.merge(folder)

    def merge(self, folder):
        with utils.stash_local_changes(folder):
            original_merge_base = folder.git_merge_base
            folder.run_git_command('merge', 'jira')
            final_merge_base = folder.git_merge_base

            return utils.PostStatusResponse(
                original_merge_base == final_merge_base,
                final_merge_base
            )
