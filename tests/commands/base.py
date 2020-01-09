import os
import tempfile

import mock
from mock import patch

from jirafs.utils import run_command_method_with_kwargs

from ..base import BaseTestCase


class BaseCommandTestCase(BaseTestCase):
    def setUp(self):
        super(BaseCommandTestCase, self).setUp()
        self.arbitrary_ticket_number = "ALPHA-123"
        self.root_folder = tempfile.mkdtemp()
        self.mock_jira = mock.MagicMock()
        self.mock_jira.issue.return_value = self.rehydrate_issue("basic.issue.json")
        self.mock_get_jira = lambda _, config=None: self.mock_jira

        with patch(
            "jirafs.ticketfolder.TicketFolder.get_remotely_changed"
        ) as get_remotely_changed:
            get_remotely_changed.return_value = []
            self.ticketfolder = run_command_method_with_kwargs(
                "clone",
                url="http://arbitrary.com/browse/ALPHA-123",
                jira=self.mock_get_jira,
                path=os.path.join(self.root_folder, self.arbitrary_ticket_number,),
            )
