import six

from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """Assign the current task to a user"""
    MIN_VERSION = '1.0a1'
    MAX_VERSION = '1.99.99'

    def handle(self, args, folder, **kwargs):
        username = args.username
        if not username:
            username = folder.get_config().get(
                folder.jira_base,
                'username',
            )
        folder.jira.assign_issue(folder.issue, username)
        folder.log(
            'Successfully assigned %s to %s.',
            args=(
                folder.issue.key,
                username
            ),
        )

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            nargs='?',
            type=six.text_type
        )
