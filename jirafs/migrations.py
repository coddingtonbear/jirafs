import json
import os
import subprocess


def set_repo_version(repo, version):
    with open(repo.get_metadata_path('version'), 'w') as out:
        out.write(str(version))


def migration_0002(repo):
    """ Creates shadow repository used for storing remote values """
    subprocess.check_call((
        'git',
        'clone',
        '--shared',
        repo.get_metadata_path('git'),
        os.path.join(
            repo.get_metadata_path('shadow')
        )
    ))
    repo.run_git_command('checkout', '-b', 'jira', shadow=True)
    repo.run_git_command('push', 'origin', 'jira', shadow=True)
    set_repo_version(repo, 2)


def migration_0003(repo):
    """ Creates a shadow copy of the issue. """
    os.mkdir(repo.get_shadow_path('.jirafs'))
    issue_json = repo.get_shadow_path('.jirafs/issue.json')
    with open(issue_json, 'w') as out:
        out.write(json.dumps(repo.issue.raw))
    repo.run_git_command('add', '-f', issue_json, shadow=True)
    repo.run_git_command(
        'commit', '-m', 'Completing migration_0003', shadow=True
    )
    repo.run_git_command('push', 'origin', 'jira', shadow=True)
    repo.run_git_command('merge', 'jira')
    set_repo_version(repo, 3)
