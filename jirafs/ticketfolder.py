import datetime
import fnmatch
import json
import logging
import os
import re
import sys
import subprocess
import textwrap

from jira.resources import Issue
import six
from six.moves.urllib import parse
from six.moves import input

from . import constants
from . import exceptions
from . import migrations
from . import utils
from .decorators import run_plugins, stash_local_changes
from .jirafieldmanager import JiraFieldManager
from .plugin import PluginValidationError


logger = logging.getLogger(__name__)


class TicketFolder(object):
    def __init__(self, path, jira, migrate=True, quiet=False):
        self.path = os.path.realpath(
            os.path.expanduser(path)
        )
        self.quiet = quiet
        self.issue_url = self.get_ticket_url()
        self.get_jira = jira
        self.plugins = self.load_plugins()

        if not os.path.isdir(self.metadata_dir):
            raise exceptions.NotTicketFolderException(
                "%s is not a synchronizable ticket folder" % (
                    path
                )
            )

        if migrate:
            self.run_migrations()

        # If no `new_comment.jira.txt` file exists, let's create one
        comment_path = self.get_local_path(constants.TICKET_NEW_COMMENT)
        if not os.path.exists(comment_path):
            with open(comment_path, 'w') as out:
                out.write('')

    def execute_plugin_method_series(
        self, name, args=None, kwargs=None, single_response=False
    ):
        if args is None:
            args = []
            use_kwargs = True
        if kwargs is None:
            kwargs = {}
            use_kwargs = False

        if use_kwargs and single_response:
            raise RuntimeError(
                "When executing plugins in series using `single` response "
                "mode, you must specify only args."
            )
        elif args and kwargs:
            raise RuntimeError(
                "Plugins can be ran in series using either args or "
                "kwargs, not both."
            )

        for plugin in self.plugins:
            if not hasattr(plugin, name):
                continue
            method = getattr(plugin, name)
            plugin_result = method(*args, **kwargs)
            if plugin_result is not None:
                if use_kwargs:
                    kwargs = plugin_result
                elif single_response:
                    args = (plugin_result, )
                else:
                    args = plugin_result

        if use_kwargs:
            return kwargs
        elif single_response:
            return args[0]
        return args

    def load_plugins(self):
        config = self.get_config()
        plugins = []

        if not config.has_section(constants.CONFIG_PLUGINS):
            return plugins

        installed_plugins = utils.get_installed_plugins()

        for name, status in config.items(constants.CONFIG_PLUGINS):
            if not utils.convert_to_boolean(status):
                # This plugin is not turned on.
                continue
            if name not in installed_plugins:
                # This plugin is not installed.
                self.log(
                    "Plugin '%s' is not available.",
                    (name, ),
                )
                continue

            plugin = installed_plugins[name](self, name)

            try:
                plugin.validate()
            except PluginValidationError as e:
                self.log(
                    "Plugin '%s' did not pass validation; not loading: %s.",
                    (name, e,)
                )

            plugins.append(plugin)

        return plugins

    def get_config(self):
        local_config_file = self.get_metadata_path('config')
        additional_configs = []
        if os.path.exists(local_config_file):
            additional_configs.append(
                local_config_file
            )

        return utils.get_config(additional_configs)

    @stash_local_changes
    def set_config_value(self, section, key, value):
        local_config_file = self.get_metadata_path('config')

        config = utils.get_config(
            additional_configs=[
                local_config_file,
            ],
            include_global=False,
        )
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, key, value)

        with open(local_config_file, 'w') as out:
            config.write(out)

        self.run_git_command('add', '.jirafs/config')
        self.run_git_command(
            'commit', '-m', 'Config change',
            failure_ok=True
        )

    @property
    def jira_base(self):
        parts = parse.urlparse(self.issue_url)
        return '{scheme}://{netloc}'.format(
            scheme=parts.scheme,
            netloc=parts.netloc,
        )

    @property
    def ticket_number(self):
        parts = parse.urlparse(self.issue_url)
        match = re.match('\/browse\/(\w+-\d+)\/?.*', parts.path)
        if not match:
            raise ValueError(
                "Could not infer ticket number from URL %s" % self.issue_url
            )
        return match.group(1)

    @property
    def jira(self):
        if not hasattr(self, '_jira'):
            self._jira = self.get_jira(
                self.jira_base,
                config=self.get_config()
            )
        return self._jira

    @property
    def issue(self):
        if not hasattr(self, '_issue'):
            self._issue = self.jira.issue(self.ticket_number)
        return self._issue

    def store_cached_issue(self, shadow=True):
        storable = {
            'options': self.issue._options,
            'raw': self.issue.raw
        }
        with open(
            self.get_path('.jirafs/issue.json', shadow=shadow), 'w'
        ) as out:
            out.write(
                json.dumps(
                    storable,
                    indent=4,
                    sort_keys=True,
                )
            )

    @property
    def cached_issue(self):
        if not hasattr(self, '_cached_issue'):
            try:
                issue_path = self.get_metadata_path('issue.json')
                with open(issue_path, 'r') as _in:
                    storable = json.loads(_in.read())
                    self._cached_issue = Issue(
                        storable['options'],
                        None,
                        storable['raw'],
                    )
            except IOError:
                self.log(
                    'Error encountered while loading cached issue!',
                    level=logging.ERROR,
                )
                self._cached_issue = self.issue
        return self._cached_issue

    @property
    def metadata_dir(self):
        return os.path.join(
            self.path,
            constants.METADATA_DIR,
        )

    @property
    def git_merge_base(self):
        return self.run_git_command(
            'merge-base', 'master', 'jira',
        )

    def get_ticket_url(self):
        if os.path.isfile(self.get_metadata_path('issue_url')):
            with open(self.get_metadata_path('issue_url'), 'r') as in_:
                return in_.read().strip()

        jira_base = utils.get_default_jira_server()
        ticket_number = self.infer_ticket_number()
        return parse.urljoin(
            jira_base,
            'browse/' + ticket_number + '/',
        )

    def infer_ticket_number(self):
        raw_number = self.path.split('/')[-1:][0].upper()
        if not re.match('^\w+-\d+$', raw_number):
            raise exceptions.CannotInferTicketNumberFromFolderName(
                "Cannot infer ticket number from folder %s. Please name "
                "ticket folders after the ticket they represent." % (
                    self.path,
                )
            )
        return raw_number

    def get_metadata_path(self, *args):
        return os.path.join(
            self.metadata_dir,
            *args
        )

    def get_remote_file_metadata(self, shadow=True):
        remote_files = self.get_path(
            '.jirafs/remote_files.json',
            shadow=shadow
        )
        try:
            with open(remote_files, 'r') as _in:
                data = json.loads(_in.read())
        except IOError:
            data = {}

        return self.execute_plugin_method_series(
            'alter_get_remote_file_metadata',
            args=(data, ),
            single_response=True,
        )

    def set_remote_file_metadata(self, data, shadow=True):
        data = self.execute_plugin_method_series(
            'alter_set_remote_file_metadata',
            args=(data, ),
            single_response=True,
        )
        remote_files = self.get_path(
            '.jirafs/remote_files.json',
            shadow=shadow
        )
        with open(remote_files, 'w') as out:
            out.write(
                json.dumps(
                    data,
                    indent=4,
                    sort_keys=True,
                )
            )

    def get_local_path(self, *args):
        return os.path.join(
            self.path,
            *args
        )

    def get_shadow_path(self, *args):
        return os.path.join(
            self.get_metadata_path('shadow'),
            *args
        )

    def get_path(self, *args, **kwargs):
        shadow = kwargs.get('shadow', False)

        if shadow:
            return self.get_shadow_path(*args)
        return self.get_local_path(*args)

    @property
    def version(self):
        try:
            with open(self.get_metadata_path('version'), 'r') as _in:
                return int(_in.read().strip())
        except IOError:
            return 1

    @property
    def log_path(self):
        return self.get_metadata_path(constants.TICKET_OPERATION_LOG)

    @classmethod
    def initialize_ticket_folder(cls, ticket_url, path, jira):
        path = os.path.realpath(path)

        metadata_path = os.path.join(
            path,
            constants.METADATA_DIR,
        )
        os.mkdir(metadata_path)

        with open(os.path.join(metadata_path, 'issue_url'), 'w') as out:
            out.write(ticket_url)

        # Create bare git repository so we can easily detect changes.
        excludes_path = os.path.join(metadata_path, 'gitignore')
        with open(excludes_path, 'w') as gitignore:
            gitignore.write(
                '\n'.join(
                    [
                        '%s/git' % constants.METADATA_DIR,
                        '%s/shadow' % constants.METADATA_DIR,
                        '%s/operation.log' % constants.METADATA_DIR,
                    ]
                )
            )

        subprocess.check_call(
            (
                'git',
                '--bare',
                'init',
                os.path.join(
                    metadata_path,
                    'git',
                )
            ),
            stdout=subprocess.PIPE
        )
        subprocess.check_call((
            'git',
            'config',
            '--file=%s' % os.path.join(
                metadata_path,
                'git',
                'config'
            ),
            'core.excludesfile',
            '.jirafs/gitignore',
        ))

        instance = cls(path, jira, migrate=False)
        instance.log(
            'Ticket folder for issue %s created at %s',
            (instance.ticket_number, instance.path, )
        )
        instance.run_git_command(
            'add', '-A'
        )
        instance.run_git_command(
            'commit', '--allow-empty', '-m', 'Initialized'
        )
        instance.run_migrations(init=True)

        comment_path = instance.get_local_path(constants.TICKET_NEW_COMMENT)
        with open(comment_path, 'w') as out:
            out.write('')

        return instance

    @classmethod
    def clone(cls, ticket_url, jira, path=None):
        match = re.match('.*\/browse\/(\w+-\d+)\/?', ticket_url)
        if not match:
            raise exceptions.JirafsError(
                    "\'%s\' is not a valid JIRA ticket URL." % (
                        ticket_url
                    )
            )
        if not path:
            path = match.group(1)
        path = os.path.realpath(path)
        os.mkdir(path)
        folder = cls.initialize_ticket_folder(ticket_url, path, jira)
        folder.pull()
        return folder

    def run_git_command(self, command, *args, **kwargs):
        failure_ok = kwargs.get('failure_ok', False)
        shadow = kwargs.get('shadow', False)
        binary = kwargs.get('binary', False)

        args = list(args)

        if not shadow:
            work_tree = self.path,
            git_dir = self.get_metadata_path('git')
        else:
            work_tree = self.get_metadata_path('shadow')
            git_dir = self.get_metadata_path('shadow/.git')

        cmd = [
            'git',
            '--work-tree=%s' % work_tree,
            '--git-dir=%s' % git_dir,
        ]
        cmd.append(command)
        if command == 'commit':
            args.append(
                "--author='%s'" % constants.GIT_AUTHOR
            )
        cmd.extend(args)

        self.log('Executing git command %s', (cmd, ), logging.DEBUG)
        try:
            result = subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT
            )
            if not binary:
                return result.decode('utf-8').strip()
            return result
        except subprocess.CalledProcessError as e:
            if not failure_ok:
                command = ' '.join(cmd)
                raise exceptions.GitCommandError(
                    "Error running command `%s`" % command,
                    inner_exception=e,
                    cmd=command
                )

    def get_local_file_at_revision(
        self, path, revision, failure_ok=True, binary=False
    ):
        return self.run_git_command(
            'show', '%s:%s' % (
                revision,
                path,
            ),
            failure_ok=failure_ok,
            binary=binary,
        )

    def get_ignore_globs(self, which=constants.IGNORE_FILE):
        all_globs = [
            constants.TICKET_DETAILS,
            constants.TICKET_COMMENTS,
            constants.TICKET_NEW_COMMENT,
        ]
        for field in constants.FILE_FIELDS:
            all_globs.append(
                constants.TICKET_FILE_FIELD_TEMPLATE.format(field_name=field)
            )

        def get_globs_from_file(input_file):
            globs = []
            for line in input_file.readlines():
                if line.startswith('#') or not line.strip():
                    continue
                globs.append(line.strip())
            return globs

        try:
            with open(self.get_local_path(which)) as local_ign:
                all_globs.extend(
                    get_globs_from_file(local_ign)
                )
        except IOError:
            pass

        try:
            with open(os.path.expanduser('~/%s' % which)) as global_ignores:
                all_globs.extend(
                    get_globs_from_file(global_ignores)
                )
        except IOError:
            pass

        return all_globs

    def file_matches_globs(self, filename, ignore_globs):
        for glob in ignore_globs:
            if fnmatch.fnmatch(filename, glob):
                return True
        return False

    def get_ready_changes(self):
        changed_files = self.filter_ignored_files(
            self.run_git_command(
                'diff',
                '--name-only',
                '%s..master' % self.git_merge_base,
            ).split('\n')
        )

        return {
            'fields': (
                self.get_fields('HEAD') - self.get_fields(self.git_merge_base)
            ),
            'files': changed_files,
            'new_comment': self.get_new_comment(ready=True)
        }

    def get_uncommitted_changes(self):
        new_files = self.run_git_command(
            'ls-files', '-o', failure_ok=True
        ).split('\n')
        modified_files = self.run_git_command(
            'ls-files', '-m', failure_ok=True
        ).split('\n')

        return {
            'files': self.filter_ignored_files([
                filename for filename in new_files + modified_files if filename
            ]),
            'fields': self.get_fields() - self.get_fields('HEAD'),
            'new_comment': self.get_new_comment(ready=False)
        }

    def get_local_uncommitted_changes(self):
        new_files = self.run_git_command(
            'ls-files', '-o', failure_ok=True
        ).split('\n')
        modified_files = self.run_git_command(
            'ls-files', '-m', failure_ok=True
        ).split('\n')

        committable = self.filter_ignored_files([
            filename for filename in new_files + modified_files if filename
        ])

        return {
            'files': self.filter_ignored_files([
                filename for filename in modified_files + new_files
                if filename not in committable
            ], which=constants.GIT_IGNORE_FILE)
        }


    def get_remotely_changed(self):
        metadata = self.get_remote_file_metadata(shadow=True)

        assets = []
        attachments = self.filter_ignored_files(
            self.issue.fields.attachment,
            constants.REMOTE_IGNORE_FILE
        )
        for attachment in attachments:
            changed = metadata.get(attachment.filename) != attachment.created
            if changed:
                assets.append(attachment.filename)

        return self.execute_plugin_method_series(
            name='alter_remotely_changed',
            args=(assets, ),
            single_response=True,
        )

    def filter_ignored_files(self, files, which=constants.IGNORE_FILE):
        ignore_globs = self.get_ignore_globs(which)

        assets = []
        for fileish in files:
            # Get the actual filename; this is a little gross -- apologies.
            filename = fileish
            attachment = False
            if not isinstance(fileish, six.string_types):
                filename = fileish.filename
                attachment = True

            if self.file_matches_globs(filename, ignore_globs):
                continue
            if (
                not attachment
                and not os.path.isfile(os.path.join(self.path, filename))
            ):
                continue
            if filename.startswith('.'):
                continue
            assets.append(fileish)

        return self.execute_plugin_method_series(
            name='alter_filter_ignored_files',
            args=(assets, ),
            single_response=True,
        )

    def get_fields(self, revision=None, path=None):
        kwargs = {}
        if not revision:
            kwargs['path'] = path if path else self.path
        else:
            kwargs['revision'] = revision
        return JiraFieldManager.create(
            self,
            **kwargs
        )

    def get_new_comment(self, clear=False, staged=False, ready=True):
        try:
            with open(
                self.get_local_path(constants.TICKET_NEW_COMMENT), 'r+'
            ) as c:
                local_contents = c.read().strip()
            if ready:
                contents = self.get_local_file_at_revision(
                    constants.TICKET_NEW_COMMENT,
                    'HEAD'
                )
                if contents:
                    contents = contents.strip()
                else:
                    contents = ''
            else:
                contents = local_contents

            if not ready and contents == self.get_new_comment(ready=True):
                contents = ''

            if contents == local_contents and clear:
                with open(
                    self.get_local_path(constants.TICKET_NEW_COMMENT), 'r+'
                ) as c:
                    c.truncate()
        except IOError:
            contents = ''

        return self.execute_plugin_method_series(
            name='alter_new_comment',
            args=(contents, ),
            single_response=True,
        )

    @run_plugins(pre='pre_fetch', post='post_fetch')
    def fetch(self):
        file_meta = self.get_remote_file_metadata(shadow=True)
        original_hash = self.run_git_command('rev-parse', 'jira')

        for filename in self.get_remotely_changed():
            for attachment in self.issue.fields.attachment:
                if attachment.filename == filename:
                    self.log(
                        'Download file "%s"',
                        (attachment.filename, ),
                    )
                    content = six.BytesIO(attachment.get())
                    filename, content = self.execute_plugin_method_series(
                        'alter_file_download',
                        args=((filename, content, ),),
                        single_response=True,
                    )
                    save_path = self.get_shadow_path(filename)
                    with open(save_path, 'wb') as save_file:
                        content.seek(0)
                        save_file.write(content.read())
                        file_meta[filename] = attachment.created

        self.set_remote_file_metadata(file_meta, shadow=True)

        with open(self.get_shadow_path(constants.TICKET_DETAILS), 'w') as dets:
            for field in sorted(self.issue.raw['fields'].keys()):
                value = getattr(self.issue.fields, field)
                if isinstance(value, six.string_types):
                    value = value.replace('\r\n', '\n').strip()
                elif value is None:
                    value = ''
                elif field in constants.NO_DETAIL_FIELDS:
                    continue

                if not isinstance(value, six.string_types):
                    value = six.text_type(value)

                if field in constants.FILE_FIELDS:
                    # Write specific fields to their own files without
                    # significant alteration

                    file_field_path = self.get_shadow_path(
                        constants.TICKET_FILE_FIELD_TEMPLATE
                    ).format(field_name=field)
                    with open(file_field_path, 'w') as file_field_file:
                        file_field_file.write(value)
                        file_field_file.write('\n')  # For unix' sake
                else:
                    # Normal fields, though, just go into the standard
                    # fields file.
                    if value is None:
                        continue
                    elif field in constants.NO_DETAIL_FIELDS:
                        continue

                    dets.write('* %s:\n' % field)
                    for line in value.replace('\r\n', '\n').split('\n'):
                        dets.write('    %s\n' % line)

        comments_filename = self.get_shadow_path(constants.TICKET_COMMENTS)
        with open(comments_filename, 'w') as comm:
            for comment in self.issue.fields.comment.comments:
                comm.write(
                    '* At %s, %s wrote:\n\n' % (
                        comment.created,
                        comment.author
                    )
                )
                final_lines = []
                lines = comment.body.replace('\r\n', '\n').split('\n')
                for line in lines:
                    if not line:
                        final_lines.append('')
                    else:
                        final_lines.extend(
                            textwrap.wrap(
                                line,
                                width=70,
                                expand_tabs=False,
                                replace_whitespace=False,
                                break_long_words=False,
                            )
                        )
                for line in final_lines:
                    comm.write('    %s\n' % line)
                comm.write('\n')

        self.store_cached_issue()

        self.run_git_command('add', '-A', shadow=True)
        self.run_git_command(
            'commit', '-m', 'Pulled remote changes',
            failure_ok=True, shadow=True
        )
        self.run_git_command('push', 'origin', 'jira', shadow=True)
        final_hash = self.run_git_command('rev-parse', 'jira')
        return utils.PostStatusResponse(
            original_hash == final_hash,
            final_hash
        )

    @stash_local_changes
    @run_plugins(pre='pre_merge', post='post_merge')
    def merge(self):
        original_merge_base = self.git_merge_base
        self.run_git_command('merge', 'jira')
        final_merge_base = self.git_merge_base

        return utils.PostStatusResponse(
            original_merge_base == final_merge_base,
            final_merge_base
        )

    def pull(self):
        self.fetch()
        self.merge()

    def commit(self, message, *args):
        self.run_git_command(
            'add', '-A'
        )
        try:
            self.run_git_command(
                'commit', '-m', message, *args
            )
        except exceptions.GitCommandError:
            print("Nothing to commit")

    def is_up_to_date(self):
        jira_commit = self.run_git_command('rev-parse', 'jira')
        master_commit = self.run_git_command('rev-parse', 'master')

        try:
            self.run_git_command(
                'merge-base', '--is-ancestor', jira_commit, master_commit,
            )
        except exceptions.GitCommandError:
            return False
        return True

    @stash_local_changes
    @run_plugins(pre='pre_push', post='post_push')
    def push(self):
        status = self.status()
        original_hash = self.run_git_command('rev-parse', 'jira')

        if not self.is_up_to_date():
            raise exceptions.LocalCopyOutOfDate()

        file_meta = self.get_remote_file_metadata(shadow=False)

        for filename in status['ready']['files']:
            upload = six.BytesIO(
                self.get_local_file_at_revision(
                    filename,
                    'HEAD',
                    binary=True
                )
            )
            filename, upload = self.execute_plugin_method_series(
                'alter_file_upload',
                args=((filename, upload, ), ),
                single_response=True,
            )
            self.log(
                'Uploading file "%s"',
                (filename, ),
            )
            # Delete the existing issue if there is one
            for attachment in self.issue.fields.attachment:
                if attachment.filename == filename:
                    attachment.delete()
            upload.seek(0)
            attachment = self.jira.add_attachment(
                self.ticket_number,
                upload,
                filename=filename,
            )
            file_meta[filename] = attachment.created

        self.set_remote_file_metadata(file_meta, shadow=False)

        comment = self.get_new_comment(clear=True, ready=True)
        if comment:
            self.log('Adding comment "%s"' % comment)
            self.jira.add_comment(self.ticket_number, comment)

        collected_updates = {}
        for field, diff_values in status['ready']['fields'].items():
            collected_updates[field] = diff_values[1]

        if collected_updates:
            self.log(
                'Updating fields "%s"',
                (collected_updates, )
            )
            self.issue.update(**collected_updates)

        # Commit local copy
        self.run_git_command('reset', '--soft', failure_ok=True)
        self.run_git_command(
            'add', '.jirafs/remote_files.json', failure_ok=True
        )
        self.run_git_command(
            'add', constants.TICKET_NEW_COMMENT, failure_ok=True
        )
        self.run_git_command(
            'commit', '-m', 'Pushed local changes', failure_ok=True
        )

        # Commit changes to remote copy, too, so we record remote
        # file metadata.
        self.run_git_command('fetch', shadow=True)
        self.run_git_command('merge', 'origin/master', shadow=True)
        self.run_git_command('add', '-A', shadow=True)
        self.run_git_command(
            'commit', '-m', 'Pulled remote changes',
            failure_ok=True, shadow=True
        )
        self.run_git_command('push', 'origin', 'jira', shadow=True)
        final_hash = self.run_git_command('rev-parse', 'jira')
        return utils.PostStatusResponse(
            original_hash == final_hash,
            final_hash
        )

    @run_plugins(pre='pre_status', post='post_status')
    def status(self):
        status = {
            'uncommitted': self.get_uncommitted_changes(),
            'ready': self.get_ready_changes(),
            'local_uncommitted': self.get_local_uncommitted_changes(),
            'up_to_date': self.is_up_to_date(),
        }

        return status

    @stash_local_changes
    def run_migrations(self, init=False):
        loglevel = logging.INFO
        if init:
            loglevel = logging.DEBUG
        else:
            if self.version < constants.CURRENT_REPO_VERSION:
                print(
                    "Your ticket folder is out-of-date and must be updated.  "
                    "Although migrations will never affect the JIRA issue "
                    "itself, they may modify your local clone of the issue; "
                    "please record your current changes before proceeding."
                )
                result = utils.convert_to_boolean(input("Continue? (N/Y): "))
                if not result:
                    sys.exit(1)
        while self.version < constants.CURRENT_REPO_VERSION:
            migrator = getattr(
                migrations,
                'migration_%s' % str(self.version + 1).zfill(4)
            )
            self.migrate(migrator, loglevel=loglevel, init=init)

    def migrate(self, migrator, loglevel=logging.INFO, init=False):
        self.log('%s: Migration started', (migrator.__name__, ), loglevel)
        migrator(self, init=init)
        self.log('%s: Migration finished', (migrator.__name__, ), loglevel)

    def log(self, message, args=None, level=logging.INFO):
        if args is None:
            args = []
        logger.log(level, message, *args)
        with open(self.log_path, 'a') as log_file:
            log_file.write(
                "%s\t%s\t%s\n" % (
                    datetime.datetime.utcnow().isoformat(),
                    logging.getLevelName(level),
                    (message % args).replace('\n', '\\n')
                )
            )
        if level >= logging.INFO and not self.quiet:
            print(
                "[%s %s] %s" % (
                    logging.getLevelName(level),
                    self.issue,
                    message % args
                )
            )

    def get_log(self):
        with open(self.log_path, 'r') as log_file:
            return log_file.read()
