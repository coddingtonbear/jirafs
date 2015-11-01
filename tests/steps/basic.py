from __future__ import print_function

import collections
import json
import os
import subprocess
import textwrap

from behave import *


@given('jirafs is installed and configured')
def installed_and_configured(context):
    keys = {
        'known_ticket_url': 'INTEGRATION_TESTING_KNOWN_TICKET',
        'username': 'INTEGRATION_TESTING_USERNAME',
        'url': 'INTEGRATION_TESTING_URL',
        'project': 'INTEGRATION_TESTING_PROJECT',
        'password': 'INTEGRATION_TESTING_PASSWORD',
    }
    context.integration_testing = {}
    for k, v in keys.items():
        context.integration_testing[k] = os.environ[v]

    context.integration_testing['config_path'] = (
        os.path.join(os.getcwd(), 'jirafs_config')
    )

    with open(context.integration_testing['config_path'], 'w') as out:
        out.write(
            textwrap.dedent(
                """\
                    [{url}]
                    username={username}
                    password={password}

                    [jira]
                    server={url}

                """.format(
                    **context.integration_testing
                )
            )
        )


@when('the command "{command}" is executed')
def execute_command(context, command):
    command = command.format(**context.integration_testing)

    env = os.environ.copy()
    env['JIRAFS_GLOBAL_CONFIG'] = context.integration_testing['config_path']
    env['JIRAFS_ALLOW_USER_INPUT__BOOL'] = '0'

    proc = subprocess.Popen(
        command.encode('utf-8'),
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    stdout, stderr = proc.communicate()

    if not hasattr(context, 'executions'):
        context.executions = collections.deque()

    context.executions.appendleft(
        {
            'command': command,
            'stdout': stdout.decode('utf-8'),
            'stderr': stderr.decode('utf-8'),
            'return_code': proc.returncode,
        }
    )


@then('the output will contain the text "{expected}"')
def output_will_contain(context, expected):
    expected = expected.format(**context.integration_testing)

    assert (expected in context.executions[0]['stdout']), "%s not in %s" % (
        expected,
        context.executions[0]['stdout'],
    )


@step('print execution results')
def print_stdout(context):
    print(json.dumps(context.executions[0], indent=4, sort_keys=True))
