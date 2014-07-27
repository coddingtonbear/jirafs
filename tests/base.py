import json
import os
from unittest import TestCase

from jira.resources import Issue


class BaseTestCase(TestCase):
    def get_asset_path(self, filename):
        return os.path.join(
            os.path.dirname(__file__),
            'assets',
            filename
        )

    def get_asset_contents(self, filename, mode='r'):
        path = self.get_asset_path(filename)

        with open(path, mode) as r:
            return r.read()

    def rehydrate_issue(self, filename):
        stored = json.loads(self.get_asset_contents(filename))
        return Issue(
            stored['options'],
            None,
            stored['raw'],
        )

    def get_empty_status(self):
        return {
            'ready': {
                'files': [],
                'fields': {},
                'new_comment': '',
            },
            'uncommitted': {
                'files': [],
                'fields': {},
                'new_comment': '',
            },
            'local_uncommitted': {
                'files': [],
            },
            'up_to_date': True,
        }
