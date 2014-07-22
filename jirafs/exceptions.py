class NotTicketFolderException(Exception):
    pass


class CannotInferTicketNumberFromFolderName(Exception):
    pass


class LocalCopyOutOfDate(Exception):
    pass


class GitCommandError(Exception):
    def __init__(self, *args, **kwargs):
        inner_exception = kwargs.pop('inner_exception', None)
        self._inner_exception = inner_exception

        super(GitCommandError, self).__init__(*args, **kwargs)
