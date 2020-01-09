import os
from unittest import TestCase, SkipTest
import shutil
import subprocess
import tempfile

from jira.client import JIRA

from jirafs.utils import run_command_method_with_kwargs
from jirafs.ticketfolder import TicketFolder


class IntegrationTestBase(TestCase):
    def setUp(self):
        super(IntegrationTestBase, self).setUp()

        self.jira_configured = True

        jira_env_settings = {
            "username": "INTEGRATION_TESTING_USERNAME",
            "url": "INTEGRATION_TESTING_URL",
            "project": "INTEGRATION_TESTING_PROJECT",
            "password": "INTEGRATION_TESTING_PASSWORD",
        }
        self.jira_env = {}
        for key, env_var in jira_env_settings.items():
            try:
                self.jira_env[key] = os.environ[env_var]
            except KeyError:
                raise SkipTest(
                    "Integration tests require the following environment "
                    "variables to be set: %s"
                    % (", ".join([v for k, v in jira_env_settings.items()]))
                )

        self.jira = JIRA(
            {"server": self.jira_env["url"]},
            basic_auth=(self.jira_env["username"], self.jira_env["password"],),
        )

        self.created_issues = []
        self.path = tempfile.mkdtemp()

    def get_jira(self, *args, **kwargs):
        return self.jira

    def get_ticket_folder_for_path(self, path):
        return TicketFolder(path, self.get_jira,)

    def _get_default_fields(self):
        return {
            "project": {"key": self.jira_env["project"],},
            "issuetype": {"name": "Task"},
        }

    def tearDown(self):
        for issue in self.created_issues:
            issue.delete()

        shutil.rmtree(self.path, ignore_errors=True)

    def create_issue(self, fields, *args, **kwargs):
        issue_fields = self._get_default_fields()
        issue_fields.update(fields)

        issue = self.jira.create_issue(issue_fields, *args, **kwargs)
        self.created_issues.append(issue)

        return issue

    def run_command(self, name, **kwargs):
        return run_command_method_with_kwargs(name, **kwargs)

    def run_from_shell(self, *args, **kwargs):
        if "path" not in kwargs:
            path = self.path
        else:
            path = kwargs["path"]

        return subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=path,
        )
