from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """Assign the current task to a user"""

    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"

    def main(self, args, folder, **kwargs):
        username = args.username
        if not username:
            username = folder.get_config().get(folder.jira_base, "username",)
        folder.jira.assign_issue(folder.issue, username)
        folder.log(
            "Successfully assigned %s to %s.", args=(folder.issue.key, username),
        )

    def add_arguments(self, parser):
        parser.add_argument("username", nargs="?", type=str)
