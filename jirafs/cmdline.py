import argparse
import logging
import os
import sys
import time

from blessings import Terminal
import six
from verlib import NormalizedVersion

from . import utils
from .exceptions import (
    GitCommandError,
    JiraInteractionFailed,
    JirafsError,
    NotTicketFolderException
)


logger = logging.getLogger(__name__)


def main():
    term = Terminal()
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
        type=six.text_type,
        choices=commands.keys()
    )
    parser.add_argument(
        '--subtasks',
        action='store_true',
        default=False
    )
    args, extra = parser.parse_known_args()

    command_name = args.command
    cmd_class = commands[command_name]

    # Subtasks
    if args.subtasks:
        cmd_class.RUN_FOR_SUBTASKS = True

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
            u"{t.red}Error (code: {code}) while running git "
            u"command.{t.normal}".format(
                t=term,
                code=e.returncode
            )
        )
        print("")
        print(u"{t.red}Command:{t.normal}{t.red}{t.bold}".format(t=term))
        print(u"    {cmd}".format(cmd=e.command))
        print(u"{t.normal}".format(t=term))
        print(u"{t.red}Output:{t.normal}{t.red}{t.bold}".format(t=term))
        for line in e.output.decode('utf8').split('\n'):
            print(u"    %s" % line)
        print(u"{t.normal}".format(t=term))
        sys.exit(10)
    except NotTicketFolderException:
        if not getattr(cmd_class, 'TRY_SUBFOLDERS', False):
            print(
                u"{t.red}The command '{cmd}' must be ran from "
                u"within an issue folder.{t.normal}".format(
                    t=term,
                    cmd=command_name
                )
            )
            sys.exit(20)
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
                u"{t.red}The command '{cmd}' must be ran from "
                u"within an issue folder or from within a folder containing "
                u"issue folders.{t.normal}".format(
                    t=term,
                    cmd=command_name
                )
            )
            sys.exit(21)
    except JiraInteractionFailed as e:
        print(
            u"{t.red}JIRA was unable to satisfy your "
            u"request: {t.normal}{t.red}{t.bold}{error}{t.normal}".format(
                t=term,
                error=str(e)
            )
        )
        sys.exit(80)
    except JirafsError as e:
        print(
            u"{t.red}Jirafs encountered an error processing your "
            u"request: {t.normal}{t.red}{t.bold}{error}{t.normal}".format(
                t=term,
                error=str(e)
            )
        )
        sys.exit(90)

    logger.debug(
        'Command %s(%s) finished in %s seconds',
        command_name,
        extra,
        (time.time() - started)
    )
