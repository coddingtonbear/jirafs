import json
import os
import re

from jirafs import constants
from jirafs.readers import GitRevisionReader, WorkingCopyReader


class JiraFieldManager(dict):
    FIELD_MATCHER = re.compile(
        '^%s$' % (
            constants.TICKET_FILE_FIELD_TEMPLATE.replace(
                '{field_name}', '([\w_]+)'
            )
        )
    )

    def __init__(self, data=None, prepared=False):
        if not prepared:
            self._data = self.get_fields_from_string(data)
        else:
            self._data = data
        super(JiraFieldManager, self).__init__(self._data)

    def __sub__(self, other):
        differing = {}
        for k, v in other.items():
            if self.get(k) != v:
                differing[k] = (v, self.get(k), )

        return differing

    @classmethod
    def create(cls, folder, revision=None, path=None):
        if revision and path:
            raise TypeError(
                'You may specify a git revision or a local path; not both.'
            )

        if revision:
            return GitRevisionJiraFieldManager(folder, revision)
        else:
            return WorkingCopyJiraFieldManager(folder, path)

    def get_requested_per_ticket_fields(self):
        return constants.FILE_FIELDS

    def get_used_per_ticket_fields(self):
        raise NotImplementedError()

    def set_data_value(self, data, field_name, raw_value):
        raw_value = raw_value.strip()
        try:
            value = json.loads(raw_value)
        except (TypeError, ValueError):
            value = raw_value
        data[field_name] = value

    def get_fields_from_string(self, string):
        """ Gets field data from an incoming string.

        Parses through the string using the following RST-derived
        pattern::

            0 | * Field
            1 |     VALUE
            2 |     MORE VALUE

        """
        data = {}
        field_name = ''
        value = ''
        if not string:
            return data
        lines = string.split('\n')
        for idx, line in enumerate(lines):
            if line.startswith('*'):
                if value:
                    self.set_data_value(data, field_name, value)
                    value = ''
                raw_field_name = re.match('^\* ([^:]+):$', line).group(1)
                if '(' in raw_field_name:
                    # This field name's real name doesn't match the field ID
                    field_name = re.match(
                        '.*\(([^)]+)\)',
                        raw_field_name
                    ).group(1)
                else:
                    field_name = raw_field_name.replace(' ', '_')
            elif field_name:
                value = value + '\n' + line.strip()
        if value:
            self.set_data_value(data, field_name, value)

        return data


class AutomaticJiraFieldManager(JiraFieldManager):
    def __init__(self):
        data = self.load()
        super(AutomaticJiraFieldManager, self).__init__(data, prepared=True)

    def load(self):
        fields = self.get_fields_from_string(
            self.get_file_contents(constants.TICKET_DETAILS)
        )

        used_fields = set(self.get_used_per_ticket_fields())
        requested_fields = set(self.get_requested_per_ticket_fields())

        file_fields = {}
        for field_name in used_fields | requested_fields:
            try:
                field_path = constants.TICKET_FILE_FIELD_TEMPLATE.format(
                    field_name=field_name
                )
                file_fields[field_name] = self.get_file_contents(field_path)
            except (IOError, OSError):
                pass

        fields.update(file_fields)
        return fields

    def get_file_contents(self, path):
        raise NotImplemented()


class WorkingCopyJiraFieldManager(
    WorkingCopyReader, AutomaticJiraFieldManager
):
    def get_used_per_ticket_fields(self):
        fields = []
        for filename in os.listdir(self.path):
            full_path = os.path.join(self.path, filename)
            matched = self.FIELD_MATCHER.match(filename)
            if matched and os.path.isfile(full_path):
                field_name = matched.group(1)
                if field_name not in constants.FILE_FIELD_BLACKLIST:
                    fields.append(field_name)

        return fields


class GitRevisionJiraFieldManager(
    GitRevisionReader, AutomaticJiraFieldManager
):
    def get_used_per_ticket_fields(self):
        files = self.folder.run_git_command(
            'ls-tree',
            '--name-only',
            self.revision
        ).split()
        fields = []

        for filename in files:
            matched = self.FIELD_MATCHER.match(filename)
            if matched:
                field_name = matched.group(1)
                if field_name not in constants.FILE_FIELD_BLACKLIST:
                    fields.append(field_name)

        return fields
