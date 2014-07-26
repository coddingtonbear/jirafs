from jirafs.plugins.compiler_plugin_base import CompilerPluginBase


class DOTtoPNG(CompilerPluginBase):
    PLUGIN_NAME = 'dot_compiler'
    INPUT_EXTENSIONS = ['.dot']
    OUTPUT_EXTENSION = '.png'

    @classmethod
    def get_command_tests(cls):
        return {
            'graphviz dot': ['dot', '-V'],
        }

    @classmethod
    def get_command_args(cls, output_path):
        return [
            'dot',
            '-Tpng',
            '-o',
            output_path
        ]
