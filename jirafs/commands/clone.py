import os
import re
import shutil
import subprocess
import tempfile
from urllib import parse

from jirafs import constants, exceptions, utils
from jirafs.plugin import CommandPlugin
from jirafs.ticketfolder import TicketFolder


class Command(CommandPlugin):
    """ Clone a new ticketfolder for the specified ticket URL"""

    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"
    AUTOMATICALLY_INSTANTIATE_FOLDER = False

    TICKET_RE = re.compile(r".*\/browse\/(\w+-\d+)\/?")

    def handle(self, args, jira, path, **kwargs):
        ticket_url = args.ticket_url[0]

        if not os.path.exists(os.path.realpath(ticket_url)):
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
        except Exception:
            shutil.rmtree(path)
            raise

        folder.log(
            "Issue %s cloned successfully to %s", (folder.issue_url, folder.path,)
        )

        return folder

    def clone_from_git_repository(self, url, path, jira):
        temp_dir = tempfile.mkdtemp()

        subprocess.check_call(
            ["git", "clone", url, temp_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for branch in ["jira", "master"]:
            subprocess.check_call(
                ["git", "checkout", branch],
                cwd=temp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        issue_url_path = os.path.join(temp_dir, constants.METADATA_DIR, "issue_url")
        with open(issue_url_path, "r") as issue_url_file:
            issue_url = issue_url_file.read()

        match = self.TICKET_RE.match(issue_url)
        if not match:
            shutil.rmtree(temp_dir)
            raise exceptions.NotTicketFolderException(
                "The git repository at %s is not a Jirafs backup." % (url,)
            )

        if path:
            path = os.path.realpath(path)
        else:
            # This will create a subdirectory of the cwd named after
            # the ticket's number
            path = os.path.realpath(match.group(1))

        # Move the temporary clone into the proper place
        os.rename(temp_dir, path)

        # Re-clone the shadow repository
        shadow_path = os.path.join(path, constants.METADATA_DIR, "shadow")
        subprocess.check_call(
            ["git", "clone", path, shadow_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Move the .git directory to where we hide it
        os.rename(
            os.path.join(path, ".git"),
            os.path.join(path, constants.METADATA_DIR, "git"),
        )

        # Reset the shadow's URL to use a relative path
        subprocess.check_call(
            ["git", "remote", "set-url", "origin", "../git"],
            cwd=shadow_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        subprocess.check_call(
            ["git", "checkout", "jira"],
            cwd=shadow_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        folder = TicketFolder(path, jira,)
        folder.run_git_command(
            "config",
            "--file=%s" % folder.get_metadata_path("git", "config",),
            "core.excludesfile",
            ".jirafs/gitignore",
        )
        folder.log(
            "Cloned Jirafs ticket folder for %s at %s; on hash %s",
            (
                folder.issue_url,
                folder.path,
                folder.run_git_command("rev-parse", "master",),
            ),
        )
        return folder

    def main(self, path, url, jira):
        match = self.TICKET_RE.match(url)
        if match:
            return self.clone_from_issue(match, url, path, jira,)

        # Try checking if it's a git repository, too
        try:
            subprocess.check_call(
                ["git", "ls-remote", url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return self.clone_from_git_repository(url, path, jira,)
        except subprocess.CalledProcessError:
            pass

        raise exceptions.JirafsError(
            "'%s' is neither a valid JIRA ticket URL, "
            "nor Jirafs remote backup" % (url)
        )

    def add_arguments(self, parser):
        parser.add_argument("ticket_url", nargs=1, type=str)
        parser.add_argument(
            "path", nargs="*", type=str,
        )
