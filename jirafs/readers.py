import io
import os


class GitRevisionReader(object):
    def __init__(self, folder, revision):
        self.folder = folder
        self.revision = revision
        super(GitRevisionReader, self).__init__()

    def get_file_contents(self, path):
        return self.folder.get_local_file_at_revision(
            path,
            self.revision
        )


class WorkingCopyReader(object):
    def __init__(self, folder, path):
        self.folder = folder
        self.path = path
        super(WorkingCopyReader, self).__init__()

    def get_file_contents(self, path):
        full_path = os.path.join(self.path, path)

        with io.open(
            self.folder.get_local_path(full_path),
            'r',
            encoding='utf-8'
        ) as _in:
            return _in.read().strip()
