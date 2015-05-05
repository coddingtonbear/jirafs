import json

from blessings import Terminal

from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Get the status of the current ticketfolder """
    TRY_SUBFOLDERS = True
    MIN_VERSION = '1.0a1'
    MAX_VERSION = '1.99.99'

    def handle(self, args, folder, **kwargs):
        return self.status(folder, args.format)

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            default='text',
            choices=['text', 'json']
        )

    def status(self, folder, output_format='text'):
        status = folder.status()
        if output_format == 'json':
            self.status_json(folder, status)
        self.status_text(folder, status)
        return status

    def status_json(self, folder, status):
        print(json.dumps(status))

    def has_changes(self, section, *keys):
        if not keys:
            keys = ['files', 'fields', 'new_comment', 'links']
        for key in keys:
            if section[key]:
                return True

    def status_text(self, folder, folder_status):
        t = Terminal()
        print(
            u"On ticket {ticket} ({url})".format(
                ticket=folder.ticket_number,
                url=folder.cached_issue.permalink(),
            )
        )
        if not folder_status['up_to_date']:
            print(
                t.magenta + "Warning: unmerged upstream changes exist; "
                "run `jirafs merge` to merge them into your local copy." +
                t.normal
            )

        printed_changes = False
        ready = folder_status['ready']
        if self.has_changes(ready):
            printed_changes = True
            print('')
            print(
                "Ready for upload; use `jirafs push` to update JIRA."
            )
            print(
                self.format_field_changes(ready, 'green', terminal=t)
            )

        staged = folder_status['uncommitted']
        if self.has_changes(staged):
            printed_changes = True
            print('')
            print(
                "Uncommitted changes; use `jirafs commit` to mark these "
                "for JIRA."
            )
            print(
                self.format_field_changes(staged, 'red', terminal=t)
            )

        local_uncommitted = folder_status['local_uncommitted']
        if self.has_changes(local_uncommitted, 'files'):
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
                self.format_field_changes(
                    local_uncommitted,
                    'cyan',
                    no_upload=True,
                    terminal=t,
                )
            )

        if not printed_changes:
            print('No changes found')
        else:
            print('')

    def format_field_changes(
        self, changes, color, no_upload=False, terminal=None
    ):
        if terminal is None:
            t = Terminal()
        else:
            t = terminal
        lines = []
        color = getattr(t, color)
        normal = t.normal

        for filename in changes.get('files', []):
            lines.append(
                '\t' + color + filename + normal + (
                    ' (save to repository)' if no_upload else ' (file upload)'
                )
            )
        for link, data in changes.get('links', {}).get('remote', {}).items():
            orig = data[0]
            new = data[1]
            if new is not None:
                if new.get('description'):
                    description = new['description']
                else:
                    description = '(Untitled)'
                lines.append(
                    '\t' + color + description +
                    ': ' + link + normal + (
                        ' (changed remote link)'
                        if orig else ' (new remote link)'
                    )
                )
            else:
                if orig.get('description'):
                    description = orig['description']
                else:
                    description = '(Untitled)'
                lines.append(
                    '\t' + color + description +
                    ': ' + link + normal + ' (removed remote link)'
                )
        for link, data in changes.get('links', {}).get('issue', {}).items():
            orig = data[0]
            new = data[1]
            if new is not None:
                if new.get('status'):
                    status = new['status']
                else:
                    status = '(Untitled)'
                lines.append(
                    '\t' + color + status.title() +
                    ': ' + link + normal + (
                        ' (changed issue link)'
                        if orig else ' (new issue link)'
                    )
                )
            else:
                if orig.get('status'):
                    status = orig['status']
                else:
                    status = '(Untitled)'
                lines.append(
                    '\t' + color + status.title() +
                    ': ' + link + normal + ' (removed issue link)'
                )
        for field, value_set in changes.get('fields', {}).items():
            lines.append(
                '\t' + color + field + normal
            )
        if changes.get('new_comment', ''):
            lines.append(
                '\t' + color + '[New Comment]' + normal
            )

        return '\n'.join(lines)
