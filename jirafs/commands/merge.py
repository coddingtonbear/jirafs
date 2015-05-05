from jirafs import constants, utils
from jirafs.plugin import CommandPlugin
from jirafs.jirafieldmanager import JiraFieldManager
from jirafs.jiralinkmanager import JiraLinkManager


class Command(CommandPlugin):
    """ Merge remote changes into your local copy """
    RUN_FOR_SUBTASKS = True
    TRY_SUBFOLDERS = True
    MIN_VERSION = '1.0a1'
    MAX_VERSION = '1.99.99'

    def handle(self, folder, **kwargs):
        return self.merge(folder)

    def merge(self, folder):
        with utils.stash_local_changes(folder):
            original_merge_base = folder.git_merge_base
            folder.run_git_command('merge', 'jira')
            final_merge_base = folder.git_merge_base

            new_comments = folder.run_git_command(
                'diff',
                '%s..%s' % (
                    original_merge_base,
                    final_merge_base
                ),
                '--',
                constants.TICKET_COMMENTS,
            ).strip()
            if new_comments:
                folder.log(
                    "New comment(s) have been posted."
                )

            jira_fields = JiraFieldManager.create(
                folder, revision='jira'
            )
            master_fields = JiraFieldManager.create(
                folder, revision=original_merge_base
            )
            for field, values in (jira_fields - master_fields).items():
                folder.log(
                    u"Field {field} changed: \"{fr}\" -> \"{to}\"".format(
                        field=field,
                        fr=values[0],
                        to=values[1]
                    )
                )

            jira_links = JiraLinkManager.create(
                folder, revision='jira'
            )
            master_links = JiraLinkManager.create(
                folder, revision=original_merge_base
            )
            for category in ('issue', 'remote'):
                values_dict = (jira_links - master_links).get(category, {})
                for field, values in values_dict.items():
                    folder.log(
                        u"Link {field} changed: \"{fr}\" -> \"{to}\"".format(
                            field=field,
                            fr=values[0],
                            to=values[1]
                        )
                    )

            if original_merge_base != final_merge_base:
                folder.log(
                    "Merged 'jira' into 'master'; merge-base is now %s" % (
                        final_merge_base
                    )
                )
            return utils.PostStatusResponse(
                original_merge_base == final_merge_base,
                final_merge_base
            )
