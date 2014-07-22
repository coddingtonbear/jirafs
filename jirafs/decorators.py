from functools import wraps


def stash_local_changes(cmd):
    @wraps(cmd)
    def wrapped(self, *args, **kwargs):
        self.run_git_command(
            'stash', '--include-untracked', failure_ok=True,
        )
        cmd(self, *args, **kwargs)
        self.run_git_command(
            'stash', 'apply', failure_ok=True,
        )
        self.run_git_command(
            'stash', 'drop', failure_ok=True,
        )
    return wrapped
