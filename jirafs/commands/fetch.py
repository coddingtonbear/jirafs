import io
import json
import textwrap

import six

from jirafs import constants, utils
from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Fetch remote changes """
    TRY_SUBFOLDERS = True
    MIN_VERSION = '1.0a1'
    MAX_VERSION = '1.99.99'

    def handle(self, folder, **kwargs):
        return self.fetch(folder)

    def get_field_map(self, folder):
        fields = {}
        for field in folder.jira.fields():
            fields[field['id']] = field['name']

        return fields

    def fetch(self, folder):
        folder.clear_cache()

        file_meta = folder.get_remote_file_metadata(shadow=True)
        original_hash = folder.run_git_command('rev-parse', 'jira')

        for filename in folder.get_remotely_changed():
            for attachment in folder.issue.fields.attachment:
                if attachment.filename == filename:
                    folder.log(
                        'Download file "%s"',
                        (attachment.filename, ),
                    )
                    content = six.BytesIO(attachment.get())
                    filename, content = folder.execute_plugin_method_series(
                        'alter_file_download',
                        args=((filename, content, ),),
                        single_response=True,
                    )
                    save_path = folder.get_shadow_path(filename)
                    with open(save_path, 'wb') as save_file:
                        content.seek(0)
                        save_file.write(content.read())
                        file_meta[filename] = attachment.created

        folder.set_remote_file_metadata(file_meta, shadow=True)

        field_map = self.get_field_map(folder)
        detail_path = folder.get_shadow_path(constants.TICKET_DETAILS)
        with io.open(detail_path, 'w', encoding='utf-8') as dets:
            for field in sorted(folder.issue.raw['fields'].keys()):
                value = folder.issue.raw['fields'][field]
                if isinstance(value, six.string_types):
                    value = value.replace('\r\n', '\n').strip()
                elif value is None:
                    value = ''
                elif field in constants.NO_DETAIL_FIELDS:
                    continue

                if not isinstance(value, six.string_types):
                    value = json.dumps(
                        value,
                        sort_keys=True,
                        indent=4,
                        ensure_ascii=False
                    )

                if field in constants.FILE_FIELDS:
                    # Write specific fields to their own files without
                    # significant alteration

                    file_field_path = folder.get_shadow_path(
                        constants.TICKET_FILE_FIELD_TEMPLATE
                    ).format(field_name=field)
                    with io.open(
                        file_field_path,
                        'w',
                        encoding='utf-8'
                    ) as file_field_file:
                        file_field_file.write(six.text_type(value))
                        file_field_file.write(
                            six.text_type('\n')
                        )  # For unix' sake
                else:
                    # Normal fields, though, just go into the standard
                    # fields file.
                    if value is None:
                        continue
                    elif field in constants.NO_DETAIL_FIELDS:
                        continue

                    human_readable = field_map.get(field)
                    if human_readable is None or human_readable == field:
                        dets.write(
                            six.text_type('* %s:\n') % (
                                field
                            )
                        )
                    else:
                        dets.write(
                            six.text_type('* %s (%s):\n') % (
                                human_readable,
                                field
                            )
                        )
                    for line in value.replace('\r\n', '\n').split('\n'):
                        dets.write(six.text_type('    %s\n' % line))

        comments_filename = folder.get_shadow_path(constants.TICKET_COMMENTS)
        with io.open(comments_filename, 'w', encoding='utf-8') as comm:
            for comment in folder.issue.fields.comment.comments:
                comm.write(
                    six.text_type('* At %s, %s wrote:\n\n') % (
                        comment.created,
                        comment.author
                    )
                )
                final_lines = []
                lines = comment.body.replace('\r\n', '\n').split('\n')
                for line in lines:
                    if not line:
                        final_lines.append(six.text_type(''))
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
                    comm.write(six.text_type('    %s\n') % line)
                comm.write(six.text_type('\n'))

        folder.store_cached_issue()

        folder.run_git_command('add', '-A', shadow=True)
        folder.run_git_command(
            'commit', '-m', 'Fetched remote changes',
            failure_ok=True, shadow=True
        )
        folder.run_git_command('push', 'origin', 'jira', shadow=True)
        final_hash = folder.run_git_command('rev-parse', 'jira')
        if original_hash != final_hash:
            folder.log(
                "Updated 'jira' to %s" % final_hash
            )
        return utils.PostStatusResponse(
            original_hash == final_hash,
            final_hash
        )
