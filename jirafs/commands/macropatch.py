import io

from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Merge remote changes into your local copy """
    RUN_FOR_SUBTASKS = True
    TRY_SUBFOLDERS = True
    MIN_VERSION = '1.15'
    MAX_VERSION = '1.99.99'

    def handle(self, args, folder, **kwargs):
        return self.cmd(folder, args)

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            default='get',
            choices=[
                'get',
                'reset',
            ]
        )

    def main(self, folder, args):
        path = folder.get_metadata_path('macros_applied.patch')
        if args.action == 'reset':
            with io.open(path, 'w', encoding='utf-8') as out:
                out.write(u'\n\n')

            print(
                "Macro patch successfully reset. Be sure to run "
                "`jirafs commit` or `jirafs submit` for these changes "
                "to take effect."
            )
        elif args.action == 'get':
            with io.open(path, 'r', encoding='utf-8') as in_:
                print(in_.read())
