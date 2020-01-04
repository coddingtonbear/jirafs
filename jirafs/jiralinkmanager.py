import copy
import re

from jirafs import constants, exceptions
from jirafs.readers import GitRevisionReader, WorkingCopyReader


class JiraLinkManager(dict):
    TICKET_MATCHER = re.compile("[A-Za-z]+-\d+")

    def __init__(self, data, prepared=False):
        if not prepared:
            self._data = self.get_fields_from_string(data)
        else:
            self._data = data
        super(JiraLinkManager, self).__init__(self._data)

    @classmethod
    def create(cls, folder, revision=None, path=None):
        if revision and path:
            raise TypeError("You may specify a git revision or a local path; not both.")

        if revision:
            return GitRevisionJiraLinkManager(folder, revision)
        else:
            return WorkingCopyJiraLinkManager(folder, path)

    def __sub__(self, other):
        differing = {}

        slf = {}
        for category in ["remote", "issue"]:
            slf[category] = self[category].copy()
            for k, v in other[category].items():
                if k not in slf[category]:
                    if category not in differing:
                        differing[category] = {}
                    differing[category][k] = (
                        v,
                        None,
                    )
                    continue
                l_v = slf[category].pop(k)
                if l_v != v:
                    if category not in differing:
                        differing[category] = {}
                    differing[category][k] = (
                        v,
                        l_v,
                    )

            for k, v in slf[category].items():
                if category not in differing:
                    differing[category] = {}
                differing[category][k] = (None, v)

        return differing

    def get_links_from_string(self, contents):
        links = {
            "remote": {},
            "issue": {},
        }

        for line in contents.split("\n"):
            if not line.startswith("*"):
                continue
            line = line[1:].strip()
            try:
                left, right = line.split(": ", 1)
            except ValueError:
                raise exceptions.IssueValidationError(
                    u"Remote links must have a description; format your "
                    u"link to {url} like '* Your Title: {url}' "
                    u"to continue.".format(url=line.strip())
                )
            left = left.strip()
            right = right.strip()
            if self.TICKET_MATCHER.match(right):
                right = right.upper()
                links["issue"][right] = {"status": left.lower()}
            else:
                links["remote"][right] = {}
                if left:
                    links["remote"][right]["description"] = left

        return links


class AutomaticJiraLinkManager(JiraLinkManager):
    def __init__(self):
        data = self.load()
        super(AutomaticJiraLinkManager, self).__init__(data, prepared=True)

    def load(self):
        return self.get_links_from_string(
            self.get_file_contents(constants.TICKET_LINKS)
        )

    def get_file_contents(self, path):
        raise NotImplemented()


class GitRevisionJiraLinkManager(GitRevisionReader, AutomaticJiraLinkManager):
    pass


class WorkingCopyJiraLinkManager(WorkingCopyReader, AutomaticJiraLinkManager):
    pass
