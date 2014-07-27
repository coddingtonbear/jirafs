import json

from verlib import NormalizedVersion

from . import __version__


class PluginError(Exception):
    pass


class PluginValidationError(PluginError):
    pass


class PluginOperationError(PluginError):
    pass


class Plugin(object):
    MIN_VERSION = None
    MAX_VERSION = None

    def __init__(self, ticketfolder, plugin_name, **kwargs):
        self.ticketfolder = ticketfolder
        self.plugin_name = plugin_name

    def validate(self):
        if not self.MIN_VERSION or not self.MAX_VERSION:
            raise PluginValidationError(
                "Minimum and maximum version numbers not specified."
            )

        min_version = NormalizedVersion(self.MIN_VERSION)
        max_version = NormalizedVersion(self.MAX_VERSION)
        curr_version = NormalizedVersion(__version__)
        if not min_version <= curr_version <= max_version:
            raise PluginValidationError(
                "Plugin '%s' is not compatible with version %s of Jirafs; "
                "minimum version: %s; maximum version %s.",
                (
                    self.plugin_name,
                    __version__,
                    self.MIN_VERSION,
                    self.MAX_VERSION,
                ),
            )

        return True

    @property
    def metadata_filename(self):
        return self.ticketfolder.get_metadata_path(
            'plugin_meta',
            '%s.json' % self.plugin_name,
        )

    def get_configuration(self):
        config = self.ticketfolder.get_config()
        if config.has_section(self.plugin_name):
            return dict(config.items(self.plugin_name))
        return {}

    def get_metadata(self):
        try:
            with open(self.metadata_filename, 'r') as _in:
                return json.loads(_in.read())
        except (IOError, OSError):
            return {}

    def set_metadata(self, data):
        with open(self.metadata_filename, 'w') as out:
            out.write(
                json.dumps(
                    data,
                    indent=4,
                    sort_keys=True,
                )
            )
