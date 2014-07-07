import argparse

import six


COMMANDS = {}


def command(desc, name=None):
    def decorator(func):
        func_name = name or func.__name__
        func.description = desc
        COMMANDS[func_name] = func
        return func
    return decorator


@command('Synchronize folder(s) with JIRA')
def sync(args):
    pass


def main():
    parser = argparse.ArgumentParser(
        description='Edit Jira issues locally from your filesystem',
    )
    parser.add_argument(
        'command',
        nargs=1,
        type=six.text_type,
        choices=COMMANDS.keys()
    )
    args, extra = parser.parse_known_args()

    fn = COMMANDS[args.command[0]]
    fn(extra)
