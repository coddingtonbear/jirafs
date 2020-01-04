import collections
import configparser
import contextlib
import getpass
import logging
import os
import pkg_resources
import re
import subprocess

from jira.client import JIRA
from distutils.version import LooseVersion

from . import constants
from .plugin import CommandPlugin, Plugin


logger = logging.getLogger(__name__)


def convert_to_boolean(string):
    if string.upper().strip() in ["Y", "YES", "ON", "ENABLED", "ENABLE", "TRUE"]:
        return True
    elif string.upper().strip() in ["N", "NO", "OFF", "DISABLED", "DISABLE", "FALSE"]:
        return False
    return None


@contextlib.contextmanager
def stash_local_changes(repo):
    # Only v10 of repositories will properly handle stashing local
    # changes since the `version` file was previously untracked.
    try:
        if repo.version >= 10:
            repo.run_git_command("stash", failure_ok=True)
        yield
    finally:
        if repo.version >= 10:
            # This looks a little weird, I know, but what we're doing
            # is forcing a stash pop; even if it causes conflict markers,
            # that's better than just dropping the stash on the floor.
            patch = repo.run_git_command("stash", "show", "-p", failure_ok=True)
            if not patch:
                return
            repo.run_git_command(
                "apply", "-3", failure_ok=True, stdin=patch.encode("utf-8")
            )
            repo.run_git_command("stash", "drop", failure_ok=True)


def get_user_input(message, options=None, boolean=False, password=False):
    if not constants.ALLOW_USER_INPUT:
        raise RuntimeError("User input is disabled")

    value = None
    while value is None:
        if not password:
            raw_value = input(message + " ")
        else:
            raw_value = getpass.getpass(message + " ")

        if options and raw_value not in options:
            print("'%s' is not a valid response" % raw_value)
            continue
        elif boolean:
            result = convert_to_boolean(raw_value)
            if result is not None:
                value = result
            else:
                print("'%s' is not a valid response" % raw_value)
        elif raw_value.strip():
            value = raw_value
        else:
            print("Please enter a response")

    return value


def run_command_method_with_kwargs(command, method=None, **kwargs):
    if method is None:
        method = "main"
    installed_commands = get_installed_commands()
    return getattr(installed_commands[command](), method)(**kwargs)


def get_installed_commands():
    possible_commands = {}
    for entry_point in pkg_resources.iter_entry_points(group="jirafs_commands"):
        try:
            loaded_class = entry_point.load()
        except ImportError:
            logger.warning(
                "Attempted to load entrypoint %s, but " "an ImportError occurred.",
                entry_point,
            )
            continue
        if not issubclass(loaded_class, CommandPlugin):
            logger.warning(
                "Loaded entrypoint %s, but loaded class is "
                "not a subclass of `jirafs.plugin.CommandPlugin`.",
                entry_point,
            )
            continue
        possible_commands[entry_point.name] = loaded_class

    return possible_commands


def get_installed_plugins(subclass=Plugin):
    possible_plugins = {}
    for entry_point in pkg_resources.iter_entry_points(group="jirafs_plugins"):
        try:
            loaded_class = entry_point.load()
        except ImportError:
            logger.warning(
                "Attempted to load entrypoint %s, but " "an ImportError occurred.",
                entry_point,
            )
            continue
        if not issubclass(loaded_class, Plugin):
            logger.warning(
                "Loaded entrypoint %s, but loaded class is "
                "not a subclass of `jirafs.plugin.Plugin`.",
                entry_point,
            )
            continue
        if not issubclass(loaded_class, subclass):
            # Do not emit a warning here -- this filter occurs
            # when we've limited the acceptable plugins to
            # a subset of jirafs.plugin.Plugin classes
            # intentionally, so this test failing is not
            # an error.
            continue
        possible_plugins[entry_point.name] = loaded_class

    return possible_plugins


def get_config_path(filename):
    if filename.startswith("/"):
        return filename
    return os.path.expanduser("~/%s" % filename)


def get_config(additional_configs=None, include_global=True):
    filenames = []
    if include_global:
        filenames.append(get_config_path(constants.GLOBAL_CONFIG))
    if additional_configs:
        filenames.extend(additional_configs)

    parser = configparser.RawConfigParser()
    parser.read(filenames)
    return parser


def set_global_config_value(section, key, value):
    config = get_config()
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, key, value)
    with open(get_config_path(constants.GLOBAL_CONFIG), "w") as out:
        config.write(out)


def get_default_jira_server(config=None):
    if config is None:
        config = get_config()

    if not config.has_section(constants.CONFIG_JIRA):
        config.add_section(constants.CONFIG_JIRA)

    if not config.has_option(constants.CONFIG_JIRA, "server"):
        value = get_user_input("Default JIRA URL: ")
        config.set(constants.CONFIG_JIRA, "server", value)

    with open(
        os.path.expanduser("~/%s" % constants.GLOBAL_CONFIG), "w"
    ) as global_config:
        config.write(global_config)

    return config.get(constants.CONFIG_JIRA, "server")


def get_jira(domain=None, config=None):
    def get_section(config, domain):
        if domain is None:
            return constants.CONFIG_JIRA

        valid_options = [
            domain.strip("/"),
            domain.strip("/") + "/",
        ]

        for option in valid_options:
            if config.has_section(option):
                return option

        config.add_section(valid_options[0])
        return valid_options[0]

    if config is None:
        config = get_config()

    if not config.has_section(constants.CONFIG_MAIN):
        config.add_section(constants.CONFIG_MAIN)

    ask_to_save = True
    if config.has_option(constants.CONFIG_MAIN, "ask_to_save"):
        ask_to_save = convert_to_boolean(
            config.get(constants.CONFIG_MAIN, "ask_to_save")
        )

    login_data = {"verify": True}

    section = get_section(config, domain)

    if domain is not None:
        login_data["server"] = domain
    else:
        login_data["server"] = get_default_jira_server(config)
        # Config may have been changed as a result of the above; reload.
        config = get_config()

    if not config.has_option(section, "username"):
        value = get_user_input("JIRA Username (%s):" % login_data["server"])
        login_data["username"] = value
        config.set(section, "username", value)
    else:
        login_data["username"] = config.get(section, "username")

    if not config.has_option(section, "password"):
        value = get_user_input(
            "JIRA Password (%s):" % login_data["server"], password=True,
        )
        login_data["password"] = value

        if ask_to_save:
            save = get_user_input("Save JIRA Password (Y/N)?", boolean=True)
            if save:
                config.set(section, "password", value)
    else:
        login_data["password"] = config.get(section, "password")

    if config.has_option(section, "verify"):
        value = convert_to_boolean(config.get(section, "verify"))
        if value is None:
            # This means that we weren't able to convert the string's value
            # to a boolean, and it's probably instead a path to a PEM file.
            login_data["verify"] = config.get(section, "verify")
        else:
            login_data["verify"] = value

    # Prevent python-jira from checking to see if its out of date.
    login_data["check_update"] = False

    basic_auth = (
        login_data.pop("username"),
        login_data.pop("password"),
    )
    jira = JIRA(login_data, basic_auth=basic_auth)

    with open(get_config_path(constants.GLOBAL_CONFIG), "w") as global_config:
        config.write(global_config)

    return jira


def get_git_version():
    result = subprocess.check_output(
        ["git", "--version"], stderr=subprocess.PIPE,
    ).decode("utf8")
    version_string = re.match("git version ([0-9.]+).*", result).group(1)
    return LooseVersion(version_string)


def lazy_get_jira():
    return lambda domain, config=None: get_jira(domain, config)


PostStatusResponse = collections.namedtuple("PostStatusResponse", ["new", "hash"])
