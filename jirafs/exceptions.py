class JirafsError(Exception):
    pass


class NotTicketFolderException(JirafsError):
    pass


class LocalCopyOutOfDate(JirafsError):
    pass


class JiraInteractionFailed(JirafsError):
    pass


class GitCommandError(JirafsError):
    def __init__(self, *args, **kwargs):
        self._command = kwargs.pop('cmd', None)
        self._returncode = kwargs.pop('returncode', None)
        self._output = kwargs.pop('stdout', None)

        super(GitCommandError, self).__init__(*args, **kwargs)

    @property
    def command(self):
        return self._command

    @property
    def returncode(self):
        return self._returncode

    @property
    def output(self):
        return self._output


class IssueValidationError(JirafsError):
    pass
