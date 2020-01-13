from __future__ import print_function

import argparse
import codecs
import hashlib
import json
import logging
import os
import re
import sys
from typing import (
    Dict,
    Iterator,
    List,
    Match,
    Optional,
    Pattern,
    Set,
    Tuple,
    TYPE_CHECKING,
    Union,
)

from blessings import Terminal
from distutils.version import LooseVersion

from .exceptions import MacroAttributeError, MacroContentError, MacroError
from .types import JirafsMacroAttributes
from . import __version__, constants

if TYPE_CHECKING:
    from .ticketfolder import TicketFolder


logger = logging.getLogger(__name__)


class PluginError(Exception):
    pass


class PluginValidationError(PluginError):
    pass


class PluginOperationError(PluginError):
    pass


class MacroResult(str):
    _generated_filenames: List[str] = []

    def __new__(
        cls, string: str = None, generated_filenames: Optional[List[str]] = None
    ):
        if string is None:
            string = ""
        if generated_filenames is None:
            generated_filenames = []

        self: MacroResult = super().__new__(cls, string)  # type: ignore
        self._generated_filenames = generated_filenames

        return self

    @property
    def generated_filenames(self) -> List[str]:
        return self._generated_filenames


class CommandResult(str):
    _return_code: Optional[int] = None
    terminal: Optional[Terminal] = None
    cursor: int = 0

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

        self = str.__new__(cls, string)
        self._return_code = return_code
        self.terminal = terminal
        self.cursor = cursor

        return self

    def _echo(self, message: str) -> None:
        print(message, end="")

    def echo(self):
        self._echo(self[self.cursor :])
        self.cursor = len(self)

        return self

    def add_line(self, the_line: str, no_format: bool = False, **kwargs):
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

        new_result = CommandResult(the_line, no_format=no_format)
        return self + new_result

    def __add__(self, other):
        joined_strings = super(CommandResult, self).__add__(other)

        return_code = None
        if self.return_code is not None:
            return_code = self.return_code
        if isinstance(other, CommandResult) and other.return_code is not None:
            return_code = other.return_code

        return CommandResult(
            joined_strings, return_code=return_code, cursor=self.cursor, no_format=True
        )

    @property
    def return_code(self) -> int:
        return self._return_code or 0

    @return_code.setter
    def return_code(self, value):
        self._return_code = int(value) if value is not None else None


class JirafsPluginBase(object):
    MIN_VERSION = None
    MAX_VERSION = None

    def __init__(self, ticketfolder, entrypoint_name, **kwargs):
        self.ticketfolder: TicketFolder = ticketfolder
        self.entrypoint_name: str = entrypoint_name

    def validate(self, **kwargs) -> bool:
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
                % (
                    self.entrypoint_name,
                    __version__,
                    self.MIN_VERSION,
                    self.MAX_VERSION,
                ),
            )

        return True

    @property
    def metadata_filename(self) -> str:
        return self.ticketfolder.get_metadata_path(
            "plugin_meta", "%s.json" % self.entrypoint_name,
        )

    def get_configuration(self) -> Dict:
        config = self.ticketfolder.get_config()
        if config.has_section(self.entrypoint_name):
            return dict(config.items(self.entrypoint_name))
        return {}

    def _get_metadata(self):
        try:
            with open(self.metadata_filename, "r") as _in:
                return json.loads(_in.read())
        except (IOError, OSError):
            return {}

    def _set_metadata(self, data):
        with open(self.metadata_filename, "w") as out:
            out.write(json.dumps(data, indent=4, sort_keys=True,))

    @property
    def metadata(self):
        if not hasattr(self, "_metadata"):
            self._metadata = self._get_metadata()

        return self._metadata

    def save(self):
        # We'll also be running transformations for items when processing
        # incoming changes from Jira, but since the 'jira' branch is
        # always a fork from 'master', that may cause our later merge
        # of those two branches to create a merge conflict.  To prevent
        # that, let's just not let metadata be saved if we're not on the
        # master copy.
        if not self.ticketfolder.on_master:
            return

        self._set_metadata(self.metadata)


class Plugin(JirafsPluginBase):
    pass


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
            value = value[0 : length - 1] + "\u2026"

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

        cmd = cls(entrypoint_name=command_name)

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

    def handle(self, *args, **kwargs) -> None:
        self.cmd(*args, **kwargs)

    def cmd(self, *args, **kwargs) -> None:
        # By default, no return value; just execute and move along
        self.main(*args, **kwargs)

    def main(self, *args, **kwargs) -> None:
        raise NotImplementedError()

    def try_subfolders(self) -> bool:
        return getattr(self, "TRY_SUBFOLDERS", False)

    def auto_instantiate_folder(self) -> bool:
        return getattr(self, "AUTOMATICALLY_INSTANTIATE_FOLDER", True,)


class DirectOutputCommandPlugin(CommandPlugin):
    def cmd(self, *args, **kwargs):
        return self.main(*args, **kwargs)


class MacroPlugin(Plugin):
    TAG_NAME = None
    MATCHERS = [
        (
            r"<jirafs:(?P<start>{tag_name}[^>]*)>(?P<content>.*?)"
            r"</jirafs:(?P<end>{tag_name})>"
        ),
        r"<jirafs:(?P<start>{tag_name}[^/]*)/>",
    ]

    def __init__(self, folder, entrypoint_name, *args, **kwargs):
        self.ticketfolder: TicketFolder = folder
        self.entrypoint_name: str = entrypoint_name
        self._args = args
        self._kwargs = kwargs

    @property
    def tag_name(self) -> str:
        assert isinstance(self.TAG_NAME, str)

        return self.TAG_NAME

    def get_matchers(self) -> List[Pattern]:
        return [
            re.compile(rex.format(tag_name=self.tag_name), re.MULTILINE | re.DOTALL,)
            for rex in self.MATCHERS
        ]

    def get_matches(self, content: str) -> Iterator[Match]:
        for matcher in self.get_matchers():
            yield from matcher.finditer(content)

    def get_attributes(self, tag: str) -> JirafsMacroAttributes:
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

        decoder = codecs.getdecoder("unicode_escape")

        def store_value():
            nonlocal value, key, attributes

            if not value_is_raw:
                attributes[key.strip()] = value
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
                    is_escaped = False
                    if char in escapable:
                        value += char
                    else:
                        value += decoder(b"\\%s" % char.encode("utf-8"))[0]
                    continue

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
                    is_escaped = False
                    if char in escapable:
                        value += char
                    else:
                        value += decoder(b"\\%s" % char.encode("utf-8"))[0]
                    continue

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

    def get_processed_macro_data(
        self, data: str, attrs: JirafsMacroAttributes, config: Dict
    ) -> Union[MacroResult, str]:
        return self.execute_macro(data, attrs, config)

    def process_text_data(self, content: str, path: Optional[str] = None) -> str:
        if path is None:
            path = self.ticketfolder.path

        config = {
            "generated_path": path,
        }

        def run_replacement(match_data):
            data = match_data.groupdict()

            try:
                attrs = self.get_attributes(data.get("start", ""))
            except Exception as e:
                raise MacroAttributeError("Unknown Error") from e

            if data.get("end") and "src" in attrs:
                raise MacroContentError(
                    "Macro cannot use block element form while "
                    "also specifying the 'src' attribute.  'src' is "
                    "used for specifying an external file to use as "
                    "macro content."
                )

            body = data.get("content")
            if "src" in attrs:
                with open(
                    os.path.join(self.ticketfolder.path, attrs["src"],), "r"
                ) as inf:
                    body = inf.read()

            result = self.get_processed_macro_data(body, attrs, config)
            self.save()  # Save metadata changes
            return result

        try:
            content = content
            for matcher in self.get_matchers():
                content = matcher.sub(run_replacement, content)
            return content
        except MacroError:
            raise
        except Exception as e:
            raise MacroContentError(
                "Error encountered while running macro %s: %s" % (self.tag_name, e)
            ) from e

    def process_text_data_reversal(self, data: str) -> str:
        try:
            return self.execute_macro_reversal(data)
        except NotImplementedError:
            return data

    def execute_macro_reversal(self, data: str) -> str:
        raise NotImplementedError()

    def execute_macro(
        self, data: str, attrs: JirafsMacroAttributes, config: Dict
    ) -> Union[MacroResult, str]:
        raise NotImplementedError()

    def cleanup(self) -> None:
        raise NotImplementedError()

    def cleanup_pre_process(self) -> None:
        raise NotImplementedError()

    def cleanup_post_process(self) -> None:
        return self.cleanup()

    def _generate_attrs_string(self, attrs: JirafsMacroAttributes) -> str:
        params = []

        for k, v in sorted(attrs.items(), key=lambda e: e[0]):
            quoted_value = json.dumps(v)
            params.append(f"{k}={quoted_value}")

        if params:
            return " " + " ".join(params)

        return ""

    def generate_tag_from_data_and_attrs(
        self, data: str, attrs: JirafsMacroAttributes
    ) -> str:
        attrs_string = self._generate_attrs_string(attrs)

        if "src" in attrs:
            return f"<jirafs:{self.tag_name}{attrs_string} />"
        else:
            return (
                f"<jirafs:{self.tag_name}{attrs_string}>"
                f"{data}"
                f"</jirafs:{self.tag_name}>"
            )


class AutomaticReversalMacroPlugin(MacroPlugin):
    def should_rerender(self, data: str, cache_entry: Dict, config: Dict,) -> bool:
        if cache_entry:
            return False

        return True

    def _generate_metadata_key(
        self, data_hash: str, attrs: JirafsMacroAttributes, config: Dict
    ) -> str:
        hashable_attrs = json.dumps(attrs, sort_keys=True).encode("utf-8")

        return hashlib.sha256(
            b"".join([data_hash.encode("utf-8"), hashable_attrs])
        ).hexdigest()

    def store_cache_entry(
        self,
        replacement: str,
        filenames: List[str],
        attrs: JirafsMacroAttributes,
        data_hash: str,
        config: Dict,
    ) -> None:
        metadata_key = self._generate_metadata_key(data_hash, attrs, config)

        is_temp = config["generated_path"] != self.ticketfolder.path

        self.metadata.setdefault("reversal_cache", {})[metadata_key] = {
            "filenames": filenames,
            "attrs": attrs,
            "replacement": replacement,
            "is_temp": is_temp,
        }

        stored_in_session = self.metadata.setdefault("stored_in_session", [])
        if metadata_key not in stored_in_session:
            stored_in_session.append(metadata_key)

    def find_cache_entry(
        self, data: str, attrs: JirafsMacroAttributes, data_hash: str, config: Dict
    ) -> Dict:
        generated_path = config["generated_path"]
        existing_files = os.listdir(
            generated_path if generated_path else self.ticketfolder.path
        )

        metadata_key = self._generate_metadata_key(data_hash, attrs, config)

        try:
            entry = self.metadata.get("reversal_cache", {})[metadata_key]

            for filename in entry.get("filenames", []):
                if filename not in existing_files:
                    raise ValueError("Metadata references non-existent file")
            return entry
        except KeyError:
            raise ValueError("Metadata not found")

    def cleanup_pre_process(self) -> None:
        # Clear the 'stored_in_session' list; immediately
        # after this method is executed, we'll re-generate
        # this key, and can use that for determining
        # which keys are still in use
        self.metadata["stored_in_session"] = []
        self.metadata["replacements"] = {}
        self.save()

    def cleanup_post_process(self) -> None:
        cache = self.metadata.get("reversal_cache", {})

        known_keys = set(cache.keys())
        accessed_keys = set(self.metadata.get("stored_in_session", []))
        obsolete_keys = known_keys - accessed_keys

        active_local_files: Set[str] = set()
        active_temp_files: Set[str] = set()
        for key in accessed_keys:
            entry = cache[key]
            target = active_local_files
            if entry["is_temp"]:
                target = active_temp_files
            for filename in entry["filenames"]:
                target.add(filename)

        obsolete_local_files: Set[str] = set()
        obsolete_temp_files: Set[str] = set()
        for key in obsolete_keys:
            entry = cache[key]
            target = obsolete_local_files
            if entry["is_temp"]:
                target = obsolete_temp_files
            for filename in cache[key]["filenames"]:
                target.add(filename)
            del cache[key]
            logger.debug(
                "%s: deleting cache key %s", self.entrypoint_name, key,
            )

        # Delete _both_ obsolete local & temp files from the local
        # directory since a file can be present in both
        local_to_delete = (
            obsolete_local_files | obsolete_temp_files
        ) - active_local_files
        existing_local_files = os.listdir(self.ticketfolder.path)

        for filename in local_to_delete:
            if filename in existing_local_files:
                os.unlink(os.path.join(self.ticketfolder.path, filename))
                logger.debug(
                    "%s: deleting obsolete local file %s",
                    self.entrypoint_name,
                    filename,
                )

        temp_to_delete = obsolete_temp_files - active_temp_files
        temp_path = self.ticketfolder.get_path(constants.TEMP_GENERATED_FILES)
        existing_files = os.listdir(temp_path)

        for filename in temp_to_delete:
            if filename in existing_files:
                os.unlink(os.path.join(temp_path, filename))
                logger.debug(
                    "%s: deleting obsolete temp file %s",
                    self.entrypoint_name,
                    filename,
                )

        self.save()

    def execute_macro_reversal(self, data: str) -> str:
        for replacement, original in self.metadata.get("replacements", {}).items():
            data = data.replace(
                replacement,
                self.generate_tag_from_data_and_attrs(
                    original["data"], original["attrs"],
                ),
            )

        return data

    def get_processed_macro_data(
        self, data: str, attrs: JirafsMacroAttributes, config: Dict
    ) -> Union[MacroResult, str]:
        hashed = hashlib.sha256(data.encode("utf-8")).hexdigest()

        filenames = []
        replacement = ""

        try:
            metadata = self.find_cache_entry(data, attrs, hashed, config)
            replacement = metadata["replacement"]
            filenames = metadata["filenames"]
        except ValueError:
            metadata = {}

        if self.should_rerender(data, metadata, config):
            replacement = self.execute_macro(data, attrs, config)
            if isinstance(replacement, MacroResult):
                filenames = replacement.generated_filenames

        assert replacement

        if replacement:
            self.store_cache_entry(
                replacement, filenames, attrs, hashed, config,
            )
            self.metadata.setdefault("replacements", {})[replacement] = {
                "data": data,
                "attrs": attrs,
            }

        return replacement

    def get_replacement(
        self, data: str, attrs: JirafsMacroAttributes, config: Dict
    ) -> Tuple[str, str]:
        raise NotImplementedError()


class ImageMacroPlugin(AutomaticReversalMacroPlugin):
    def get_extension_and_image_data(
        self, data: str, attrs: JirafsMacroAttributes
    ) -> Tuple[str, bytes]:
        raise NotImplementedError()

    def execute_macro(
        self, data: str, attrs: JirafsMacroAttributes, config: Dict
    ) -> MacroResult:
        generated_path = config["generated_path"]
        hashed = hashlib.sha256(data.encode("utf-8")).hexdigest()

        (extension, image_data) = self.get_extension_and_image_data(data, attrs)

        filename = attrs.get("filename", f"{self.tag_name}.{hashed}.{extension}")

        assert isinstance(filename, str)
        file_path = os.path.join(generated_path, filename,)
        with open(file_path, "wb") as outf:
            outf.write(image_data)

        return MacroResult(
            f'!{filename}|alt="jirafs:{self.tag_name}"!',
            generated_filenames=[filename],
        )
