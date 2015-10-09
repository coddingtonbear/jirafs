from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Print a diff of locally-changed files """
    MIN_VERSION = '1.15'
    MAX_VERSION = '1.99.99'

    def main(self, folder, **kwargs):
        result = folder.run_git_command('diff')
        if result:
            result = result.strip()
        print(result)
        return result
