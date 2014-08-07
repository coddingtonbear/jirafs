import six

from jirafs import constants, exceptions, utils
from jirafs.plugin import CommandPlugin
from jirafs.utils import run_command_method_with_kwargs


class Command(CommandPlugin):
    """ Push locally-committed changes to JIRA """
    TRY_SUBFOLDERS = True
    MIN_VERSION = '1.0a1'
    MAX_VERSION = '1.99.99'

    def handle(self, folder, **kwargs):
        return self.push(folder)

    def push(self, folder):
        with utils.stash_local_changes(folder):
            status = folder.status()

            if not folder.is_up_to_date():
                raise exceptions.LocalCopyOutOfDate()

            file_meta = folder.get_remote_file_metadata(shadow=False)

            for filename in status['ready']['files']:
                upload = six.BytesIO(
                    folder.get_local_file_at_revision(
                        filename,
                        'HEAD',
                        binary=True
                    )
                )
                filename, upload = folder.execute_plugin_method_series(
                    'alter_file_upload',
                    args=((filename, upload, ), ),
                    single_response=True,
                )
                folder.log(
                    'Uploading file "%s"',
                    (filename, ),
                )
                # Delete the existing issue if there is one
                for attachment in folder.issue.fields.attachment:
                    if attachment.filename == filename:
                        attachment.delete()
                upload.seek(0)
                attachment = folder.jira.add_attachment(
                    folder.ticket_number,
                    upload,
                    filename=filename,
                )
                file_meta[filename] = attachment.created

            folder.set_remote_file_metadata(file_meta, shadow=False)

            comment = folder.get_new_comment(clear=True, ready=True)
            if comment:
                folder.log(
                    'Adding comment "%s..."' % comment[0:30].replace('%', '%%')
                )
                folder.jira.add_comment(folder.ticket_number, comment)

            collected_updates = {}
            for field, diff_values in status['ready']['fields'].items():
                collected_updates[field] = diff_values[1]

            if collected_updates:
                folder.log(
                    'Updating fields "%s"',
                    (collected_updates, )
                )
                folder.issue.update(**collected_updates)

            # Commit local copy
            folder.run_git_command('reset', '--soft', failure_ok=True)
            folder.run_git_command(
                'add', '.jirafs/remote_files.json', failure_ok=True
            )
            folder.run_git_command(
                'add', constants.TICKET_NEW_COMMENT, failure_ok=True
            )
            folder.run_git_command(
                'commit', '-m', 'Pushed local changes', failure_ok=True
            )

            # Commit changes to remote copy, too, so we record remote
            # file metadata.
            folder.run_git_command('fetch', shadow=True)
            folder.run_git_command('merge', 'origin/master', shadow=True)
            folder.run_git_command('add', '-A', shadow=True)
            folder.run_git_command(
                'commit', '-m', 'Pulled remote changes',
                failure_ok=True, shadow=True
            )
            folder.run_git_command('push', 'origin', 'jira', shadow=True)
            pull_result = run_command_method_with_kwargs('pull', folder=folder)
            return pull_result[1]
