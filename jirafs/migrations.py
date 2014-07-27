import json
import os
import shutil
import subprocess


def set_repo_version(repo, version):
    with open(repo.get_metadata_path('version'), 'w') as out:
        out.write(str(version))
    repo.run_git_command(
        'add', '-f', repo.get_metadata_path('version'), failure_ok=True,
    )
    repo.run_git_command(
        'commit', '-m', 'Upgraded Repository to v%s' % version, failure_ok=True
    )


def migration_0002(repo, **kwargs):
    """ Creates shadow repository used for storing remote values """
    os.mkdir(
        repo.get_metadata_path('shadow')
    )
    subprocess.check_call(
        (
            'git',
            'clone',
            '--shared',
            '-q',
            '../git',
            '.'
        ),
        cwd=repo.get_metadata_path('shadow'),
        stdout=subprocess.PIPE,
    )
    repo.run_git_command('checkout', '-b', 'jira', shadow=True)
    repo.run_git_command(
            'commit', '--allow-empty', '-m', 'Shadow Created', shadow=True
    )
    repo.run_git_command('push', 'origin', 'jira', shadow=True)
    set_repo_version(repo, 2)


def migration_0003(repo, init=False, **kwargs):
    """ Creates a shadow copy of the issue.

    .. note::

       Early versions of this migration improperly created the shadow
       copy using an absolute path.

    """
    try:
        os.mkdir(repo.get_shadow_path('.jirafs'))
    except OSError:
        pass
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


def migration_0004(repo, **kwargs):
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


def migration_0005(repo, init=False, **kwargs):
    """ Dummy migration for RST->Jira format change.

    Note: TicketFolders older than version 5 cannot be upgraded past
    version 5; although I had written a migration for this originally,
    there were a few hard-to-work-around bugs that I decided were
    not quite important enough.

    """
    if init:
        set_repo_version(repo, 5)
        return

    repo_path = repo.path
    temp_path = os.path.normpath(
        os.path.join(
            repo_path,
            '../',
            repo.path.split('/')[-1] + '.tmp'
        )
    )

    repo.clone(
        repo.issue_url,
        repo.get_jira,
        temp_path,
    )
    temp_dir = os.listdir(temp_path)
    for filename in os.listdir(repo_path):
        if filename not in temp_dir and not filename.endswith('.jira.rst'):
            shutil.copyfile(
                os.path.join(repo_path, filename),
                os.path.join(temp_path, filename),
            )

    shutil.rmtree(repo_path)
    os.rename(temp_path, repo_path)

    set_repo_version(repo, 5)


def migration_0006(repo, init=False, **kwargs):
    """ Fix a glitch preventing folders from being completely portable.

    Early versions of Jirafs would write an absolute path to the ignore
    file to the local git configuration, but that's not very desirable
    because if you move the folder, the @stash_local_changes decorator
    would then wipe out the git repository itself (among other things)
    after stashing.  Whoops; that's embarrassing.

    """
    if init:
        set_repo_version(repo, 6)
        return

    repo.run_git_command(
        'config',
        '--file=%s' % repo.get_metadata_path(
            'git',
            'config',
        ),
        'core.excludesfile',
        '.jirafs/gitignore',
    )

    set_repo_version(repo, 6)


def migration_0007(repo, init=False, **kwargs):
    """ Create the plugin metadata directory."""
    try:
        os.mkdir(
            repo.get_metadata_path(
                'plugin_meta',
            )
        )
    except OSError:
        pass
    set_repo_version(repo, 7)


def migration_0008(repo, init=False, **kwargs):
    """ Commit most of .jirafs folder to git so we can back up. """
    if init:
        set_repo_version(repo, 8)
        return

    with open(repo.get_metadata_path('gitignore'), 'w') as out:
        out.write(
            '\n'.join(
                [
                    '.jirafs/git',
                    '.jirafs/shadow',
                    '.jirafs/operation.log'
                ]
            )
        )
    repo.run_git_command(
        'add',
        '.jirafs/gitignore',
    )
    repo.run_git_command(
        'commit',
        '-m',
        'Updating gitignore',
    )

    files_to_add = [
        'config',
        'gitignore',
        'issue_url',
        'plugin_meta',
        'version',
    ]
    for filename in files_to_add:
        repo.run_git_command(
            'add',
            repo.get_metadata_path(filename),
            failure_ok=True
        )

    set_repo_version(repo, 8)


def migration_0009(repo, init=False, **kwargs):
    """ Re-clone shadow copy so it does not reference an absolute path."""
    if init:
        set_repo_version(repo, 9)

    shutil.rmtree(repo.get_metadata_path('shadow'))
    os.mkdir(
        repo.get_metadata_path('shadow')
    )
    subprocess.check_call(
        (
            'git',
            'clone',
            '--shared',
            '-q',
            '../git',
            '.'
        ),
        cwd=repo.get_metadata_path('shadow'),
        stdout=subprocess.PIPE,
    )
    repo.run_git_command('checkout', '-b', 'jira', shadow=True)
    repo.run_git_command(
        'commit', '--allow-empty', '-m', 'Shadow Created', shadow=True
    )
    repo.run_git_command('push', 'origin', 'jira', shadow=True)

    set_repo_version(repo, 9)
