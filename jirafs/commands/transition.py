from collections import OrderedDict

from six.moves import input

from jirafs.plugin import CommandPlugin
from jirafs.utils import run_command_method_with_kwargs


class Command(CommandPlugin):
    """ Transition the current issue into a new state """
    MIN_VERSION = '1.0'
    MAX_VERSION = '1.99.99'

    def handle(self, args, folder, **kwargs):
        state = self.get_state_from_string(folder, args.state)
        if state is None:
            state = self.get_state_from_user(folder)
        return self.transition(folder, state)

    def transition(self, folder, state_id):
        folder.jira.transition_issue(folder.issue, state_id)
        pull_result = run_command_method_with_kwargs('pull', folder=folder)
        return pull_result[1]

    def get_transition_dict(self, folder):
        if not hasattr(self, '_transition_dict'):
            value = folder.jira.transitions(folder.issue)
            self._transition_dict = OrderedDict(
                (v['id'], v) for v in value
            )
        return self._transition_dict

    def get_state_from_string(self, folder, value):
        options = self.get_transition_dict(folder)

        if value is None:
            return None

        # If it's a dictionary key, just go for it.
        if value in options:
            return value

        # But, if it isn't, this'll be a bit less efficient
        for k, v in options.items():
            if value.upper() == v['name'].upper():
                return k

        return None

    def get_state_from_user(self, folder):
        options = self.get_transition_dict(folder)
        response = None
        while(response is None):
            for option_id, option_data in options.items():
                print(
                    "%s: %s (%s)" % (
                        option_id,
                        option_data['name'],
                        option_data.get('to', {}).get('description', ''),
                    )
                )

            print('')
            response = self.get_state_from_string(
                folder,
                input("Please select a state from the above options: ")
            )

        return response

    def add_arguments(self, parser):
        parser.add_argument(
            'state',
            default=None,
            nargs='?'
        )
