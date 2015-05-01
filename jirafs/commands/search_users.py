from __future__ import print_function

import json

from prettytable import PrettyTable

from jirafs import utils
from jirafs.plugin import CommandPlugin
from jirafs.ticketfolder import TicketFolder


class Command(CommandPlugin):
    """Search for users matching the specified search term"""
    MIN_VERSION = '1.0a1'
    MAX_VERSION = '1.99.99'
    AUTOMATICALLY_INSTANTIATE_FOLDER = False

    def handle(self, args, jira, path, parser, **kwargs):
        search_term = ' '.join(args.terms)

        try:
            tf = TicketFolder(path, jira)
            jira_client = tf.jira
        except IOError:
            jira_client = jira(
                utils.get_default_jira_server()
            )

        users = jira_client.search_users(search_term)

        if args.json:
            print(
                json.dumps(
                    [u.raw for u in users]
                )
            )
            return

        table = PrettyTable(['Name', 'Username', 'Email Address', 'Time Zone'])
        table.align = 'l'
        for user in users:
            table.add_row(
                [
                    user.displayName,
                    user.name,
                    user.emailAddress,
                    user.timeZone
                ]
            )
        print(table)

    def add_arguments(self, parser):
        parser.add_argument('terms', nargs='*')
        parser.add_argument('--json', default=False, action='store_true')
