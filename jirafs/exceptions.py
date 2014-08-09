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
        inner_exception = kwargs.pop('inner_exception', None)
        command = kwargs.pop('cmd', None)
        self._inner_exception = inner_exception
        self._command = command

        super(GitCommandError, self).__init__(*args, **kwargs)

    @property
    def command(self):
        return self._command

    @property
    def returncode(self):
        return self._inner_exception.returncode

    @property
    def output(self):
        return self._inner_exception.output
