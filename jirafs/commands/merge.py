from jirafs import utils
from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Merge remote changes into your local copy """
    TRY_SUBFOLDERS = True
    MIN_VERSION = '1.0'
    MAX_VERSION = '1.99.99'

    def handle(self, folder, **kwargs):
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
