import os
import shutil
import tempfile
import textwrap


def before_scenario(context, *args, **kwargs):
    context.starting_dir = os.getcwd()
    context.temp_dir = tempfile.mkdtemp()
    os.chdir(context.temp_dir)

    keys = {
        "known_ticket_url": "INTEGRATION_TESTING_KNOWN_TICKET",
        "username": "INTEGRATION_TESTING_USERNAME",
        "url": "INTEGRATION_TESTING_URL",
        "project": "INTEGRATION_TESTING_PROJECT",
        "password": "INTEGRATION_TESTING_PASSWORD",
    }
    context.integration_testing = {}
    for k, v in keys.items():
        context.integration_testing[k] = os.environ[v]

    context.integration_testing["config_path"] = os.path.join(
        os.getcwd(), "jirafs_config"
    )

    with open(context.integration_testing["config_path"], "w") as out:
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


def after_scenario(context, *args, **kwargs):
    os.chdir(context.starting_dir)
    shutil.rmtree(context.temp_dir)

    if hasattr(context, "cleanup_steps"):
        for step in context.cleanup_steps:
            step(context)
