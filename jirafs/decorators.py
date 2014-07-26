from functools import wraps
import inspect


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


def run_plugins(pre=None, post=None):
    def wrapper(cmd):
        @wraps(cmd)
        def wrapped(*args, **kwargs):
            # Convert args into kwargs
            self = args[0]
            kwargs = inspect.getcallargs(cmd, *args, **kwargs)

            if pre:
                kwargs = self.execute_plugin_method_series(
                    pre,
                    kwargs=kwargs
                )
            results = cmd(**kwargs)
            if post:
                results = self.execute_plugin_method_series(
                    post,
                    args=(results,),
                    single_response=True,
                )
            return results
        return wrapped
    return wrapper
