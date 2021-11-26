import os
import re
import shutil
from urllib import parse

from jirafs import exceptions, utils
from jirafs.plugin import CommandPlugin
from jirafs.ticketfolder import TicketFolder


class Command(CommandPlugin):
    """Clone a new ticketfolder for the specified ticket URL"""

    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"
    AUTOMATICALLY_INSTANTIATE_FOLDER = False

    TICKET_RE = re.compile(r".*\/browse\/(\w+-\d+)\/?")

    def handle(self, args, jira, path, **kwargs):
        ticket_url = args.ticket_url[0]

        ticket_url_parts = parse.urlparse(ticket_url)
        if not ticket_url_parts.netloc:
            default_server = utils.get_default_jira_server()
            ticket_url = parse.urljoin(default_server, "browse/" + ticket_url + "/")

        path = args.path[0] if args.path else None

        return self.cmd(path, ticket_url, jira)

    def clone_from_issue(self, match, ticket_url, path, jira):
        if not path:
            path = match.group(1)
        path = os.path.realpath(path)
        os.mkdir(path)

        try:
            folder = TicketFolder.initialize_ticket_folder(ticket_url, path, jira)

            utils.run_command_method_with_kwargs("pull", folder=folder)
        except BaseException:
            shutil.rmtree(path)
            raise

        folder.log(
            "Issue %s cloned successfully to %s",
            (
                folder.issue_url,
                folder.path,
            ),
        )

        return folder

    def main(self, path, url, jira):
        match = self.TICKET_RE.match(url)
        if not match:
            raise exceptions.JirafsError("'%s' is not a valid Jira ticket URL." % url)

        return self.clone_from_issue(
            match,
            url,
            path,
            jira,
        )

    def add_arguments(self, parser):
        parser.add_argument("ticket_url", nargs=1, type=str)
        parser.add_argument(
            "path",
            nargs="*",
            type=str,
        )
