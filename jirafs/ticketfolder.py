import datetime
import fnmatch
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
        instance.log('Ticket folder created')
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
            return subprocess.check_call(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except subprocess.CalledProcessError:
            if not failure_ok:
                raise

    def get_ignore_globs(self, which=constants.IGNORE_FILE):
        all_globs = [
            constants.TICKET_DETAILS,
            constants.TICKET_COMMENTS,
        ]

        def get_globs_from_file(input_file):
            globs = []
            for line in input_file.readlines():
                if line.startswith('#') or not line.strip():
                    continue
                globs.append(line)
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

    def get_local_assets(self):
        ignore_globs = self.get_ignore_globs()

        assets = []
        for filename in os.listdir(self.path):
            if self.file_matches_globs(filename, ignore_globs):
                continue
            if not os.path.isfile(os.path.join(self.path, filename)):
                continue
            assets.append(filename)
        return assets

    def get_remote_assets(self):
        ignore_globs = self.get_ignore_globs(constants.REMOTE_IGNORE_FILE)

        assets = []
        for attachment in self.issue.fields.attachment:
            if not self.file_matches_globs(attachment.filename, ignore_globs):
                assets.append(attachment.filename)
        return assets

    def get_local_fields(self):
        fields = {}

        try:
            with open(
                self.get_local_path(constants.TICKET_DETAILS), 'r'
            ) as current_status:
                pass
        except IOError:
            pass

        return fields

    def get_original_values(self):
        return {}

    def get_local_differing_fields(self):
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
        for k, v in self.issue.raw['fields'].items():
            if original_values.get(k, '') != v:
                differing.append(k)

        return differing

    def sync(self):
        status = self.status()

        for filename in status['to_download']:
            for attachment in self.issue.fields.attachment:
                if attachment.filename == filename:
                    with open(self.get_local_path(filename), 'wb') as download:
                        self.log(
                            'Fetching file from %s',
                            (attachment.content, ),
                            logging.DEBUG
                        )
                        download.write(attachment.get())

        for filename in status['to_upload']:
            with open(self.get_local_path(filename), 'r') as upload:
                self.jira.add_attachment(
                    self.ticket_number,
                    upload
                )

        values = self.get_original_values()
        local_values = self.get_local_fields()

        for field in status['local_differs']:
            # TODO Upload local changes
            values[field] = local_values[field]

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
        self.run_git_command('commit', '-m', 'Synchronized', failure_ok=True)

    def status(self):
        local_assets = set(self.get_local_assets())
        remote_assets = set(self.get_remote_assets())

        status = {
            'to_download': remote_assets - local_assets,
            'to_upload': local_assets - remote_assets,
            'local_differs': self.get_local_differing_fields(),
            'remote_differs': self.get_remote_differing_fields(),
        }

        for key, item in status.items():
            self.log(
                'Current status; %s: %s',
                (
                    key,
                    item
                ),
                logging.DEBUG
            )

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
