import os
import shutil
import tempfile

import mock
from mock import patch

from jirafs.ticketfolder import TicketFolder

from .base import BaseTestCase


class TestPlugins(BaseTestCase):
    def setUp(self):
        self.arbitrary_ticket_number = 'ALPHA-123'
        self.root_folder = tempfile.mkdtemp()
        self.mock_jira = mock.MagicMock()
        self.mock_jira.issue.return_value = self.rehydrate_issue(
            'basic.issue.json'
        )
        self.mock_get_jira = lambda _, config=None: self.mock_jira

        with patch(
            'jirafs.ticketfolder.TicketFolder.get_remotely_changed'
        ) as get_remotely_changed:
            get_remotely_changed.return_value = []
            self.ticketfolder = TicketFolder.clone(
                ticket_url='http://arbitrary.com/browse/ALPHA-123',
                jira=self.mock_get_jira,
                path=os.path.join(
                    self.root_folder,
                    self.arbitrary_ticket_number,
                ),
            )

    def test_load_plugins(self):
        existing_plugins = {
            'alpha': mock.Mock(),
            'beta': mock.Mock(),
            'delta': mock.Mock(),
        }

        with patch('jirafs.utils.get_installed_plugins') as gip:
            gip.return_value = existing_plugins
            with patch.object(self.ticketfolder, 'get_config') as config:
                config.return_value = mock.Mock(
                    has_section=mock.Mock(return_value=True),
                    items=mock.Mock(
                        return_value=[
                            ('alpha', 'on'),
                            ('delta', 'enabled'),
                            ('gamma', 'off'),
                        ]
                    )
                )
                results = self.ticketfolder.load_plugins()

        self.assertEquals(2, len(results))
        existing_plugins['alpha'].assert_called_with(self.ticketfolder)
        self.assertFalse(existing_plugins['beta'].called)
        existing_plugins['delta'].assert_called_with(self.ticketfolder)

    def tearDown(self):
        shutil.rmtree(self.root_folder)
