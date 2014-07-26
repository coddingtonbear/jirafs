class NotTicketFolderException(Exception):
    pass


class CannotInferTicketNumberFromFolderName(Exception):
    pass


class LocalCopyOutOfDate(Exception):
    pass


class GitCommandError(Exception):
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
