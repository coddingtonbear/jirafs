import json
import os
import shutil
import subprocess
from urllib import parse

from . import utils
from .exceptions import GitCommandError


def set_repo_version(repo, version):
    with open(repo.get_metadata_path("version"), "w") as out:
        out.write(str(version))
    repo.run_git_command(
        "add", "-f", repo.get_metadata_path("version"), failure_ok=True,
    )
    repo.run_git_command(
        "commit", "-m", "Upgraded Repository to v%s" % version, failure_ok=True
    )


def migration_0002(repo, **kwargs):
    """ Creates shadow repository used for storing remote values """
    os.mkdir(repo.get_metadata_path("shadow"))
    subprocess.check_call(
        ("git", "clone", "-q", "../git", "."),
        cwd=repo.get_metadata_path("shadow"),
        stdout=subprocess.PIPE,
    )
    try:
        repo.run_git_command("checkout", "-b", "jira", shadow=True)
    except GitCommandError:
        repo.run_git_command("checkout", "jira", shadow=True)
    repo.run_git_command("commit", "--allow-empty", "-m", "Shadow Created", shadow=True)
    repo.run_git_command("push", "origin", "jira", shadow=True)
    set_repo_version(repo, 2)


def migration_0003(repo, init=False, **kwargs):
    """ Creates a shadow copy of the issue.

    .. note::

       Early versions of this migration improperly created the shadow
       copy using an absolute path.

    """
    try:
        os.mkdir(repo.get_shadow_path(".jirafs"))
    except OSError:
        pass
    storable = {"options": repo.issue._options, "raw": repo.issue.raw}
    with open(repo.get_shadow_path(".jirafs/issue.json"), "w") as out:
        out.write(json.dumps(storable))
    issue_pickle_path = repo.get_shadow_path(".jirafs/issue.json")
    repo.run_git_command("add", "-f", issue_pickle_path, shadow=True)
    repo.run_git_command("commit", "-m", "Completing migration_0003", shadow=True)
    repo.run_git_command("push", "origin", "jira", shadow=True)
    repo.run_git_command("merge", "jira")
    set_repo_version(repo, 3)


def migration_0004(repo, **kwargs):
    """ Moves remote_files.json into version control. """
    local_remote_files_path = repo.get_metadata_path("remote_files.json")
    jira_remote_files_path = repo.get_shadow_path(".jirafs/remote_files.json")
    try:
        os.rename(local_remote_files_path, jira_remote_files_path)
    except (IOError, OSError):
        with open(jira_remote_files_path, "w") as out:
            out.write("{}")

    repo.run_git_command("add", "-f", jira_remote_files_path, shadow=True)
    repo.run_git_command("commit", "-m", "Completing migration_0004", shadow=True)
    repo.run_git_command("push", "origin", "jira", shadow=True)
    repo.run_git_command("merge", "jira")
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
        os.path.join(repo_path, "../", repo.path.split("/")[-1] + ".tmp")
    )

    repo.clone(
        repo.issue_url, repo.get_jira, temp_path,
    )
    temp_dir = os.listdir(temp_path)
    for filename in os.listdir(repo_path):
        if filename not in temp_dir and not filename.endswith(".jira.rst"):
            shutil.copyfile(
                os.path.join(repo_path, filename), os.path.join(temp_path, filename),
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
        "config",
        "--file=%s" % repo.get_metadata_path("git", "config",),
        "core.excludesfile",
        ".jirafs/gitignore",
    )

    set_repo_version(repo, 6)


def migration_0007(repo, init=False, **kwargs):
    """ Create the plugin metadata directory."""
    try:
        os.mkdir(repo.get_metadata_path("plugin_meta",))
    except OSError:
        pass
    with open(repo.get_metadata_path("plugin_meta", ".empty"), "w") as out:
        out.write("")
    repo.run_git_command("add", "-f", repo.get_metadata_path("plugin_meta", ".empty",))
    repo.run_git_command("commit", "-m", "Completing migration_0007", failure_ok=True)
    set_repo_version(repo, 7)


def migration_0008(repo, init=False, **kwargs):
    """ Commit most of .jirafs folder to git so we can back up. """
    if init:
        set_repo_version(repo, 8)
        return

    with open(repo.get_metadata_path("gitignore"), "w") as out:
        out.write("\n".join([".jirafs/git", ".jirafs/shadow", ".jirafs/operation.log"]))
    repo.run_git_command(
        "add", ".jirafs/gitignore",
    )
    repo.run_git_command("commit", "-m", "Updating gitignore", failure_ok=True)

    files_to_add = [
        "config",
        "gitignore",
        "issue_url",
        "plugin_meta",
        "version",
    ]
    for filename in files_to_add:
        repo.run_git_command("add", repo.get_metadata_path(filename), failure_ok=True)

    set_repo_version(repo, 8)


def migration_0009(repo, init=False, **kwargs):
    """ Re-clone shadow copy so it does not reference an absolute path."""
    if init:
        set_repo_version(repo, 9)

    shutil.rmtree(repo.get_metadata_path("shadow"))
    os.mkdir(repo.get_metadata_path("shadow"))
    subprocess.check_call(
        ("git", "clone", "-q", "../git", "."),
        cwd=repo.get_metadata_path("shadow"),
        stdout=subprocess.PIPE,
    )
    try:
        repo.run_git_command("checkout", "-b", "jira", shadow=True)
    except GitCommandError:
        repo.run_git_command("checkout", "jira", shadow=True)
    repo.run_git_command("commit", "--allow-empty", "-m", "Shadow Created", shadow=True)
    repo.run_git_command("push", "origin", "jira", shadow=True)

    set_repo_version(repo, 9)


def migration_0010(repo, init=False, **kwargs):
    """ Make sure that the operation.log and plugin_meta are untracked/tracked.

    * ``operation.log`` *cannot* be tracked, since if we make a change,
      followed by a stash pop, operation.log may have encountered changes
      since then.
    * ``plugin_meta`` *must* be tracked, or when we pop stash, 

    """
    if init:
        set_repo_version(repo, 10)
        return

    with open(repo.get_metadata_path("gitignore"), "w") as out:
        out.write("\n".join([".jirafs/git", ".jirafs/shadow", ".jirafs/operation.log"]))
    repo.run_git_command(
        "add", "-f", ".jirafs/gitignore",
    )
    try:
        os.mkdir(repo.get_metadata_path("plugin_meta",))
    except OSError:
        # Already exists
        pass
    with open(repo.get_metadata_path("plugin_meta", ".empty"), "w") as out:
        out.write("")
    repo.run_git_command("add", "-f", repo.get_metadata_path("plugin_meta", ".empty"))
    repo.run_git_command(
        "rm", "-f", "--cached", ".jirafs/operation.log", failure_ok=True,
    )
    repo.run_git_command("commit", "-m", "Completing migration_0010", failure_ok=True)
    set_repo_version(repo, 10)


def migration_0011(repo, init=False, **kwargs):
    """ Re-clone shadow copy so it does not reference an absolute path.

    .. note::

       The amount of stumbling I've engaged in in managing this shadow
       copy has been terribly embarassing.  Who knew it was so complicated.

       The TLDR is that you *cannot* use `shared` if you ever want the folder
       to be portable, since it'll write an absolute path to the repository
       in your `.jirafs/shadow/.git/objects/info/alternates` file.

    """
    if init:
        set_repo_version(repo, 11)
        return

    shutil.rmtree(repo.get_metadata_path("shadow"))
    os.mkdir(repo.get_metadata_path("shadow"))
    subprocess.check_call(
        ("git", "clone", "-q", "../git", "."),
        cwd=repo.get_metadata_path("shadow"),
        stdout=subprocess.PIPE,
    )
    try:
        repo.run_git_command("checkout", "-b", "jira", shadow=True)
    except GitCommandError:
        repo.run_git_command("checkout", "jira", shadow=True)
    repo.run_git_command("commit", "--allow-empty", "-m", "Shadow Created", shadow=True)
    repo.run_git_command("push", "-f", "origin", "jira", shadow=True)
    repo.run_git_command("merge", "jira")

    set_repo_version(repo, 11)


def migration_0012(repo, init=False, **kwargs):
    """ Force the shadow repository to use a relative URL."""
    subprocess.check_call(
        ("git", "remote", "set-url", "origin", "../git"),
        cwd=repo.get_metadata_path("shadow"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    set_repo_version(repo, 12)


def migration_0013(repo, init=False, **kwargs):
    """ Ensure that folder URL is written to issue_url file."""
    if init:
        set_repo_version(repo, 13)
        return

    result = repo.get_ticket_url()
    if result is not None:
        set_repo_version(repo, 13)
        return

    jira_base = utils.get_default_jira_server()
    ticket_number = repo.path.split("/")[-1:][0].upper()
    issue_url = parse.urljoin(jira_base, "browse/" + ticket_number + "/",)

    with open(repo.get_metadata_path("issue_url", "w")) as out:
        out.write(issue_url)

    set_repo_version(repo, 13)


def migration_0014(repo, init=False, **kwargs):
    if init:
        set_repo_version(repo, 14)
        return

    with open(repo.get_metadata_path("git/info/exclude"), "w") as out:
        out.write("\n".join([".jirafs/git", ".jirafs/shadow", ".jirafs/operation.log"]))

    if os.path.exists(repo.get_local_path(".jirafs_ignore")):
        shutil.copyfile(
            repo.get_local_path(".jirafs_ignore"), repo.get_local_path(".jirafs_local"),
        )
        repo.run_git_command(
            "add", ".jirafs_local",
        )
    if os.path.exists(repo.get_metadata_path("gitignore")):
        shutil.copyfile(
            repo.get_metadata_path("gitignore"), repo.get_local_path(".jirafs_ignore")
        )
        repo.run_git_command(
            "add", ".jirafs_ignore",
        )
        repo.run_git_command("rm", repo.get_metadata_path("gitignore"))

    repo.run_git_command(
        "config",
        "--file=%s" % repo.get_metadata_path("git", "config",),
        "core.excludesfile",
        ".jirafs/combined_ignore",
    )

    tracked_files = repo.run_git_command("ls-files", "-c", failure_ok=True).split("\n")
    filtered_files = repo.filter_ignored_files(tracked_files, ".jirafs_ignore")
    ignored = repo.filter_ignored_files(
        set(tracked_files) - set(filtered_files), ".jirafs_local"
    )

    for filename in ignored:
        repo.run_git_command("rm", "--cached", filename, failure_ok=True, shadow=True)

    repo.run_git_command(
        "commit", "-m", "Completing migration_0014", failure_ok=True, shadow=True
    )

    set_repo_version(repo, 14)


def migration_0015(repo, init=False, **kwargs):
    """ No-op; was previously something else."""
    set_repo_version(repo, 15)


def migration_0016(repo, init=False, **kwargs):
    """ Add the 'macros_applied.patch' file to the repository."""
    macro_path = repo.get_metadata_path("macros_applied.patch")
    if not os.path.exists(macro_path):
        with open(macro_path, "w") as out:
            out.write("")

    repo.run_git_command("add", "-f", macro_path)
    repo.run_git_command("commit", "-m", "Completing migration_0015", failure_ok=True)

    set_repo_version(repo, 16)
