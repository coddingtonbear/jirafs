import mock

from jirafs import utils

from .base import BaseTestCase


class TestStashLocalChanges(BaseTestCase):
    def test_stash_local_changes(self):
        repo = mock.Mock()
        repo.version = 10

        with utils.stash_local_changes(repo):
            pass

        self.assertEqual(
            repo.run_git_command.call_count,
            3,
        )
        repo.run_git_command.assert_has_calls([
            mock.call('stash', '--include-untracked', failure_ok=True),
            mock.call('stash', 'apply', failure_ok=True),
            mock.call('stash', 'drop', failure_ok=True),
        ])

    def test_stash_local_changes_exception(self):
        repo = mock.Mock()
        repo.version = 10

        with self.assertRaises(Exception):
            with utils.stash_local_changes(repo):
                raise Exception()

        self.assertEqual(
            repo.run_git_command.call_count,
            3,
        )
        repo.run_git_command.assert_has_calls([
            mock.call('stash', '--include-untracked', failure_ok=True),
            mock.call('stash', 'apply', failure_ok=True),
            mock.call('stash', 'drop', failure_ok=True),
        ])
