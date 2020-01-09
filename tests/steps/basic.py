from __future__ import print_function

import collections
import json
import os
import shutil
import subprocess

from behave import *
from jira.client import JIRA


@given("jirafs is installed and configured")
def installed_and_configured(context):
    pass


@given("a cloned ticket with the following fields")
def cloned_ticket_with_following_fields(context):
    jira_client = JIRA(
        {
            "server": context.integration_testing["url"],
            "verify": False,
            "check_update": False,
        },
        basic_auth=(
            context.integration_testing["username"],
            context.integration_testing["password"],
        ),
    )

    issue_data = {
        "project": {"key": context.integration_testing["project"]},
        "issuetype": {"name": "Task",},
    }
    for row in context.table:
        issue_data[row[0]] = json.loads(row[1])

    issue = jira_client.create_issue(issue_data)

    if not "cleanup_steps" in context:
        context.cleanup_steps = []
    context.cleanup_steps.append(lambda context: issue.delete())
    context.execute_steps(
        u"""
        when the command "jirafs clone {url}" is executed
        and we enter the ticket folder for "{url}"
        """.format(
            url=issue.permalink()
        )
    )


@when('the command "{command}" is executed')
def execute_command(context, command):
    command = command.format(**context.integration_testing)

    env = os.environ.copy()
    env["JIRAFS_GLOBAL_CONFIG"] = context.integration_testing["config_path"]
    env["JIRAFS_ALLOW_USER_INPUT__BOOL"] = "0"

    proc = subprocess.Popen(
        command.encode("utf-8"),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    stdout, stderr = proc.communicate()

    if not hasattr(context, "executions"):
        context.executions = collections.deque()

    context.executions.appendleft(
        {
            "command": command,
            "stdout": stdout.decode("utf-8"),
            "stderr": stderr.decode("utf-8"),
            "return_code": proc.returncode,
        }
    )


@when('we enter the ticket folder for "{url}"')
def execute_command(context, url):
    url = url.format(**context.integration_testing)

    os.chdir(os.path.join(os.getcwd(), url.split("/")[-1]))


@then('the directory will contain a file named "{filename}"')
def directory_contains_file(context, filename):
    assert filename in os.listdir("."), "%s not in folder" % filename


@then('the output will contain the text "{expected}"')
def output_will_contain(context, expected):
    expected = expected.format(**context.integration_testing)

    assert expected in context.executions[0]["stdout"], "%s not in %s" % (
        expected,
        context.executions[0]["stdout"],
    )


@step("print execution results")
def print_stdout(context):
    print(json.dumps(context.executions[0], indent=4, sort_keys=True))


@step("debugger")
def debugger(context):
    import ipdb

    ipdb.set_trace()
