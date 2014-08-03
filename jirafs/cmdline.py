import argparse
import logging
import os
import sys
import time

import six
from verlib import NormalizedVersion

from . import utils
from .exceptions import (
    GitCommandError,
    JirafsError,
    NotTicketFolderException
)


logger = logging.getLogger(__name__)


def main():
    if sys.version_info < (2, 7):
        raise RuntimeError(
            "Jirafs requires minimally version 2.7 of Python 2, or "
            "any version of Python 3.  Please upgrade your version of "
            "python before using Jirafs."
        )
    if utils.get_git_version() < NormalizedVersion('1.8'):
        raise RuntimeError(
            "Jirafs requires minimally version 1.8 of Git.  Please "
            "upgrade your version of git before using Jirafs."
        )

    commands = utils.get_installed_commands()

    parser = argparse.ArgumentParser(
        description='Edit Jira issues locally from your filesystem',
        add_help=False,
    )
    parser.add_argument(
        'command',
        nargs=1,
        type=six.text_type,
        choices=commands.keys()
    )
    args, extra = parser.parse_known_args()

    command_name = args.command[0]
    cmd_class = commands[command_name]

    started = time.time()
    logger.debug(
        'Command %s(%s) started',
        command_name,
        extra
    )
    jira = utils.lazy_get_jira()
    try:
        cmd_class.execute_command(
            extra, jira=jira, path=os.getcwd(), command_name=command_name
        )
    except GitCommandError as e:
        print(
            "Error (code: %s) while running git command." % (
                e.returncode
            )
        )
        print("")
        print("Command:")
        print("    %s" % e.command)
        print("")
        print("Output:")
        for line in e.output.decode('utf8').split('\n'):
            print("    %s" % line)
        print("")
        sys.exit(1)
    except NotTicketFolderException:
        if not getattr(cmd_class, 'TRY_SUBFOLDERS', False):
            print(
                "The command '%s' must be ran from within an issue folder." % (
                    command_name
                )
            )
            sys.exit(1)
        count_runs = 0
        for folder in os.listdir(os.getcwd()):
            try:
                cmd_class.execute_command(
                    extra,
                    jira=jira,
                    path=os.path.join(
                        os.getcwd(),
                        folder,
                    ),
                    command_name=command_name,
                )
                count_runs += 1
            except NotTicketFolderException:
                pass
        if count_runs == 0:
            print(
                "The command '%s' must be ran from within an issue folder "
                "or from within a folder containing issue folders." % (
                    command_name
                )
            )
            sys.exit(1)
    except JirafsError as e:
        print("Jirafs encountered an error processing your request: %s" % e)

    logger.debug(
        'Command %s(%s) finished in %s seconds',
        command_name,
        extra,
        (time.time() - started)
    )
