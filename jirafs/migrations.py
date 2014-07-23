import json
import os
import re
import subprocess

from . import constants


def set_repo_version(repo, version):
    with open(repo.get_metadata_path('version'), 'w') as out:
        out.write(str(version))


def migration_0002(repo):
    """ Creates shadow repository used for storing remote values """
    subprocess.check_call(
        (
            'git',
            'clone',
            '--shared',
            '-q',
            repo.get_metadata_path('git'),
            os.path.join(
                repo.get_metadata_path('shadow')
            )
        ),
        stdout=subprocess.PIPE,
    )
    repo.run_git_command('checkout', '-b', 'jira', shadow=True)
    repo.run_git_command('commit', '--allow-empty', '-m', 'Shadow Created')
    repo.run_git_command('push', 'origin', 'jira', shadow=True)
    set_repo_version(repo, 2)


def migration_0003(repo):
    """ Creates a shadow copy of the issue. """
    os.mkdir(repo.get_shadow_path('.jirafs'))
    storable = {
        'options': repo.issue._options,
        'raw': repo.issue.raw
    }
    with open(repo.get_shadow_path('.jirafs/issue.json'), 'w') as out:
        out.write(json.dumps(storable))
    issue_pickle_path = repo.get_shadow_path('.jirafs/issue.json')
    repo.run_git_command('add', '-f', issue_pickle_path, shadow=True)
    repo.run_git_command(
        'commit', '-m', 'Completing migration_0003', shadow=True
    )
    repo.run_git_command('push', 'origin', 'jira', shadow=True)
    repo.run_git_command('merge', 'jira')
    set_repo_version(repo, 3)


def migration_0004(repo):
    """ Moves remote_files.json into version control. """
    local_remote_files_path = repo.get_metadata_path('remote_files.json')
    jira_remote_files_path = repo.get_shadow_path('.jirafs/remote_files.json')
    try:
        os.rename(local_remote_files_path, jira_remote_files_path)
    except (IOError, OSError):
        with open(jira_remote_files_path, 'w') as out:
            out.write('{}')

    repo.run_git_command('add', '-f', jira_remote_files_path, shadow=True)
    repo.run_git_command(
        'commit', '-m', 'Completing migration_0004', shadow=True
    )
    repo.run_git_command('push', 'origin', 'jira', shadow=True)
    repo.run_git_command('merge', 'jira')
    set_repo_version(repo, 4)


def migration_0005(repo):
    """ Migrates existing .rst files into .jira files. """

    def get_fields_from_rst_string(string):
        """ Gets field data from an incoming string.

        Parses through the string using the following RST-derived
        pattern::

            0 | FIELD_NAME::
            1 |
            2 |     VALUE

        """
        FIELD_DECLARED = 0
        PREAMBLE = 1
        VALUE = 2

        state = None

        data = {}
        field_name = ''
        value = ''
        if not string:
            return data
        lines = string.split('\n')
        for idx, line in enumerate(lines):
            line = line.replace('\t', '    ')
            if state == FIELD_DECLARED and not line:
                state = PREAMBLE
            elif (
                (state == VALUE or state is None)
                and re.match('^(\w+)::', line)
            ):
                if value:
                    data[field_name] = value.strip()
                    value = ''
                state = FIELD_DECLARED
                field_name = re.match('^(\w+)::', line).group(1)
                if not field_name:
                    raise ValueError(
                        "Syntax error on line %s" % idx
                    )
            elif (state == PREAMBLE or state == VALUE):
                state = VALUE
                value = value + '\n' + line[4:]  # Remove first indentation
        if value:
            data[field_name] = value.strip()

        return data

    for shadow in [False, True]:
        if os.path.isfile(repo.get_path('fields.jira.rst', shadow=shadow)):
            with open(repo.get_path('fields.jira.rst', shadow=shadow)) as _in:
                data = get_fields_from_rst_string(_in.read())
            with open(repo.get_path(constants.TICKET_DETAILS, shadow=shadow), 'w') as out:
                for k, v in data.items():
                    out.write('* %s:\n' % k)
                    for line in v.replace('\r\n', '\n').split('\n'):
                        out.write('    %s\n' % line)

            repo.run_git_command('rm', 'fields.jira.rst', shadow=shadow)
            repo.run_git_command(
                'add', constants.TICKET_DETAILS, shadow=shadow
            )

            for filename in os.listdir(repo.get_path('', shadow=shadow)):
                if not filename.endswith('.jira.rst'):
                    continue
                new_filename = filename[0:len(filename)-4]
                os.rename(
                    repo.get_path(filename, shadow=shadow),
                    repo.get_path(new_filename, shadow=shadow)
                )
                repo.run_git_command('rm', '-f', filename, shadow=shadow)
                repo.run_git_command('add', new_filename, shadow=shadow)

            repo.run_git_command(
                'commit', '-m', 'Completing migration_0005', shadow=shadow
            )
            if shadow:
                repo.run_git_command('push', 'origin', 'jira', shadow=True)

    repo.merge()

    set_repo_version(repo, 5)
