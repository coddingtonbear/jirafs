import copy
import re

from jirafs import constants, exceptions
from jirafs.readers import GitRevisionReader, WorkingCopyReader


class JiraLinkManager(dict):
    TICKET_MATCHER = re.compile('[A-Za-z]+-\d+')

    def __init__(self):
        self._data = self.load()
        super(JiraLinkManager, self).__init__(self._data)

    @classmethod
    def create(cls, folder, revision=None, path=None):
        if revision and path:
            raise TypeError(
                'You may specify a git revision or a local path; not both.'
            )

        if revision:
            return GitRevisionJiraLinkManager(folder, revision)
        else:
            return WorkingCopyJiraLinkManager(folder, path)

    def load(self):
        return self.get_links_from_string(
            self.get_file_contents(constants.TICKET_LINKS)
        )

    def __sub__(self, other):
        differing = {}

        slf = copy.deepcopy(self)
        for category in ['remote', 'issue']:
            for k, v in other[category].items():
                if k not in slf[category]:
                    if category not in differing:
                        differing[category] = {}
                    differing[category][k] = (v, None, )
                    continue
                l_v = slf[category].pop(k)
                if l_v != v:
                    if category not in differing:
                        differing[category] = {}
                    differing[category][k] = (v, l_v, )

            for k, v in slf[category].items():
                if category not in differing:
                    differing[category] = {}
                differing[category][k] = (None, v)

        return differing

    def get_links_from_string(self, contents):
        links = {
            'remote': {},
            'issue': {},
        }

        for line in contents.split('\n'):
            if not line.startswith('*'):
                continue
            line = line[1:].strip()
            try:
                left, right = line.split(': ')
            except ValueError:
                raise exceptions.IssueValidationError(
                    "Remote links must have a description; format your "
                    "link to {url} like '* Your Title: {url}' "
                    "to continue.".format(
                        url=line.strip()
                    )
                )
            left = left.strip()
            right = right.strip()
            if self.TICKET_MATCHER.match(right):
                right = right.upper()
                links['issue'][right] = {
                    'status': left.lower()
                }
            else:
                links['remote'][right] = {}
                if left:
                    links['remote'][right]['description'] = left

        return links


class GitRevisionJiraLinkManager(GitRevisionReader, JiraLinkManager):
    pass


class WorkingCopyJiraLinkManager(WorkingCopyReader, JiraLinkManager):
    pass
