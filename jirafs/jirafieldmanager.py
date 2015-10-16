import io
import json
import logging
import os
import re

import six

from jirafs import constants, utils
from jirafs.readers import GitRevisionReader, WorkingCopyReader


class JiraFieldManager(dict):
    FIELD_MATCHER = re.compile(
        '^%s$' % (
            constants.TICKET_FILE_FIELD_TEMPLATE.replace(
                '{field_name}', '([\w_]+)'
            )
        )
    )

    def __init__(self, data=None, names=None):
        if names is None:
            self._data, self._names = self.get_fields_from_string(data)
        else:
            self._data = data
            self._names = names
        super(JiraFieldManager, self).__init__(self._data)

    def __sub__(self, other):
        differing = {}
        for k, v in other.items():
            if (self.get(k) or v) and self.get(k) != v:
                tx = self.get(k)
                differing[k] = (v, tx, self.get(k), )

        return differing

    def get_human_name_for_field(self, field):
        try:
            return self._names[field]
        except KeyError:
            return field

    def items_transformed(self):
        for k, v in self.items():
            if k in self.get_requested_per_ticket_fields():
                result = self.folder.process_macros(v)
                yield k, result
            else:
                yield k, v

    def get_transformed(self, field_name, default=None):
        if field_name not in self.get_requested_per_ticket_fields():
            return self[field_name]

        try:
            return self.folder.process_macros(self[field_name])
        except KeyError:
            return default

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

    def get_field_data_files(self):
        all_files = [
            constants.TICKET_DETAILS,
        ]

        used_per_ticket_fields = []
        try:
            for field in self.get_used_per_ticket_fields():
                all_files.append(
                    constants.TICKET_FILE_FIELD_TEMPLATE.format(
                        field_name=field,
                    )
                )
        except NotImplementedError:
            pass

        for field in self.get_requested_per_ticket_fields():
            all_files.append(
                constants.TICKET_FILE_FIELD_TEMPLATE.format(
                    field_name=field,
                )
            )

        return all_files

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
        human_names = {}
        value = ''
        if not string:
            return data, human_names
        lines = string.split('\n')
        for idx, line in enumerate(lines):
            if line.startswith('*'):
                if value:  # If so, we just need to store previous loop data
                    self.set_data_value(data, field_name, value)
                    value = ''
                raw_field_name = re.match('^\* (.*\(.*?\)):$', line).group(1)
                if '(' in raw_field_name:
                    # This field name's real name doesn't match the field ID
                    match = re.match(
                        '(.*) \(([^)]+)\)',
                        raw_field_name
                    )
                    field_name = match.group(2)
                    human_names[field_name] = match.group(1)
                else:
                    field_name = raw_field_name.replace(' ', '_')
            elif field_name:
                value = value + '\n' + line.strip()
        if value:
            self.set_data_value(data, field_name, value)

        return data, human_names


class AutomaticJiraFieldManager(JiraFieldManager):
    def __init__(self):
        data, names = self.load()
        super(AutomaticJiraFieldManager, self).__init__(
            data, names=names
        )

    def load(self):
        fields, names = self.get_fields_from_string(
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
        return fields, names

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

    def write(self):
        folder_path = self.folder.get_path(constants.TICKET_DETAILS)

        used_fields = set(self.get_used_per_ticket_fields())
        requested_fields = set(self.get_requested_per_ticket_fields())

        with io.open(folder_path, 'w', encoding='utf-8') as out:
            for field in sorted(self.keys()):
                if field not in used_fields | requested_fields:
                    out.write(
                        u'* {human} ({field}):\n'.format(
                            human=self.get_human_name_for_field(field),
                            field=field,
                        )
                    )

                    field_string = self[field]
                    if field_string is None:
                        field_string = ''
                    elif not isinstance(field_string, six.string_types):
                        field_string = json.dumps(
                            field_string,
                            sort_keys=True,
                            indent=4,
                            ensure_ascii=False,
                        )

                    # Each line is preceded by 4 spaces of whitespace
                    padded_lines = [
                        u'    %s\n' % f for f in field_string.split('\n')
                    ]
                    for line in padded_lines:
                        out.write(line)
                else:
                    field_path = constants.TICKET_FILE_FIELD_TEMPLATE.format(
                        field_name=field
                    )
                    with io.open(field_path, 'w', encoding='utf-8') as fout:
                        fout.write(self[field])
                        fout.write(u'\n')


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
