from jirafs.plugin import CommandPlugin, CommandResult


class Command(CommandPlugin):
    """ Commit local changes for later submission to JIRA """
    MIN_VERSION = '1.16'
    MAX_VERSION = '1.99.99'

    def main(self, args, folder, **kwargs):
        return folder.process_plugin_builds()

    def cmd(self, *args, **kwargs):
        data = self.main(*args, **kwargs)

        result = CommandResult()
        for key, value in data.items():
            result = result.add_line(
                'Ran build plugin {plugin}',
                plugin=key,
            )
            if not value:
                continue

            if not isinstance(value, basestring):
                value = json.dumps(
                    value,
                    indent=4,
                    sort_keys=True,
                )

            for line in value.split('\n'):
                if not line.strip():
                    continue

                result = result.add_line(
                    '\t{line}',
                    line=line,
                )

        return result

