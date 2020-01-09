import mock

from distutils.version import LooseVersion

from jirafs import utils

from .base import BaseTestCase


class TestStashLocalChanges(BaseTestCase):
    def test_stash_local_changes(self):
        repo = mock.Mock()
        repo.version = 10

        with utils.stash_local_changes(repo):
            pass

        self.assertEqual(
            repo.run_git_command.call_count, 4,
        )

    def test_stash_local_changes_exception(self):
        repo = mock.Mock()
        repo.version = 10

        with self.assertRaises(Exception):
            with utils.stash_local_changes(repo):
                raise Exception()

        self.assertEqual(
            repo.run_git_command.call_count, 4,
        )


class TestParseGitVersion(BaseTestCase):
    @mock.patch("jirafs.utils.subprocess.check_output")
    def test_parse_osx_git_version(self, git_version_output):
        git_version_output.return_value = b"git version 1.8.5.2 (Apple Git-48)"

        actual_version = utils.get_git_version()

        self.assertEqual(actual_version, LooseVersion("1.8.5.2"))

    @mock.patch("jirafs.utils.subprocess.check_output")
    def test_parse_linux_git_version(self, git_version_output):
        git_version_output.return_value = b"git version 1.9.1"

        actual_version = utils.get_git_version()

        self.assertEqual(actual_version, LooseVersion("1.9.1"))
