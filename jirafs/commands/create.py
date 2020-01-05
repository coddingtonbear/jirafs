from jirafs import utils
from jirafs.plugin import CommandPlugin
from jirafs.utils import run_command_method_with_kwargs


class Command(CommandPlugin):
    """Create a new JIRA issue"""

    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"
    AUTOMATICALLY_INSTANTIATE_FOLDER = False

    FIELDS = (
        {
            "name": "project",
            "prompt": "Project",
            "required": True,
            "path": "project.key",
        },
        {
            "name": "issuetype",
            "prompt": "Issue Type",
            "default": "Task",
            "path": "issuetype.name",
        },
        {"name": "summary", "prompt": "Summary", "required": True},
        {"name": "description", "prompt": "Description", "required": False},
    )

    def set_field_value(self, data, field, value):
        starting_reference = data

        path = field.get("path", field["name"])
        for part in path.split("."):
            if part not in data:
                data[part] = {}
            last_reference = data
            data = data[part]

        last_reference[path.split(".")[-1]] = value

        return starting_reference

    def prompt_for_input(self, field):
        while True:
            if field.get("default"):
                value = input(
                    "%s (%s): " % (field.get("prompt"), field.get("default"),)
                )
            else:
                value = input("%s: " % (field.get("prompt")))

            value = value.strip()

            if value:
                return value
            elif not field.get("required") and field.get("default"):
                return field.get("default")
            elif not field.get("required"):
                return value

    def main(self, args, jira, path, parser, **kwargs):
        server = args.server
        if not server:
            server = utils.get_default_jira_server()

        issue_data = {}

        for field in self.FIELDS:
            if getattr(args, field["name"]) is not None:
                self.set_field_value(issue_data, field, getattr(args, field["name"]))
            elif args.quiet:
                self.set_field_value(issue_data, field, field.get("default"))
            else:
                self.set_field_value(issue_data, field, self.prompt_for_input(field))

        jira_client = jira(server)
        issue = jira_client.create_issue(issue_data)

        return run_command_method_with_kwargs(
            "clone", path=None, url=issue.permalink(), jira=jira,
        )

    def add_arguments(self, parser):
        parser.add_argument("--server", default=None)
        parser.add_argument("--quiet", "-q", default=False, action="store_true")
        for argument in self.FIELDS:
            parser.add_argument("--%s" % argument["name"], default=None, type=str)
