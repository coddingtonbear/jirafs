import json
import os
import shutil
import tempfile

import mock
from mock import patch

from jirafs.plugin import MacroPlugin
from jirafs.utils import run_command_method_with_kwargs

from .base import BaseTestCase


class TestPlugins(BaseTestCase):
    def setUp(self):
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

    def test_load_plugins(self):
        existing_plugins = {
            "alpha": mock.Mock(MAX_VERSION="10.0", MIN_VERSION="0.1"),
            "beta": mock.Mock(MAX_VERSION="10.0", MIN_VERSION="0.1"),
            "delta": mock.Mock(MAX_VERSION="10.0", MIN_VERSION="0.1"),
        }

        with patch("jirafs.utils.get_installed_plugins") as gip:
            gip.return_value = existing_plugins
            with patch.object(self.ticketfolder, "get_config") as config:
                config.return_value = mock.Mock(
                    has_section=mock.Mock(return_value=True),
                    items=mock.Mock(
                        return_value=[
                            ("alpha", "on"),
                            ("delta", "enabled"),
                            ("gamma", "yes"),
                        ]
                    ),
                )
                results = self.ticketfolder.load_plugins()

        self.assertEqual(2, len(results))
        self.assertTrue(existing_plugins["alpha"].called)
        self.assertFalse(existing_plugins["beta"].called)
        self.assertTrue(existing_plugins["delta"].called)

    def test_macroplugin_block_text_data(self):
        class UppercaseMacroPlugin(MacroPlugin):
            TAG_NAME = "uppercase"

            def execute_macro(self, data, attrs, config):
                return data.upper()

        macro = UppercaseMacroPlugin(self.ticketfolder, "uppercase")

        content = """hello <jirafs:uppercase>you</jirafs:uppercase> there!"""
        expected_result = """hello YOU there!"""
        actual_result = macro.process_text_data(content)

        self.assertEqual(expected_result, actual_result)

    def test_macroplugin_void_text_data(self):
        my_name = "Adam"

        class NameMacroPlugin(MacroPlugin):
            TAG_NAME = "name"

            def execute_macro(self, data, attrs, config):
                return my_name

        macro = NameMacroPlugin(self.ticketfolder, "name")

        content = """hello <jirafs:name/>!"""
        expected_result = """hello Adam!"""
        actual_result = macro.process_text_data(content)

        self.assertEqual(expected_result, actual_result)

    def test_nongreedy_processing(self):
        class UppercaseMacroPlugin(MacroPlugin):
            TAG_NAME = "uppercase"

            def execute_macro(self, data, attrs, config):
                return data.upper()

        macro = UppercaseMacroPlugin(self.ticketfolder, "uppercase")

        content = """
            hello <jirafs:uppercase>you</jirafs:uppercase>; how are
            you <jirafs:uppercase>doing
            </jirafs:uppercase>?
        """
        expected_result = """
            hello YOU; how are
            you DOING
            ?
        """
        actual_result = macro.process_text_data(content)

        self.assertEqual(expected_result, actual_result)

    def test_attribute_extraction_block(self):
        class TestMacroPlugin(MacroPlugin):
            TAG_NAME = "test"

            def execute_macro(self, data, attrs, config):
                return json.dumps(attrs)

        macro = TestMacroPlugin(self.ticketfolder, "test")

        content = """<jirafs:test alpha="AL''\\"\\tPHA" beta=2 gamma=True epsilon='bloop"\\''>
            beep
            </jirafs:test>
        """

        expected_result = {
            "alpha": "AL''\"\tPHA",
            "beta": 2.0,
            "gamma": True,
            "epsilon": "bloop\"'",
        }
        self.assertEqual(expected_result, json.loads(macro.process_text_data(content)))

    def test_attribute_extraction_void(self):
        class TestMacroPlugin(MacroPlugin):
            TAG_NAME = "test"

            def execute_macro(self, data, attrs, config):
                return json.dumps(attrs)

        macro = TestMacroPlugin(self.ticketfolder, "test")

        content = """
            <jirafs:test alpha="AL''\\"\\tPHA" beta=2 gamma=True epsilon='bloop"\\''/>
        """

        expected_result = {
            "alpha": "AL''\"\tPHA",
            "beta": 2.0,
            "gamma": True,
            "epsilon": "bloop\"'",
        }
        self.assertEqual(expected_result, json.loads(macro.process_text_data(content)))

    def test_multiline_attribute_extraction(self):
        class TestMacroPlugin(MacroPlugin):
            TAG_NAME = "test"

            def execute_macro(self, data, attrs, config):
                return json.dumps(attrs)

        macro = TestMacroPlugin(self.ticketfolder, "test")

        content = """
            <jirafs:test
                alpha="AL''\\"PHA"
                beta=2
                gamma=True
                epsilon='bloop"\\''
            />
        """

        expected_result = {
            "alpha": "AL''\"PHA",
            "beta": 2.0,
            "gamma": True,
            "epsilon": "bloop\"'",
        }
        self.assertEqual(expected_result, json.loads(macro.process_text_data(content)))

    def test_macroplugin_block_text_data_double(self):
        class CounterMacroPlugin(MacroPlugin):
            TAG_NAME = "counter"

            def execute_macro(self, data, attrs, config):
                return str(int(attrs["counter"])) + ":" + data

        macro = CounterMacroPlugin(self.ticketfolder, "counter")

        content = """
        Start
        <jirafs:counter counter=0>Zero</jirafs:counter>
        Middle
        <jirafs:counter counter=1>One</jirafs:counter>
        End
        """
        expected_result = """
        Start
        0:Zero
        Middle
        1:One
        End
        """
        actual_result = macro.process_text_data(content)

        self.assertEqual(expected_result, actual_result)

    def tearDown(self):
        shutil.rmtree(self.root_folder)
