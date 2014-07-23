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
    """ Dummy migration for RST->Jira format change.

    Note: TicketFolders older than version 5 cannot be upgraded past
    version 5; although I had written a migration for this originally,
    there were a few hard-to-work-around bugs that I decided were
    not quite important enough.

    """
    set_repo_version(repo, 5)
