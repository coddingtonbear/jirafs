import os
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys
import uuid

from jirafs import __version__ as version_string


requirements_path = os.path.join(
    os.path.dirname(__file__),
    'requirements.txt',
)
try:
    from pip.req import parse_requirements
    requirements = [
        str(req.req) for req in parse_requirements(
            requirements_path,
            session=uuid.uuid1()
        )
    ]
except ImportError:
    requirements = []
    with open(requirements_path, 'r') as in_:
        requirements = [
            req for req in in_.readlines()
            if not req.startswith('-')
            and not req.startswith('#')
        ]


class Tox(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import tox
        errno = tox.cmdline(self.test_args)
        sys.exit(errno)


setup(
    name='jirafs',
    version=version_string,
    url='https://github.com/coddingtonbear/jirafs',
    description=(
        'Edit Jira issues as text files locally.'
    ),
    author='Adam Coddington',
    author_email='me@adamcoddington.net',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
    ],
    install_requires=requirements,
    tests_require=['tox', 'behave>=1.2.5'],
    cmdclass = {'test': Tox},
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'jirafs = jirafs.cmdline:main'
        ],
        'jirafs_commands': [
            'fetch = jirafs.commands.fetch:Command',
            'pull = jirafs.commands.pull:Command',
            'merge = jirafs.commands.merge:Command',
            'commit = jirafs.commands.commit:Command',
            'push = jirafs.commands.push:Command',
            'git = jirafs.commands.git:Command',
            'log = jirafs.commands.log:Command',
            'debug = jirafs.commands.debug:Command',
            'plugins = jirafs.commands.plugins:Command',
            'status = jirafs.commands.status:Command',
            'clone = jirafs.commands.clone:Command',
            'open = jirafs.commands.open:Command',
            'diff = jirafs.commands.diff:Command',
            'config = jirafs.commands.config:Command',
            'transition = jirafs.commands.transition:Command',
            'field = jirafs.commands.field:Command',
            'setfield = jirafs.commands.setfield:Command',
            'subtask = jirafs.commands.subtask:Command',
            'assign = jirafs.commands.assign:Command',
            'search_users = jirafs.commands.search_users:Command',
            'create = jirafs.commands.create:Command',
            'submit = jirafs.commands.submit:Command',
            'match = jirafs.commands.match:Command',
            'build = jirafs.commands.build:Command',
        ]
    },
)
