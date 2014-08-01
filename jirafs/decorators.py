from functools import wraps
import inspect


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
