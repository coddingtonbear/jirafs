import datetime
import os

from jirafs.plugins.compiler_plugin_base import CompilerPluginBase


class RSTtoPDF(CompilerPluginBase):
    PLUGIN_NAME = 'rst_to_pdf'
    INPUT_EXTENSIONS = ['.rst']
    OUTPUT_EXTENSION = '.pdf'

    @classmethod
    def get_command_tests(cls):
        return {
            'pandoc': ['pandoc', '-v'],
            'pdflatex': ['pdflatex', '-v'],
        }

    @classmethod
    def get_command_args(cls, output_path):
        template_path = os.path.join(
            os.path.dirname(__file__),
            'pdf_template.tex',
        )
        version = "Updated %s UTC" % (
            datetime.datetime.utcnow().isoformat()[0:16]
        )

        return [
            'pandoc',
            '--template=%s' % template_path,
            '--variable', 'fontsize=12pt',
            '--variable', 'version=%s' % version,
            '--latex-engine=xelatex',
            '--from=rst',
            '--to=latex',
            '-o',
            output_path
        ]


class RSTtoHTML(CompilerPluginBase):
    PLUGIN_NAME = 'rst_to_html'
    INPUT_EXTENSIONS = ['.rst']
    OUTPUT_EXTENSION = '.html'

    @classmethod
    def get_command_tests(cls):
        return {
            'pandoc': ['pandoc', '-v'],
        }

    @classmethod
    def get_command_args(cls, output_path):
        return [
            'pandoc',
            '--from=rst',
            '--to=html',
            '-o',
            output_path
        ]
