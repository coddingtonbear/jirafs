from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Print a diff of locally-changed files """

    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"

    def main(self, folder, **kwargs):
        result = folder.run_git_command("diff")
        if result:
            result = result.strip()
        print(result)
        return result
