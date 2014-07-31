import argparse
import json
import logging
import os
import subprocess
import sys
import time
import webbrowser

from blessings import Terminal
import ipdb
import six
from six.moves import configparser
from six.moves.urllib import parse
from verlib import NormalizedVersion

from . import utils
from .exceptions import (
    CannotInferTicketNumberFromFolderName,
    GitCommandError,
    JirafsError,
    LocalCopyOutOfDate,
    NotTicketFolderException
)
from .ticketfolder import TicketFolder


logger = logging.getLogger(__name__)


COMMANDS = {}


def command(desc, name=None, try_subfolders=False, aliases=None):
    def decorator(func):
        func_name = name or func.__name__
        func.description = desc
        func.try_subfolders = try_subfolders
        COMMANDS[func_name] = func
        if aliases:
            for alias in aliases:
                COMMANDS[alias] = func
        return func
    return decorator


def short_status_line(folder):
    return (
        "On ticket {ticket} ({url})".format(
            ticket=folder.ticket_number,
            url=folder.cached_issue.permalink(),
        )
    )


@command('Fetch remote changes', try_subfolders=True)
def fetch(args, jira, path, **kwargs):
    parser = argparse.ArgumentParser()
    parser.parse_args(args)

    folder = TicketFolder(path, jira)
    folder.fetch()


@command('Merge remote changes into your local copy', try_subfolders=True)
def merge(args, jira, path, **kwargs):
    parser = argparse.ArgumentParser()
    parser.parse_args(args)

    folder = TicketFolder(path, jira)
    folder.merge()


@command('Fetch and apply remote changes locally', try_subfolders=True)
def pull(args, jira, path, **kwargs):
    parser = argparse.ArgumentParser()
    parser.parse_args(args)

    folder = TicketFolder(path, jira)
    folder.pull()


@command('Commit local changes for later pushing to JIRA')
def commit(args, jira, path, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--message', default='Untitled')
    args, extra = parser.parse_known_args(args)

    kwargs = {}
    if args.message:
        kwargs['message'] = args.message

    folder = TicketFolder(path, jira)
    try:
        folder.commit(args.message, *extra)
    except subprocess.CalledProcessError:
        print("No changes to commit")


@command('Push local changes to JIRA', try_subfolders=True)
def push(args, jira, path, **kwargs):
    parser = argparse.ArgumentParser()
    parser.parse_args(args)

    folder = TicketFolder(path, jira)
    try:
        folder.push()
        folder.pull()
    except LocalCopyOutOfDate:
        print(
            "Your local copy is out-of-date; please run "
            "`jirafs merge` to merge changes from JIRA."
        )


@command('Run a command in this issue\'s git repository')
def git(args, jira, path, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--no-migrate',
        dest='migrate',
        default=True,
        action='store_false',
    )
    args, extra = parser.parse_known_args(args)

    folder = TicketFolder(path, jira, migrate=args.migrate)
    print(folder.run_git_command(*extra))


@command('Print the log for this issue')
def log(args, jira, path, **kwargs):
    parser = argparse.ArgumentParser()
    parser.parse_known_args(args)

    folder = TicketFolder(path, jira)
    print(folder.get_log())


@command('Open debug console')
def debug(args, jira, path, **kwargs):
    folder = TicketFolder(path, jira)
    ipdb.set_trace()


@command('List which plugins are currently enabled')
def plugins(args, jira, path, **kwargs):
    def build_plugin_dict(enabled, available):
        all_plugins = {}
        for plugin_name, cls in available.items():
            all_plugins[plugin_name] = {
                'enabled': False,
                'class': cls,
            }
        for plugin_instance in enabled:
            plugin_name = plugin_instance.plugin_name
            all_plugins[plugin_name]['enabled'] = True
            all_plugins[plugin_name]['instance'] = plugin_instance

        return all_plugins

    t = Terminal()
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true', default=False)
    parser.add_argument(
        '--enabled-only',
        dest='enabled_only',
        action='store_true',
        default=False
    )
    parser.add_argument(
        '--disabled-only',
        dest='disabled_only',
        action='store_true',
        default=False
    )
    parser.add_argument(
        '--enable',
    )
    parser.add_argument(
        '--disable',
    )
    parser.add_argument(
        '--global',
        dest='set_global',
        default=False,
        action='store_true',
    )
    args = parser.parse_args(args)

    if args.disabled_only and args.enabled_only:
        parser.error(
            "--disabled-only and --enabled-only are mutually exclusive."
        )

    folder = TicketFolder(path, jira, quiet=True)
    enabled_plugins = folder.load_plugins()
    available_plugins = utils.get_installed_plugins()

    if args.enable:
        if args.enable not in available_plugins:
            parser.error(
                "Plugin '%s' is not installed." % args.enable
            )
        if args.set_global:
            utils.set_global_config_value(
                'plugins', args.enable, 'enabled',
            )
        else:
            folder.set_config_value(
                'plugins', args.enable, 'enabled'
            )
    elif args.disable:
        if args.set_global:
            utils.set_global_config_value(
                'plugins', args.disable, 'disabled',
            )
        else:
            folder.set_config_value(
                'plugins', args.disable, 'disabled'
            )
    else:
        all_plugins = build_plugin_dict(enabled_plugins, available_plugins)

        for plugin_name, plugin_data in all_plugins.items():
            if plugin_data['enabled'] and args.disabled_only:
                continue
            if not plugin_data['enabled'] and args.enabled_only:
                continue
            if plugin_data['enabled']:
                color = t.bold
            else:
                color = t.normal

            print(
                color + plugin_name + t.normal
                + (' (Enabled)'
                    if plugin_data['enabled']
                    else (
                        ' (Disabled; enable by running `jirafs '
                        'plugins --enable=%s`)' % plugin_name
                    )
                )
            )
            if args.verbose:
                for line in plugin_data['class'].__doc__.strip().split('\n'):
                    print('     %s' % line)


@command('Get the status of the current folder', try_subfolders=True)
def status(args, jira, path, **kwargs):
    t = Terminal()

    def format_field_changes(changes, color, no_upload=False):
        lines = []
        color = getattr(t, color)
        normal = t.normal

        for filename in changes.get('files', []):
            lines.append(
                '\t' + color + filename + normal + (
                    ' (save to repository)' if no_upload else ' (file upload)'
                )
            )
        for field, value_set in changes.get('fields', {}).items():
            lines.append(
                '\t' + color + field + normal +
                ' (field changed from \'%s\' to \'%s\')' % value_set
            )
        if changes.get('new_comment', ''):
            lines.append(
                '\t' + color + '[New Comment]' + normal
            )
            for line in changes.get('new_comment', '').split('\n'):
                lines.append(
                    '\t\t' + line
                )

        return '\n'.join(lines)

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
        print(short_status_line(folder))
        folder_status = folder.status()
        if not folder_status['up_to_date']:
            print(
                t.magenta + "Warning: unmerged upstream changes exist; "
                "run `jirafs merge` to merge them into your local copy." +
                t.normal
            )

        printed_changes = False
        ready = folder_status['ready']
        if ready['files'] or ready['fields'] or ready['new_comment']:
            printed_changes = True
            print('')
            print(
                "Ready for upload; use `jirafs push` to update JIRA."
            )
            print(
                format_field_changes(ready, 'green')
            )

        staged = folder_status['uncommitted']
        if staged['files'] or staged['fields'] or staged['new_comment']:
            printed_changes = True
            print('')
            print(
                "Uncommitted changes; use `jirafs commit` to mark these "
                "for JIRA."
            )
            print(
                format_field_changes(staged, 'red')
            )

        local_uncommitted = folder_status['local_uncommitted']
        if local_uncommitted['files']:
            printed_changes = True
            print('')
            print(
                "Uncommitted changes prevented from being sent to JIRA "
                "because they match at least one of the patterns in your "
                ".jirafs_ignore file; use `jirafs commit` to commit these "
                "changes."
            )
            print(
                "Note: these files will " + t.bold + "not" + t.normal + " "
                "be uploaded to JIRA even after being committed."
            )
            print(
                format_field_changes(local_uncommitted, 'cyan', no_upload=True)
            )

        if not printed_changes:
            print('No changes found')
        else:
            print('')


@command(
    'Clone a new ticket folder for the specified ticket number',
    aliases=['get'],
)
def clone(args, jira, path, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'ticket_url',
        nargs=1,
        type=six.text_type
    )
    parser.add_argument(
        'path',
        nargs='*',
        type=six.text_type,
    )
    args = parser.parse_args(args)
    ticket_url = args.ticket_url[0]
    ticket_url_parts = parse.urlparse(ticket_url)
    if not ticket_url_parts.netloc:
        default_server = utils.get_default_jira_server()
        ticket_url = parse.urljoin(
            default_server,
            'browse/' + ticket_url + '/'
        )
    path = args.path[0] if args.path else None

    TicketFolder.clone(
        path=path,
        ticket_url=ticket_url,
        jira=jira,
    )


@command('Open this ticket in JIRA', try_subfolders=True, name='open')
def web_open(args, jira, path, **kwargs):
    parser = argparse.ArgumentParser()
    parser.parse_args(args)

    folder = TicketFolder(path, jira)

    webbrowser.open(folder.cached_issue.permalink())


@command('Show local issue changes')
def diff(args, jira, path, **kwargs):
    parser = argparse.ArgumentParser()
    parser.parse_args(args)

    folder = TicketFolder(path, jira)
    result = folder.run_git_command('diff')
    if result.strip():
        print(result)


@command('Get or set configuration values')
def config(args, jira, path, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--get', action='store_true')
    parser.add_argument('--set', action='store_true')
    parser.add_argument(
        '--global',
        dest='global_config',
        default=False,
        action='store_true'
    )
    parser.add_argument('params', nargs='*')
    args = parser.parse_args(args)
    if not args.list and not args.get and not args.set:
        parser.error(
            'Please specify action using either --list, '
            '--set, or --get.'
        )

    if args.global_config:
        config = utils.get_config()
    else:
        try:
            folder = TicketFolder(path, jira)
            config = folder.get_config()
        except NotTicketFolderException:
            config = utils.get_config()

    if args.list:
        if len(args.params) != 0:
            parser.error(
                "--list requires no parameters."
            )
        for section in config.sections():
            parameters = config.items(section)
            for key, value in parameters:
                line = (
                    "{section}.{key}={value}".format(
                        section=section,
                        key=key,
                        value=value
                    )
                )
                print(line)
    elif args.get:
        if len(args.params) != 1:
            parser.error(
                "--get requires exactly one parameter, the configuration "
                "value to display."
            )
        section, key = args.params[0].rsplit('.', 1)
        try:
            print(config.get(section, key))
        except configparser.Error:
            pass
    elif args.set:
        if len(args.params) != 2:
            parser.error(
                "--set requires exactly two parameters, the configuration "
                "key, and the configuration value."
            )
        section, key = args.params[0].rsplit('.', 1)
        value = args.params[1]

        if args.global_config:
            utils.set_global_config_value(section, key, value)
        else:
            try:
                folder = TicketFolder(path, jira)
                folder.set_config_value(
                    section, key, value
                )
            except NotTicketFolderException:
                parser.error(
                    "Not currently within a ticket folder.  To set a "
                    "global configuration value, use the --global option."
                )


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
    jira = utils.lazy_get_jira()
    try:
        fn(extra, jira=jira, path=os.getcwd())
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
    except (NotTicketFolderException, CannotInferTicketNumberFromFolderName):
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
    except JirafsError as e:
        print("Jirafs encountered an error processing your request: %s" % e)

    logger.debug(
        'Command %s(%s) finished in %s seconds',
        command_name,
        extra,
        (time.time() - started)
    )
