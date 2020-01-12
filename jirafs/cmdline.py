import argparse
import codecs
import copy
import logging
import logging.config
import os
import shlex
import subprocess
import sys
import time
import traceback

from blessings import Terminal

try:
    from jira.utils import JIRAError
except ImportError:
    from jira.exceptions import JIRAError
from distutils.version import LooseVersion

from . import utils
from .exceptions import (
    GitCommandError,
    JiraInteractionFailed,
    JirafsError,
    NotTicketFolderException,
    UnknownMacroError,
    MacroError,
)


# Write data to stdout as UTF-8 bytes when there's no encoding specified
if sys.version_info < (3,) and sys.stdout.encoding is None:
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout)


logger = logging.getLogger(__name__)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "pretty": {"format": "[%(levelname)s] %(message)s"},
        "file": {"format": "%(asctime)s\t%(levelname)s\t%(module)s\t%(message)s"},
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "pretty",
            "stream": "ext://sys.stdout",
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}


def main():
    term = Terminal()
    if sys.version_info < (2, 7):
        raise RuntimeError(
            "Jirafs requires minimally version 2.7 of Python 2, or "
            "any version of Python 3.  Please upgrade your version of "
            "python before using Jirafs."
        )
    if utils.get_git_version() < LooseVersion("1.8"):
        raise RuntimeError(
            "Jirafs requires minimally version 1.8 of Git.  Please "
            "upgrade your version of git before using Jirafs."
        )

    commands = utils.get_installed_commands()

    parser = argparse.ArgumentParser(
        description="Edit Jira issues locally from your filesystem", add_help=False,
    )
    parser.add_argument("command", type=str, choices=commands.keys())
    parser.add_argument("--subtasks", action="store_true", default=False)
    parser.add_argument(
        "--log-level", default="INFO", dest="log_level",
    )
    parser.add_argument("--folder", default=os.getcwd())
    parser.add_argument(
        "--no-subfolders", action="store_true", default=False,
    )
    parser.add_argument(
        "--traceback", action="store_true", default=False,
    )
    parser.add_argument(
        "--debugger-port",
        default=58024,
        help=("(Requires --debugger) start debugger on this port."),
    )
    parser.add_argument(
        "--debugger",
        action="store_true",
        default=False,
        help=("Launch ptvsd debugger on --debugger-port."),
    )
    args, extra = parser.parse_known_args()

    if args.debugger:
        try:
            import ptvsd

            ptvsd.enable_attach(address=("localhost", args.debugger_port))
            print(
                f"{term.magenta}Waiting for debugger connection on "
                f"port {args.debugger_port}...{term.normal}"
            )
            ptvsd.wait_for_attach()
        except ImportError:
            print(f"{term.red}Module 'ptvsd' required for debugging." f"{term.normal}")
            sys.exit(1)

    logging.config.dictConfig(LOGGING)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.getLevelName(args.log_level))

    command_name = args.command
    cmd_class = commands[command_name]

    # Subtasks
    if args.subtasks:
        cmd_class.RUN_FOR_SUBTASKS = True

    started = time.time()
    logger.debug("Command %s(%s) started", command_name, extra)
    jira = utils.lazy_get_jira()
    try:
        value = cmd_class.execute_command(
            extra, jira=jira, path=args.folder, command_name=command_name
        )
        logger.debug(
            "Command %s(%s) finished in %s seconds",
            command_name,
            extra,
            (time.time() - started),
        )
        if value:
            value.echo()
        sys.exit(value.return_code)
    except GitCommandError as e:
        print(
            "{t.red}Error (code: {code}) while running git "
            "command.{t.normal}".format(t=term, code=e.returncode)
        )
        print("")
        print("{t.red}Command:{t.normal}{t.red}{t.bold}".format(t=term))
        print("    {cmd}".format(cmd=e.command))
        print("{t.normal}".format(t=term))
        print("{t.red}Output:{t.normal}{t.red}{t.bold}".format(t=term))
        for line in e.output.decode("utf8").split("\n"):
            print("    %s" % line)
        print("{t.normal}".format(t=term))
        if args.traceback:
            traceback.print_exc()
        sys.exit(10)
    except NotTicketFolderException:
        if not getattr(cmd_class, "TRY_SUBFOLDERS", False):
            print(
                "{t.red}The command '{cmd}' must be ran from "
                "within an issue folder.{t.normal}".format(t=term, cmd=command_name)
            )
            sys.exit(20)
        elif args.no_subfolders:
            sys.exit(20)

        count_runs = 0
        for folder in os.listdir(os.getcwd()):
            full_path = os.path.join(os.getcwd(), folder,)
            if not os.path.isdir(full_path):
                continue

            try:
                full_args = copy.copy(sys.argv)
                if "--no-subfolders" not in full_args:
                    full_args.append("--no-subfolders")
                result = subprocess.call(
                    " ".join([shlex.quote(a) for a in full_args]),
                    cwd=full_path,
                    shell=True,
                )
                if result == 0:
                    count_runs += 1
            except NotTicketFolderException:
                pass
        if count_runs == 0:
            if args.traceback:
                traceback.print_exc()
            sys.exit(21)
    except UnknownMacroError as e:
        print(
            "{t.red}Jirafs encountered an unknown macro while processing "
            "your content: {t.normal}{t.red}{t.bold}{error}"
            "{t.normal}".format(t=term, error=str(e))
        )
        if args.traceback:
            traceback.print_exc()
        sys.exit(30)
    except MacroError as e:
        print(
            "{t.red}Jirafs encountered an error while processing a "
            "{t.bold}{macro}{t.normal}{t.red} macro: "
            "{t.normal}{t.red}{t.bold}{error}{t.normal}".format(
                t=term, macro=e.macro_name or "?", error=str(e)
            )
        )
        if args.traceback:
            traceback.print_exc()
        sys.exit(40)
    except JIRAError as e:
        print(
            "{t.red}Jirafs encountered an error while interacting with "
            "your JIRA instance: {t.normal}{t.red}{t.bold}{error}"
            "{t.normal}".format(t=term, error=str(e))
        )
        if args.traceback:
            traceback.print_exc()
        sys.exit(70)
    except JiraInteractionFailed as e:
        print(
            "{t.red}JIRA was unable to satisfy your "
            "request: {t.normal}{t.red}{t.bold}{error}{t.normal}".format(
                t=term, error=str(e)
            )
        )
        if args.traceback:
            traceback.print_exc()
        sys.exit(80)
    except JirafsError as e:
        print(
            "{t.red}Jirafs encountered an error processing your "
            "request: {t.normal}{t.red}{t.bold}{error}{t.normal}".format(
                t=term, error=str(e)
            )
        )
        if args.traceback:
            traceback.print_exc()
        sys.exit(90)
