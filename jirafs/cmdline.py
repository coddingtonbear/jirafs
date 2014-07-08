import argparse
import json
import logging
import os
import sys
import time
import webbrowser

import six

from .exceptions import NotTicketFolderException
from .ticketfolder import TicketFolder
from .utils import get_jira


logger = logging.getLogger(__name__)


COMMANDS = {}


def command(desc, name=None, try_subfolders=True):
    def decorator(func):
        func_name = name or func.__name__
        func.description = desc
        func.try_subfolders = try_subfolders
        COMMANDS[func_name] = func
        return func
    return decorator


@command('Synchronize folder(s) with JIRA', try_subfolders=True)
def sync(args, jira, path, **kwargs):
    parser = argparse.ArgumentParser()
    parser.parse_args(args)

    folder = TicketFolder(path, jira)
    folder.sync()


@command('Fetch and apply remote changes locally', try_subfolders=True)
def pull(args, jira, path, **kwargs):
    parser = argparse.ArgumentParser()
    parser.parse_args(args)

    folder = TicketFolder(path, jira)
    folder.pull()


@command('Push local changes to JIRA', try_subfolders=True)
def push(args, jira, path, **kwargs):
    parser = argparse.ArgumentParser()
    parser.parse_args(args)

    folder = TicketFolder(path, jira)
    folder.push()


@command('Create a new ticket folder at your current path')
def init(args, jira, path, **kwargs):
    parser = argparse.ArgumentParser()
    parser.parse_args(args)

    folder = TicketFolder.initialize_ticket_folder(path, jira)
    folder.create_empty_head()


@command('Get the status of the current folder', try_subfolders=True)
def status(args, jira, path, **kwargs):
    human_readable = {
        'to_download': 'Files ready to be downloaded from JIRA',
        'to_upload': 'Files ready to be uploaded to JIRA',
        'local_differs': 'The following fields have been changed locally',
        'remote_differs': 'The following fields have been changed in JIRA',
        'new_comment': 'The following comment is ready to be posted to JIRA',
    }

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--format',
        default='text',
        choices=['text', 'json']
    )
    args = parser.parse_args(args)

    folder = TicketFolder(path, jira)
    if args.format == 'json':
        print(json.dumps(folder.status()))
    else:
        for k, v in folder.status().items():
            human_heading = human_readable.get(k, k)  # Default to key name
            if v:
                if isinstance(v, six.string_types):
                    if not v:
                        continue
                    v = v.split('\n')
                print(human_heading + ':\n')
                for item in v:
                    print('\t' + item)
                print('')


@command('Get a new ticket folder for the specified ticket number')
def get(args, jira, path, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'ticket',
        nargs=1,
        type=six.text_type
    )
    args = parser.parse_args(args)
    ticket_number = args.ticket[0].upper()

    folder = TicketFolder.create_ticket_folder(ticket_number, jira)
    folder.sync()


@command('Open this ticket in JIRA', try_subfolders=True)
def open(args, jira, path, **kwargs):
    jira = kwargs.get('jira', get_jira())

    parser = argparse.ArgumentParser()
    parser.parse_args(args)

    folder = TicketFolder(path, jira)

    webbrowser.open(folder.issue.permalink())


def main():
    parser = argparse.ArgumentParser(
        description='Edit Jira issues locally from your filesystem',
    )
    parser.add_argument(
        'command',
        nargs=1,
        type=six.text_type,
        choices=COMMANDS.keys()
    )
    args, extra = parser.parse_known_args()

    command_name = args.command[0]
    fn = COMMANDS[command_name]
    started = time.time()
    logger.debug(
        'Command %s(%s) started',
        command_name,
        extra
    )
    jira = get_jira()
    try:
        fn(extra, jira=jira, path=os.getcwd())
    except NotTicketFolderException:
        if not fn.try_subfolders:
            print(
                "The command '%s' must be ran from within an issue folder." % (
                    command_name
                )
            )
            sys.exit(1)
        count_runs = 0
        for folder in os.listdir(os.getcwd()):
            try:
                fn(
                    extra,
                    jira=jira,
                    path=os.path.join(
                        os.getcwd(),
                        folder,
                    ),
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

    logger.debug(
        'Command %s(%s) finished in %s seconds',
        command_name,
        extra,
        (time.time() - started)
    )
