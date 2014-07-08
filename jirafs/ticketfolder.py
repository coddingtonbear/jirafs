import datetime
import fnmatch
import json
import logging
import os
import re
import subprocess

import six

from . import constants
from .exceptions import (
    CannotInferTicketNumberFromFolderName,
    NotTicketFolderException
)


logger = logging.getLogger(__name__)


class TicketFolder(object):
    def __init__(self, path, jira):
        self.path = os.path.realpath(
            os.path.expanduser(path)
        )
        self.jira = jira

        if not os.path.isdir(self.metadata_dir):
            raise NotTicketFolderException(
                "%s is not a synchronizable ticket folder" % (
                    path
                )
            )

        self.ticket_number = self.infer_ticket_number()

    def infer_ticket_number(self):
        raw_number = self.path.split('/')[-1:][0].upper()
        if not re.match('^\w+-\d+$', raw_number):
            raise CannotInferTicketNumberFromFolderName(
                "Cannot infer ticket number from folder %s. Please name "
                "ticket folders after the ticket they represent." % (
                    self.path,
                )
            )
        return raw_number

    @property
    def issue(self):
        if not hasattr(self, '_issue'):
            self._issue = self.jira.issue(self.ticket_number)
        return self._issue

    @property
    def metadata_dir(self):
        return os.path.join(
            self.path,
            constants.METADATA_DIR,
        )

    def get_metadata_path(self, filename):
        return os.path.join(
            self.metadata_dir,
            filename
        )

    def get_remote_file_metadata(self):
        try:
            with open(self.get_metadata_path('remote_files.json'), 'r') as _in:
                return json.loads(_in.read())
        except IOError:
            return {}

    def set_remote_file_metadata(self, data):
        with open(self.get_metadata_path('remote_files.json'), 'w') as out:
            out.write(
                json.dumps(data)
            )

    def get_local_path(self, filename):
        return os.path.join(
            self.path,
            filename
        )

    @property
    def log_path(self):
        return self.get_metadata_path(constants.TICKET_OPERATION_LOG)

    @classmethod
    def initialize_ticket_folder(cls, path, jira):
        path = os.path.realpath(path)

        metadata_path = os.path.join(
            path,
            constants.METADATA_DIR,
        )
        os.mkdir(metadata_path)

        # Create bare git repository so we can easily detect changes.
        excludes_path = os.path.join(metadata_path, 'gitignore')
        with open(excludes_path, 'w') as gitignore:
            gitignore.write(
                '%s\n' % constants.METADATA_DIR,
            )

        subprocess.check_call((
            'git',
            '--bare',
            'init',
            os.path.join(
                metadata_path,
                'git',
            )
        ))
        subprocess.check_call((
            'git',
            'config',
            '--file=%s' % os.path.join(
                metadata_path,
                'git',
                'config'
            ),
            'core.excludesfile',
            excludes_path
        ))

        instance = cls(path, jira)
        instance.log(
            'Ticket folder for issue %s created at %s',
            (instance.ticket_number, instance.path, )
        )
        return instance

    @classmethod
    def create_ticket_folder(cls, path, jira):
        path = os.path.realpath(path)
        os.mkdir(path)
        folder = cls.initialize_ticket_folder(path, jira)
        return folder

    def run_git_command(self, *args, **kwargs):
        failure_ok = kwargs.get('failure_ok', False)
        cmd = [
            'git',
            '--work-tree=%s' % self.path,
            '--git-dir=%s' % self.get_metadata_path('git'),
        ]
        cmd.extend(args)
        self.log('Executing git command %s', cmd, logging.DEBUG)
        try:
            return subprocess.check_output(
                cmd,
                stderr=subprocess.PIPE
            ).decode('utf-8').strip()
        except subprocess.CalledProcessError:
            if not failure_ok:
                raise

    def create_empty_head(self):
        self.run_git_command('commit', '--allow-empty', '-m', 'Initialized')

    def get_ignore_globs(self, which=constants.IGNORE_FILE):
        all_globs = [
            constants.TICKET_DETAILS,
            constants.TICKET_COMMENTS,
            constants.TICKET_NEW_COMMENT,
        ]

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

    def get_locally_changed(self):
        ignore_globs = self.get_ignore_globs()

        new_files = self.run_git_command(
            'ls-files', '-o', failure_ok=True
        ).split('\n')
        modified_files = self.run_git_command(
            'ls-files', '-m', failure_ok=True
        ).split('\n')

        all_possible = [
            filename for filename in new_files + modified_files if filename
        ]

        assets = []
        for filename in all_possible:
            if self.file_matches_globs(filename, ignore_globs):
                continue
            if not os.path.isfile(os.path.join(self.path, filename)):
                continue
            if filename.startswith('.'):
                continue
            assets.append(filename)

        return assets

    def get_remotely_changed(self):
        ignore_globs = self.get_ignore_globs(constants.REMOTE_IGNORE_FILE)
        metadata = self.get_remote_file_metadata()

        assets = []
        for attachment in self.issue.fields.attachment:
            matches_globs = (
                self.file_matches_globs(attachment.filename, ignore_globs)
            )
            changed = metadata.get(attachment.filename) != attachment.created
            if not matches_globs and changed:
                assets.append(attachment.filename)
        return assets

    def get_field_data_from_string(self, string):
        """ Gets field data from an incoming string.

        0 | FIELD_NAME::
        1 |
        2 |     VALUE

        """
        FIELD_DECLARED = 0
        PREAMBLE = 1
        VALUE = 2

        state = None

        data = {}
        field_name = ''
        value = ''
        if not string:
            return data
        lines = string.split('\n')
        for idx, line in enumerate(lines):
            line = line.replace('\t', '    ')
            if state == FIELD_DECLARED and not line:
                state = PREAMBLE
            elif (
                (state == VALUE or state is None)
                and re.match('^(\w+)::', line)
            ):
                if value:
                    data[field_name] = value.strip()
                    value = ''
                state = FIELD_DECLARED
                field_name = re.match('^(\w+)::', line).group(1)
                if not field_name:
                    raise ValueError(
                        "Syntax error on line %s" % idx
                    )
            elif (state == PREAMBLE or state == VALUE) and line:
                state = VALUE
                value = value + '\n' + line[4:]  # Remove first indentation
        if value:
            data[field_name] = value.strip()

        return data

    def get_local_fields(self):
        try:
            with open(
                self.get_local_path(constants.TICKET_DETAILS), 'r'
            ) as current_status:
                return self.get_field_data_from_string(current_status.read())
        except IOError:
            pass

        return {}

    def get_original_values(self):
        head = self.run_git_command(
            'rev-parse', 'HEAD'
        )
        original_file = self.run_git_command(
            'show', '%s:%s' % (
                head,
                constants.TICKET_DETAILS
            ),
            failure_ok=True
        )
        return self.get_field_data_from_string(original_file)

    def get_local_differing_fields(self):
        """ Get fields that differ between local and the last sync

        .. warning::

           Does not support setting fields that were not set originally
           in a sync operation!

        """
        local_fields = self.get_local_fields()
        original_values = self.get_original_values()

        differing = []
        for k, v in original_values.items():
            if local_fields[k] != v:
                differing.append(k)

        return differing

    def get_remote_differing_fields(self):
        original_values = self.get_original_values()

        differing = []
        for k in self.issue.raw['fields'].keys():
            v = getattr(self.issue.fields, k)
            if isinstance(v, six.string_types):
                v = v.replace('\r\n', '\n').strip()
            elif v is None:
                v = ''
            elif k in constants.NO_DETAIL_FIELDS:
                continue
            if original_values.get(k, '') != six.text_type(v):
                differing.append(k)

        return differing

    def get_new_comment(self, clear=False):
        try:
            with open(
                self.get_local_path(constants.TICKET_NEW_COMMENT), 'r+'
            ) as c:
                comment = c.read().strip()
                if clear:
                    c.seek(0)
                    c.truncate()

            return comment
        except IOError:
            return ''

    def pull(self):
        status = self.status()

        file_meta = self.get_remote_file_metadata()

        for filename in status['to_download']:
            for attachment in self.issue.fields.attachment:
                if attachment.filename == filename:
                    with open(self.get_local_path(filename), 'wb') as download:
                        self.log(
                            'Download file "%s"',
                            (attachment.filename, ),
                        )
                        file_meta[filename] = attachment.created
                        download.write(attachment.get())

        self.set_remote_file_metadata(file_meta)

        values = self.get_original_values()

        for field in status['remote_differs']:
            values[field] = getattr(self.issue.fields, field)

        with open(self.get_local_path(constants.TICKET_DETAILS), 'w') as dets:
            for field, value in sorted(six.iteritems(values)):
                if value is None:
                    continue
                elif field in constants.NO_DETAIL_FIELDS:
                    continue
                elif not isinstance(value, six.string_types):
                    value = six.text_type(value)
                dets.write('%s::\n\n' % field)
                for line in value.replace('\r\n', '\n').split('\n'):
                    dets.write('    %s\n' % line)
                dets.write('\n')

        with open(self.get_local_path(constants.TICKET_COMMENTS), 'w') as comm:
            for comment in self.issue.fields.comment.comments:
                comm.write('%s: %s::\n\n' % (comment.created, comment.author))
                lines = comment.body.replace('\r\n', '\n').split('\n')
                for line in lines:
                    comm.write('    %s\n' % line)
                comm.write('\n')

        self.run_git_command('add', '-A')
        self.run_git_command(
            'commit', '-m', 'Pulled remote changes', failure_ok=True
        )

    def push(self):
        status = self.status()

        file_meta = self.get_remote_file_metadata()

        for filename in status['to_upload']:
            with open(self.get_local_path(filename), 'r') as upload:
                self.log(
                    'Uploading file "%s"',
                    (filename, ),
                )
                # Delete the existing issue if there is one
                for attachment in self.issue.fields.attachment:
                    if attachment.filename == filename:
                        attachment.delete()
                attachment = self.jira.add_attachment(
                    self.ticket_number,
                    upload
                )
                file_meta[filename] = attachment.created

        self.set_remote_file_metadata(file_meta)

        comment = self.get_new_comment(clear=True)
        if comment:
            self.log('Adding comment "%s"' % comment)
            self.jira.add_comment(self.ticket_number, comment)

        values = self.get_original_values()
        local_values = self.get_local_fields()

        collected_updates = {}
        for field in status['local_differs']:
            collected_updates[field] = local_values[field]
            values[field] = local_values[field]

        if collected_updates:
            self.log(
                'Updating fields "%s"',
                (collected_updates, )
            )
            self.issue.update(**collected_updates)

        self.run_git_command('add', '-A')
        self.run_git_command(
            'commit', '-m', 'Pushed local changes', failure_ok=True
        )

    def sync(self):
        self.push()
        self.pull()

    def status(self):
        locally_changed = self.get_locally_changed()
        remotely_changed = self.get_remotely_changed()

        status = {
            'to_upload': locally_changed,
            'to_download': remotely_changed,
            'local_differs': self.get_local_differing_fields(),
            'remote_differs': self.get_remote_differing_fields(),
            'new_comment': self.get_new_comment()
        }

        return status

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
        if level >= logging.INFO:
            print(
                "[%s %s] %s" % (
                    logging.getLevelName(level),
                    self.issue,
                    message % args
                )
            )
