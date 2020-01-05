from __future__ import print_function

import argparse
import json
import logging
import os
import re
import sys

from blessings import Terminal
from distutils.version import LooseVersion

from .exceptions import MacroAttributeError, MacroContentError, MacroError
from . import __version__


logger = logging.getLogger(__name__)


class PluginError(Exception):
    pass


class PluginValidationError(PluginError):
    pass


class PluginOperationError(PluginError):
    pass


class CommandResult(str):
    def __new__(
        cls, string=None, return_code=None, cursor=0, no_format=False, **kwargs
    ):
        if string is None:
            string = ""
        if string and not string.endswith("\n"):
            string = string + "\n"

        terminal = Terminal()
        if not no_format:
            kwargs["t"] = terminal
            try:
                string = string.format(**kwargs)
            except KeyError:
                logger.warning(
                    "An error was encountered while attempting to format "
                    "string; returning the original string unformatted. "
                    "The caller may want to use the 'no_format' option if "
                    "the outgoing string includes curly braces.",
                )

        self = super(CommandResult, cls).__new__(cls, string)
        self.return_code = return_code
        self.terminal = terminal
        self.cursor = cursor

        return self

    def _echo(self, message):
        print(message, end="")

    def echo(self):
        self._echo(self[self.cursor :])
        self.cursor = len(self)

        return self

    def add_line(self, the_line, no_format=False, **kwargs):
        if not the_line.endswith("\n"):
            the_line = the_line + "\n"

        if not no_format:
            kwargs["t"] = self.terminal
            try:
                the_line = the_line.format(**kwargs)
            except KeyError:
                logger.warning(
                    "An error was encountered while attempting to format "
                    "string; returning the original string unformatted. "
                    "The caller may want to use the 'no_format' option if "
                    "the outgoing string includes curly braces.",
                )

        new_result = CommandResult(the_line)
        return self + new_result

    def __add__(self, other):
        joined_strings = super(CommandResult, self).__add__(other)

        return_code = None
        if self.return_code is not None:
            return_code = self.return_code
        if isinstance(other, CommandResult) and other.return_code is not None:
            return_code = other.return_code

        return CommandResult(
            joined_strings, return_code=return_code, cursor=self.cursor
        )

    @property
    def return_code(self):
        return self._return_code

    @return_code.setter
    def return_code(self, value):
        self._return_code = int(value) if value is not None else None


class JirafsPluginBase(object):
    MIN_VERSION = None
    MAX_VERSION = None

    def validate(self, **kwargs):
        if not self.MIN_VERSION or not self.MAX_VERSION:
            raise PluginValidationError(
                "Minimum and maximum version numbers not specified."
            )

        min_version = LooseVersion(self.MIN_VERSION)
        max_version = LooseVersion(self.MAX_VERSION)
        curr_version = LooseVersion(__version__)
        if not min_version <= curr_version < max_version:
            raise PluginValidationError(
                "Plugin '%s' is not compatible with version %s of Jirafs; "
                "minimum version: %s; maximum version %s."
                % (self.plugin_name, __version__, self.MIN_VERSION, self.MAX_VERSION,),
            )

        return True


class Plugin(JirafsPluginBase):
    def __init__(self, ticketfolder, plugin_name, **kwargs):
        self.ticketfolder = ticketfolder
        self.plugin_name = plugin_name

    @property
    def metadata_filename(self):
        return self.ticketfolder.get_metadata_path(
            "plugin_meta", "%s.json" % self.plugin_name,
        )

    def get_configuration(self):
        config = self.ticketfolder.get_config()
        if config.has_section(self.plugin_name):
            return dict(config.items(self.plugin_name))
        return {}

    def get_metadata(self):
        try:
            with open(self.metadata_filename, "r") as _in:
                return json.loads(_in.read())
        except (IOError, OSError):
            return {}

    def set_metadata(self, data):
        with open(self.metadata_filename, "w") as out:
            out.write(json.dumps(data, indent=4, sort_keys=True,))


class CommandPlugin(JirafsPluginBase):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def truncate_field_value(self, original_value, length=30):
        if original_value is None:
            original_value = ""
        elif not isinstance(original_value, str):
            original_value = str(original_value)
        value = original_value.strip()
        for newline in ("\n", "\r"):
            if newline in value:
                value = value[0 : value.find(newline)]

        value = value[0:length]

        if value != original_value:
            value = value[0 : length - 1] + u"\u2026"

        return value

    def get_description(self):
        try:
            return self.__doc__.strip()
        except AttributeError:
            raise None

    def add_arguments(self, parser):
        pass

    def parse_arguments(self, parser, extra_args):
        return parser.parse_args(extra_args)

    @classmethod
    def get_command_result(cls, result, original=None):
        if not isinstance(result, CommandResult):
            result = CommandResult(result)

        if original is not None:
            result = original + result

        return result

    @classmethod
    def execute_command(cls, extra_args, jira, path, command_name, **ckwargs):
        from .ticketfolder import TicketFolder

        cmd = cls(plugin_name=command_name)

        parser = argparse.ArgumentParser(
            prog=os.path.basename(sys.argv[0]) + " " + command_name,
            description=cmd.get_description(),
        )
        if cmd.auto_instantiate_folder():
            parser.add_argument(
                "--no-migrate", dest="migrate", default=True, action="store_false"
            )
        cmd.add_arguments(parser)
        args = cmd.parse_arguments(parser, extra_args)

        folder = None
        folder_plugins = []
        if cmd.auto_instantiate_folder():
            folder = TicketFolder(path, jira, migrate=args.migrate)
            folder_plugins = folder.plugins

        kwargs = {
            "args": args,
            "folder": folder,
            "jira": jira,
            "path": path,
            "parser": parser,
        }
        pre_method = "pre_%s" % command_name
        post_method = "post_%s" % command_name
        for plugin in folder_plugins:
            if not hasattr(plugin, pre_method):
                continue
            method = getattr(plugin, pre_method)
            result = method(**kwargs)
            if result is not None:
                kwargs = result

        cmd.validate(**kwargs)
        result = cls.get_command_result(cmd.handle(**kwargs))

        for plugin in folder_plugins:
            if not hasattr(plugin, post_method):
                continue
            method = getattr(plugin, post_method)
            post_result = method(result)
            if post_result is not None:
                result = cls.get_command_result(post_result, original=result)

        if getattr(cls, "RUN_FOR_SUBTASKS", False):
            for subfolder in folder.subtasks:
                try:
                    cls.execute_command(
                        extra_args, jira, subfolder.path, command_name, **ckwargs
                    )
                except Exception as e:
                    logger.exception(
                        "Exception encountered while running "
                        "'%s' for ticket subfolder '%s': %s"
                        % (command_name, subfolder.ticket_number, e)
                    )

        return result

    def handle(self, *args, **kwargs):
        return self.cmd(*args, **kwargs)

    def cmd(self, *args, **kwargs):
        # By default, no return value; just execute and move along
        self.main(*args, **kwargs)

    def main(self, *args, **kwargs):
        raise NotImplementedError()

    def try_subfolders(self):
        return getattr(self, "TRY_SUBFOLDERS", False)

    def auto_instantiate_folder(self):
        return getattr(self, "AUTOMATICALLY_INSTANTIATE_FOLDER", True,)


class DirectOutputCommandPlugin(CommandPlugin):
    def cmd(self, *args, **kwargs):
        return self.main(*args, **kwargs)


class MacroPlugin(Plugin):
    COMPONENT_NAME = None

    def __init__(self, folder, plugin_name, *args, **kwargs):
        self.ticketfolder = folder
        self.plugin_name = plugin_name
        self._args = args
        self._kwargs = kwargs

    def get_matcher(self):
        return re.compile(
            self.BASE_REGEX.format(tag_name=self.COMPONENT_NAME),
            re.MULTILINE | re.DOTALL,
        )

    def get_matches(self, content):
        return self.get_matcher().finditer(content)

    def get_attributes(self, tag):
        state_outer = 1
        state_raw_value = 2
        state_squoted_value = 3
        state_dquoted_value = 4
        state_name = 5
        state_name_ended = 6

        state = state_outer

        escapable = (
            "'",
            '"',
        )
        attributes = {}
        key = ""
        value = ""
        value_is_raw = False
        is_escaped = False

        def store_value():
            nonlocal value, key, attributes

            if not value_is_raw:
                attributes[key.strip()] = value.strip()
            elif value.strip().upper() == "TRUE":
                attributes[key.strip()] = True
            elif value.strip().upper() == "FALSE":
                attributes[key.strip()] = False
            else:
                attributes[key.strip()] = float(value)

            value = ""
            key = ""

        for tag_length, char in enumerate(tag):
            if char.isspace():
                break

        for char in tag[tag_length + 1 :]:
            if state == state_outer:
                if not char.isspace():
                    state = state_name
                    key += char
                    continue
            elif state == state_name:
                if char == "=":
                    state = state_name_ended
                else:
                    key += char
                continue
            elif state == state_name_ended:
                if not char.isspace():
                    if char == '"':
                        state = state_dquoted_value
                        value_is_raw = False
                        continue
                    elif char == "'":
                        state = state_squoted_value
                        value_is_raw = False
                        continue
                    else:
                        state = state_raw_value
                        value_is_raw = True
                        value += char
                        continue
            elif state == state_raw_value:
                if char.isspace():
                    store_value()
                    state = state_outer
                else:
                    value += char
                continue
            elif state == state_dquoted_value:
                if is_escaped:
                    if char in escapable:
                        is_escaped = False
                        value += char
                        continue
                    else:
                        raise MacroAttributeError("Invalid escape sequence: \\%s", char)

                if char == '"':
                    store_value()
                    state = state_outer
                elif char == "\\":
                    is_escaped = True
                else:
                    value += char
                continue
            elif state == state_squoted_value:
                if is_escaped:
                    if char in escapable:
                        is_escaped = False
                        value += char
                        continue
                    else:
                        raise MacroAttributeError("Invalid escape sequence: \\%s", char)

                if char == "'":
                    store_value()
                    state = state_outer
                elif char == "\\":
                    is_escaped = True
                else:
                    value += char
                continue

        if key or value:
            store_value()

        return attributes

    def process_text_data(self, content):
        def run_replacement(match_data):
            data = match_data.groupdict()

            try:
                attributes = self.get_attributes(data.get("start", ""))
            except Exception as e:
                raise MacroAttributeError("Unknown Error") from e

            return self.execute_macro(data.get("content"), **attributes)

        try:
            return self.get_matcher().sub(run_replacement, content)
        except MacroError:
            raise
        except Exception as e:
            raise MacroContentError(
                "Error encountered while running macro %s: %s", self.plugin_name, e,
            ) from e

    def execute_macro(self, data, **attributes):
        raise NotImplementedError()


class BlockElementMacroPlugin(MacroPlugin):
    BASE_REGEX = (
        r"<jirafs:(?P<start>{tag_name}[^>]*)>(?P<content>.*?)"
        r"</jirafs:(?P<end>{tag_name})>"
    )


class VoidElementMacroPlugin(MacroPlugin):
    BASE_REGEX = r"<jirafs:(?P<start>{tag_name}[^/]*)/>"
