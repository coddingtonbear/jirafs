from jirafs import utils
from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """Create a subtask of a given issue."""

    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"

    def main(self, folder, args, **kwargs):
        summary = " ".join(args.summary)

        folder.jira.create_issue(
            fields={
                "project": {"key": folder.issue.fields.project.key},
                "summary": summary,
                "issuetype": {"name": "Sub-task"},
                "parent": {"id": folder.issue.key},
            }
        )

        commands = utils.get_installed_commands()
        jira = utils.lazy_get_jira()
        commands["fetch"].execute_command(
            [], jira=jira, path=folder.path, command_name="fetch",
        )

    def add_arguments(self, parser):
        parser.add_argument("summary", nargs="+")
