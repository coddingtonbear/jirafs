import codecs
import fnmatch
import logging
import logging.handlers
import io
import json
import os
import re
import subprocess
from urllib import parse

from jira.resources import Issue

from . import constants
from . import exceptions
from . import migrations
from . import utils
from .jiralinkmanager import JiraLinkManager
from .jirafieldmanager import JiraFieldManager
from .plugin import MacroPlugin, PluginValidationError
from .exceptions import MacroError


class TicketFolderLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return (
            "{{{issue_id}}} {msg}".format(issue_id=self.extra["issue_id"], msg=msg,),
            kwargs,
        )


class TicketFolder(object):
    def __init__(self, path, jira, migrate=True, quiet=False):
        self.path = os.path.realpath(os.path.expanduser(path))
        self.quiet = quiet
        self.issue_url = self.get_ticket_url()
        self.get_jira = jira

        self._formatter = logging.Formatter(
            fmt="%(asctime)s\t%(levelname)s\t%(module)s\t%(message)s"
        )
        self._handler = logging.handlers.RotatingFileHandler(
            self.get_metadata_path(constants.TICKET_OPERATION_LOG),
            maxBytes=2 ** 20,
            backupCount=2,
            encoding="utf-8",
        )
        self._handler.setFormatter(self._formatter)
        self._logger = logging.getLogger(
            ".".join([__name__, self.ticket_number.replace("-", "_")])
        )
        self._logger.addHandler(self._handler)
        self._logger_adapter = TicketFolderLoggerAdapter(
            self._logger, {"issue_id": self.ticket_number},
        )

        if not os.path.isdir(self.metadata_dir):
            raise exceptions.NotTicketFolderException(
                "%s is not a synchronizable ticket folder" % (path)
            )

        self.plugins = self.load_plugins()

        if migrate:
            self.run_migrations()

        # If no `new_comment.jira.txt` file exists, let's create one
        comment_path = self.get_local_path(constants.TICKET_NEW_COMMENT)
        if not os.path.exists(comment_path):
            with io.open(comment_path, "w", encoding="utf-8") as out:
                out.write("")

        # Let's update the ignore file while we're here.
        self.build_ignore_files()

    @property
    def logger(self):
        return self._logger_adapter

    def __repr__(self):
        value = self.__str__()
        return "<%s>" % value

    def __str__(self):
        return "[%s] at %s" % (self.ticket_number, self.path)

    @property
    def subtasks(self):
        if hasattr(self, "_subtasks"):
            return self._subtasks
        self._subtasks = []

        subtasks_path = self.get_metadata_path("subtasks")
        if not os.path.exists(subtasks_path):
            return self._subtasks

        with open(subtasks_path, "r") as in_:
            for line in in_:
                ticket_number = line.strip()
                folder = self.__class__(
                    self.get_path(ticket_number,), utils.lazy_get_jira()
                )
                self._subtasks.append(folder)

        return self._subtasks

    def load_plugins(self):
        config = self.get_config()
        plugins = []

        if not config.has_section(constants.CONFIG_PLUGINS):
            return plugins

        installed_plugins = utils.get_installed_plugins()

        for name, status in config.items(constants.CONFIG_PLUGINS):
            if not utils.convert_to_boolean(status):
                # This plugin is not turned on.
                continue
            if name not in installed_plugins:
                # This plugin is not installed.
                self.log(
                    "Plugin '%s' is not available.", (name,),
                )
                continue

            plugin = installed_plugins[name](self, name)

            try:
                plugin.validate()
            except PluginValidationError as e:
                self.log(
                    "Plugin '%s' did not pass validation; not loading: %s.", (name, e,)
                )

            plugins.append(plugin)

        return plugins

    def get_config(self):
        local_config_file = self.get_metadata_path("config")
        additional_configs = []
        if os.path.exists(local_config_file):
            additional_configs.append(local_config_file)

        return utils.get_config(additional_configs)

    def set_config_value(self, section, key, value):
        with utils.stash_local_changes(self):
            local_config_file = self.get_metadata_path("config")

            config = utils.get_config(
                additional_configs=[local_config_file], include_global=False,
            )
            if not config.has_section(section):
                config.add_section(section)
            config.set(section, key, value)

            with open(local_config_file, "w") as out:
                config.write(out)

            self.run_git_command("add", ".jirafs/config")
            self.run_git_command("commit", "-m", "Config change", failure_ok=True)

    @property
    def jira_base(self):
        match = re.match(r"(.*)\/browse\/.*", self.issue_url)
        if not match:
            raise ValueError(
                "Could not infer JIRA server URL from issue URL %s" % (self.issue_url,)
            )
        return match.group(1)

    @property
    def ticket_number(self):
        parts = parse.urlparse(self.issue_url)
        match = re.match(r".*\/browse\/(\w+-\d+)\/?.*", parts.path)
        if not match:
            raise ValueError(
                "Could not infer ticket number from URL %s" % self.issue_url
            )
        return match.group(1)

    @property
    def jira(self):
        if not hasattr(self, "_jira"):
            self._jira = self.get_jira(self.jira_base, config=self.get_config())
        return self._jira

    @property
    def issue(self):
        if not hasattr(self, "_issue"):
            self._issue = self.jira.issue(self.ticket_number)
        return self._issue

    def clear_cache(self):
        if hasattr(self, "_issue"):
            del self._issue
        if hasattr(self, "_jira"):
            del self._jira

    def store_cached_issue(self, shadow=True):
        storable = {"options": self.issue._options, "raw": self.issue.raw}
        with io.open(
            self.get_path(".jirafs/issue.json", shadow=shadow), "w", encoding="utf-8",
        ) as out:
            out.write(
                json.dumps(storable, indent=4, sort_keys=True, ensure_ascii=False,)
            )

    @property
    def cached_issue(self):
        if not hasattr(self, "_cached_issue"):
            try:
                issue_path = self.get_metadata_path("issue.json")
                with io.open(issue_path, "r", encoding="utf-8") as _in:
                    storable = json.loads(_in.read())
                    self._cached_issue = Issue(
                        storable["options"], None, storable["raw"],
                    )
            except IOError:
                self.log(
                    "Error encountered while loading cached issue!",
                    level=logging.ERROR,
                )
                self._cached_issue = self.issue
        return self._cached_issue

    @property
    def metadata_dir(self) -> str:
        return os.path.join(self.path, constants.METADATA_DIR,)

    @property
    def git_master(self) -> str:
        return self.run_git_command("rev-parse", "master")

    @property
    def git_merge_base(self) -> str:
        return self.run_git_command("merge-base", "master", "jira",)

    @property
    def git_branch(self) -> str:
        return self.run_git_command("rev-parse", "--abbrev-ref", "HEAD")

    @property
    def on_master(self) -> bool:
        return self.git_branch == "master"

    def get_ticket_url(self):
        try:
            with io.open(
                self.get_metadata_path("issue_url"), "r", encoding="utf-8"
            ) as in_:
                return in_.read().strip()
        except (IOError, OSError):
            return None

    def get_metadata_path(self, *args) -> str:
        return os.path.join(self.metadata_dir, *args)

    def get_remote_file_metadata(self, shadow=True):
        remote_files = self.get_path(".jirafs/remote_files.json", shadow=shadow)
        try:
            with io.open(remote_files, "r", encoding="utf-8") as _in:
                data = json.loads(_in.read())
        except IOError:
            data = {}

        return data

    def set_remote_file_metadata(self, data, shadow=True):
        remote_files = self.get_path(".jirafs/remote_files.json", shadow=shadow)
        with io.open(remote_files, "w", encoding="utf-8") as out:
            out.write(json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False,))

    def get_local_path(self, *args):
        return os.path.join(self.path, *args)

    def get_shadow_path(self, *args):
        return os.path.join(self.get_metadata_path("shadow"), *args)

    def get_path(self, *args, **kwargs):
        shadow = kwargs.get("shadow", False)

        if shadow:
            return self.get_shadow_path(*args)
        return self.get_local_path(*args)

    @property
    def version(self):
        try:
            with io.open(
                self.get_metadata_path("version"), "r", encoding="utf-8"
            ) as _in:
                return int(_in.read().strip())
        except IOError:
            return 1

    @property
    def log_path(self):
        return self.get_metadata_path(constants.TICKET_OPERATION_LOG)

    @classmethod
    def initialize_ticket_folder(cls, ticket_url, path, jira):
        path = os.path.realpath(path)

        metadata_path = os.path.join(path, constants.METADATA_DIR,)
        os.mkdir(metadata_path)

        with io.open(
            os.path.join(metadata_path, "issue_url"), "w", encoding="utf-8"
        ) as out:
            out.write(ticket_url)

        # Create bare git repository so we can easily detect changes.
        subprocess.check_call(
            ("git", "--bare", "init", os.path.join(metadata_path, "git",)),
            stdout=subprocess.PIPE,
        )
        subprocess.check_call(
            (
                "git",
                "config",
                "--file=%s" % os.path.join(metadata_path, "git", "config"),
                "core.excludesfile",
                constants.GIT_IGNORE_FILE,
            )
        )

        excludes_path = os.path.join(metadata_path, "git", "info", "exclude")
        with io.open(excludes_path, "w", encoding="utf-8") as gitignore:
            gitignore.write(
                "\n".join(
                    [
                        "%s/git" % constants.METADATA_DIR,
                        "%s/shadow" % constants.METADATA_DIR,
                        "%s/operation.log" % constants.METADATA_DIR,
                    ]
                )
            )

        instance = cls(path, jira, migrate=False)
        instance.log(
            "Ticket folder for issue %s created at %s",
            (instance.ticket_number, instance.path,),
        )
        instance.run_git_command("add", "-A")
        instance.run_git_command("commit", "--allow-empty", "-m", "Initialized")
        instance.run_migrations(init=True)

        comment_path = instance.get_local_path(constants.TICKET_NEW_COMMENT)
        with io.open(comment_path, "w", encoding="utf-8") as out:
            out.write("")

        return instance

    def run_git_command(self, command, *args, **kwargs):
        failure_ok = kwargs.get("failure_ok", False)
        shadow = kwargs.get("shadow", False)
        binary = kwargs.get("binary", False)
        stdin = kwargs.get("stdin", "")

        args = list(args)

        if not shadow:
            work_tree = (self.path,)
            git_dir = self.get_metadata_path("git")
            cwd = self.path
        else:
            work_tree = self.get_metadata_path("shadow")
            git_dir = self.get_metadata_path("shadow/.git")
            cwd = self.get_metadata_path("shadow")

        cmd = [
            "git",
            "--work-tree=%s" % work_tree,
            "--git-dir=%s" % git_dir,
        ]
        cmd.append(command)
        if command == "commit":
            args.append("--author='%s'" % constants.GIT_AUTHOR)
        cmd.extend(args)

        self.log("Executing git command `%s`", (" ".join(cmd),), logging.DEBUG)

        handle = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
        )
        result, _ = handle.communicate(stdin)

        if handle.returncode != 0 and not failure_ok:
            command = " ".join(cmd)
            raise exceptions.GitCommandError(
                "Error running command `%s`" % command,
                returncode=handle.returncode,
                stdout=result,
                cmd=command,
            )
        if not binary:
            return result.decode("utf-8").strip()
        return result

    def get_local_file_at_revision(self, path, revision, failure_ok=True, binary=False):
        return self.run_git_command(
            "show", "%s:%s" % (revision, path,), failure_ok=failure_ok, binary=binary,
        )

    def get_ignore_globs(self, which=constants.LOCAL_ONLY_FILE):
        all_globs = [
            constants.TICKET_DETAILS,
            constants.TICKET_COMMENTS,
            constants.TICKET_NEW_COMMENT,
            constants.TICKET_LINKS,
        ]
        for field in constants.FILE_FIELDS:
            all_globs.append(
                constants.TICKET_FILE_FIELD_TEMPLATE.format(field_name=field)
            )

        def get_globs_from_file(input_file):
            globs = []
            for line in input_file.readlines():
                if line.startswith("#") or not line.strip():
                    continue
                globs.append(line.strip())
            return globs

        try:
            with io.open(
                self.get_local_path(which), "r", encoding="utf-8"
            ) as local_ign:
                all_globs.extend(get_globs_from_file(local_ign))
        except IOError:
            pass

        try:
            with io.open(
                os.path.expanduser("~/%s" % which), "r", encoding="utf-8"
            ) as global_ignores:
                all_globs.extend(get_globs_from_file(global_ignores))
        except IOError:
            pass

        return all_globs

    def file_matches_globs(self, filename, ignore_globs):
        for glob in ignore_globs:
            if fnmatch.fnmatch(filename, glob):
                return True
        return False

    def get_ready_changes(self):
        ready = {
            "fields": (self.get_fields("HEAD") - self.get_fields(self.git_merge_base)),
            "links": (self.get_links("HEAD") - self.get_links(self.git_merge_base)),
            "new_comment": self.get_new_comment(ready=True),
        }

        current_hash = self.run_git_command("rev-parse", "master")
        committed_files = set(
            self.run_git_command("ls-tree", "--name-only", "-r", current_hash).split(
                "\n"
            )
        )
        merge_base_files = set(
            self.run_git_command(
                "ls-tree", "--name-only", "-r", self.git_merge_base
            ).split("\n")
        )
        ready["deleted"] = self.filter_ignored_files(
            list(merge_base_files - committed_files),
            constants.LOCAL_ONLY_FILE,
            constants.GIT_IGNORE_FILE,
            constants.GIT_EXCLUDE_FILE,
            allow_nonfile=True,
        )

        changed_files = self.filter_ignored_files(
            self.run_git_command(
                "diff", "--name-only", "%s..master" % self.git_merge_base,
            ).split("\n"),
            constants.LOCAL_ONLY_FILE,
        )
        ready["files"] = [
            filename for filename in changed_files if filename not in ready["deleted"]
        ]

        return ready

    def get_uncommitted_changes(self):
        uncommitted = {
            "fields": self.get_fields() - self.get_fields("HEAD"),
            "new_comment": self.get_new_comment(ready=False),
            "links": self.get_links() - self.get_links("HEAD"),
        }

        new_files = self.run_git_command("ls-files", "-o", failure_ok=True).split("\n")
        modified_files = self.run_git_command("ls-files", "-m", failure_ok=True).split(
            "\n"
        )
        deleted_files = self.run_git_command("ls-files", "-d", failure_ok=True).split(
            "\n"
        )
        uncommitted["files"] = self.filter_ignored_files(
            [filename for filename in new_files + modified_files if filename],
            constants.LOCAL_ONLY_FILE,
            constants.GIT_IGNORE_FILE,
            constants.GIT_EXCLUDE_FILE,
        )
        uncommitted["deleted"] = self.filter_ignored_files(
            [filename for filename in deleted_files if filename],
            constants.LOCAL_ONLY_FILE,
            constants.GIT_IGNORE_FILE,
            constants.GIT_EXCLUDE_FILE,
            allow_nonfile=True,  # They're deleted, after all
        )
        return uncommitted

    def get_local_uncommitted_changes(self):
        new_files = self.run_git_command("ls-files", "-o", failure_ok=True).split("\n")
        modified_files = self.run_git_command("ls-files", "-m", failure_ok=True).split(
            "\n"
        )

        committable = self.filter_ignored_files(
            [filename for filename in new_files + modified_files if filename],
            constants.LOCAL_ONLY_FILE,
        )
        uncommitted = self.filter_ignored_files(
            [
                filename
                for filename in modified_files + new_files
                if filename not in committable
            ],
            constants.GIT_IGNORE_FILE,
            constants.GIT_EXCLUDE_FILE,
        )

        return {"files": uncommitted}

    def get_remotely_changed(self):
        metadata = self.get_remote_file_metadata(shadow=True)

        assets = []
        attachments = self.filter_ignored_files(
            getattr(self.issue.fields, "attachment", []), constants.REMOTE_IGNORE_FILE
        )
        for attachment in attachments:
            changed = metadata.get(attachment.filename) != attachment.created
            if changed:
                assets.append(attachment.filename)

        return assets

    def filter_ignored_files(self, files, *which, allow_nonfile=False):
        if len(which) < 1:
            which = [constants.LOCAL_ONLY_FILE]
        if not isinstance(which, (list, tuple)):
            which = [which]

        for list_path in which:
            ignore_globs = self.get_ignore_globs(list_path)

            assets = []
            for fileish in files:
                # Get the actual filename; this is a little gross -- apologies.
                filename = fileish
                attachment = False
                if not isinstance(fileish, str):
                    filename = fileish.filename
                    attachment = True

                if self.file_matches_globs(filename, ignore_globs):
                    continue
                if (
                    not attachment
                    and not allow_nonfile
                    and not os.path.isfile(os.path.join(self.path, filename))
                ):
                    continue
                if filename.startswith("."):
                    continue
                assets.append(fileish)
            files = assets

        return assets

    def get_macro_plugins(self):
        if not hasattr(self, "_macro_plugins"):
            config = self.get_config()
            plugins = []

            if not config.has_section(constants.CONFIG_PLUGINS):
                return plugins

            installed_plugins = utils.get_installed_plugins(MacroPlugin)

            for entrypoint_name, status in config.items(constants.CONFIG_PLUGINS):
                if not utils.convert_to_boolean(status):
                    # This plugin is not turned on.
                    continue
                if entrypoint_name not in installed_plugins:
                    # This plugin is not installed.
                    self.log(
                        "Macro plugin '%s' is not available; "
                        "this is probably because this plugin is not a "
                        "macro.",
                        (entrypoint_name,),
                        level=logging.DEBUG,
                    )
                    continue

                plugin = installed_plugins[entrypoint_name](self, entrypoint_name)

                try:
                    plugin.validate()
                except PluginValidationError as e:
                    self.log(
                        "Plugin '%s' did not pass validation; " "not loading: %s.",
                        (entrypoint_name, e,),
                    )

                plugins.append(plugin)

            self._macro_plugins = plugins

        return self._macro_plugins

    def process_macros_for_all_fields(self):
        # Now let each plugin run its cleanup if necessary
        for plugin in self.get_macro_plugins():
            try:
                plugin.cleanup_pre_process()
            except NotImplementedError:
                pass

        # This is run just in case these macros are writing
        # files as part of their operation, and we need to have
        # those files written in advance of certain operations
        # like listing changes or committing
        fields = self.get_fields()
        for field_name in fields:
            fields.get_transformed(field_name)

        self.get_new_comment()
        with open(self.get_path(constants.TICKET_COMMENTS), "r") as inf:
            self.process_macros(inf.read())

        # Now let each plugin run its cleanup if necessary
        for plugin in self.get_macro_plugins():
            try:
                plugin.cleanup_post_process()
            except NotImplementedError:
                pass

    def process_macros(self, data, path=None):
        macro_plugins = self.get_macro_plugins()

        for plugin in macro_plugins:
            try:
                if isinstance(data, str):
                    data = plugin.process_text_data(data, path)
                else:
                    continue
            except MacroError as e:
                # Annotate the MacroError with information about what
                # macro caused the error
                e.macro_name = plugin.entrypoint_name
                raise e from e

        unprocessed = re.compile(r"(<jirafs:.*>)", re.MULTILINE | re.DOTALL).findall(
            data
        )
        if unprocessed:
            raise exceptions.UnknownMacroError(unprocessed)

        return data

    def process_macro_reversals(self, data):
        macro_plugins = self.get_macro_plugins()

        for plugin in macro_plugins:
            try:
                if isinstance(data, str):
                    data = plugin.process_text_data_reversal(data)
                else:
                    continue
            except MacroError as e:
                # Annotate the MacroError with information about what
                # macro caused the error
                e.macro_name = plugin.entrypoint_name
                raise e from e

        return data

    def get_links(self, revision=None, path=None):
        kwargs = {}
        if not revision:
            kwargs["path"] = path if path else self.path
        else:
            kwargs["revision"] = revision
        return JiraLinkManager.create(self, **kwargs)

    def get_fields(self, revision=None, path=None):
        kwargs = {}
        if not revision:
            kwargs["path"] = path if path else self.path
        else:
            kwargs["revision"] = revision
        return JiraFieldManager.create(self, **kwargs)

    def get_new_comment(self, clear=False, staged=False, ready=False):
        try:
            with io.open(
                self.get_local_path(constants.TICKET_NEW_COMMENT),
                "r+",
                encoding="utf-8",
            ) as c:
                local_contents = c.read().strip()
            if ready:
                contents = self.get_local_file_at_revision(
                    constants.TICKET_NEW_COMMENT, "HEAD"
                )
                if contents:
                    contents = contents.strip()
                else:
                    contents = ""
            else:
                contents = local_contents

            if not ready and contents == self.get_new_comment(ready=True):
                contents = ""

            if contents == local_contents and clear:
                with io.open(
                    self.get_local_path(constants.TICKET_NEW_COMMENT),
                    "r+",
                    encoding="utf-8",
                ) as c:
                    c.truncate()
        except IOError:
            contents = ""

        # Apply macro plugins
        return self.process_macros(contents)

    def get_field_value_by_dotpath(self, field_name, raw=False, **kwargs):
        fields = self.get_fields()

        key_dotpath = None
        if "." in field_name:
            field_name, key_dotpath = field_name.split(".", 1)

        if field_name not in fields:
            raise exceptions.JirafsError("Field '%s' does not exist." % field_name)

        if raw:
            data = fields[field_name]
        else:
            data = fields.get_transformed(field_name)

        if key_dotpath:
            try:
                for component in key_dotpath.split("."):
                    if not isinstance(data, dict):
                        raise exceptions.JirafsError(
                            "Key '%s' (of dotpath '%s') is not an object "
                            "in field '%s'." % (component, key_dotpath, field_name,)
                        )
                    elif component not in data:
                        if "default" in kwargs:
                            data = kwargs["default"]
                        else:
                            raise exceptions.JirafsError(
                                f"Keypath {key_dotpath} does not exist"
                            )
                        break
                    else:
                        data = data[component]
            except (ValueError, TypeError):
                raise exceptions.JirafsError(
                    "Field '%s' could not be parsed as JSON for retrieving "
                    "dotpath '%s'." % (field_name, key_dotpath,)
                )

        return data

    def is_up_to_date(self):
        jira_commit = self.run_git_command("rev-parse", "jira")
        master_commit = self.run_git_command("rev-parse", "master")

        try:
            self.run_git_command(
                "merge-base", "--is-ancestor", jira_commit, master_commit,
            )
        except exceptions.GitCommandError:
            return False
        return True

    def status(self):
        self.process_macros_for_all_fields()

        return {
            "ready": self.get_ready_changes(),
            "local_uncommitted": self.get_local_uncommitted_changes(),
            "uncommitted": self.get_uncommitted_changes(),
            "up_to_date": self.is_up_to_date(),
        }

    def run_migrations(self, init=False):
        loglevel = logging.INFO
        if init:
            loglevel = logging.DEBUG
        else:
            if not os.path.exists(self.get_metadata_path("git")):
                raise exceptions.JirafsError(
                    "{path} is not a valid ticket folder!".format(path=self.path)
                )

            if self.version < constants.CURRENT_REPO_VERSION:
                print(
                    "Your ticket folder at {path} is out-of-date "
                    "and is being automatically updated.".format(path=self.path)
                )
        while self.version < constants.CURRENT_REPO_VERSION:
            migrator = getattr(
                migrations, "migration_%s" % str(self.version + 1).zfill(4)
            )
            self.migrate(migrator, loglevel=loglevel, init=init)

    def migrate(self, migrator, loglevel=logging.INFO, init=False):
        with utils.stash_local_changes(self):
            self.log("%s: Migration started", (migrator.__name__,), loglevel)
            migrator(self, init=init)
            self.log("%s: Migration finished", (migrator.__name__,), loglevel)

    def build_ignore_files(self):
        metadata_excludes = [
            "git",
            "shadow",
            "operation.log",
            "subtasks",
            "temp-generated",
        ]
        with codecs.open(
            self.get_local_path(constants.GIT_EXCLUDE_FILE), "w", "utf-8"
        ) as out:
            for line in metadata_excludes:
                out.write("%s/%s\n" % (constants.METADATA_DIR, line,))
            subtask_list_path = self.get_metadata_path("subtasks")
            if os.path.exists(subtask_list_path):
                with open(subtask_list_path, "r") as in_:
                    for line in in_:
                        out.write("%s/*\n" % line.strip())

        with codecs.open(
            self.get_metadata_path("combined_ignore"), "w", "utf-8"
        ) as out:
            try:
                out.write("# ~/%s\n" % constants.GIT_IGNORE_FILE_PARTIAL)
                with codecs.open(
                    os.path.expanduser("~/%s" % constants.GIT_IGNORE_FILE_PARTIAL),
                    "r",
                    "utf-8",
                ) as in_:
                    for line in in_:
                        out.write("%s\n" % line.strip())
            except Exception:
                pass

            try:
                out.write("# %s\n" % (self.get_path(constants.GIT_IGNORE_FILE_PARTIAL)))
                with codecs.open(
                    self.get_path(constants.GIT_IGNORE_FILE_PARTIAL), "r", "utf-8"
                ) as in_:
                    for line in in_:
                        out.write("%s\n" % line.strip())
            except Exception:
                pass

    def log(self, message, args=None, level=logging.INFO):
        if args is None:
            args = []

        self.logger.log(level, message, *args)

    def get_log(self):
        with io.open(self.log_path, "r", encoding="utf-8") as log_file:
            return log_file.read()
