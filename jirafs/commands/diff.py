from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Print a diff of locally-changed files """
    MIN_VERSION = '1.0a1'
    MAX_VERSION = '1.99.99'

    def handle(self, folder, **kwargs):
        return self.diff(folder)

    def diff(self, folder):
        result = folder.run_git_command('diff')
        if result:
            result = result.strip()
        print(result)
        return result
