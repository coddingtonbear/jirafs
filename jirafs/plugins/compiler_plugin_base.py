import os
import shutil
import subprocess
import tempfile

import six

from jirafs.plugin import Plugin, PluginOperationError, PluginValidationError


class CompilerPluginBase(Plugin):
    MIN_VERSION = '0.8.3'
    MAX_VERSION = '0.99.99'

    def alter_file_upload(self, info):
        metadata = self.get_metadata()

        filename, file_object = info

        basename, extension = os.path.splitext(filename)
        if extension not in self.INPUT_EXTENSIONS:
            return filename, file_object
        new_filename = basename + self.OUTPUT_EXTENSION

        tempdir = tempfile.mkdtemp()
        temp_file_path = os.path.join(
            tempdir,
            new_filename,
        )

        proc = subprocess.Popen(
            self.get_command_args(temp_file_path),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = proc.communicate(file_object.read())

        if proc.returncode:
            raise PluginOperationError(
                "%s encountered an error while compiling from %s to %s: %s" % (
                    self.plugin_name,
                    extension,
                    self.OUTPUT_EXTENSION,
                    stderr,
                )
            )

        with open(temp_file_path, 'rb') as temp_output:
            content = six.BytesIO(temp_output.read())
        shutil.rmtree(tempdir)

        filename_map = metadata.get('filename_map', {})
        filename_map[new_filename] = filename
        metadata['filename_map'] = filename_map
        self.set_metadata(metadata)

        return new_filename, content

    @classmethod
    def validate(cls):
        for req_name, args in cls.get_command_tests().items():
            try:
                subprocess.check_call(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except (subprocess.CalledProcessError, IOError, OSError):
                raise PluginValidationError(
                    "%s requires %s to be installed." % (
                        cls.PLUGIN_NAME,
                        req_name,
                    )
                )

