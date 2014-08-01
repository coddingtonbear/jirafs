import os
import re

import six
from six.moves.urllib import parse

from jirafs import exceptions, utils
from jirafs.plugin import CommandPlugin
from jirafs.ticketfolder import TicketFolder


class Command(CommandPlugin):
    """ Clone a new ticketfolder for the specified ticket URL"""
    NAME = 'clone'

    def handle(self, args, jira, path):
        ticket_url = args.ticket_url[0]
        ticket_url_parts = parse.urlparse(ticket_url)
        if not ticket_url_parts.netloc:
            default_server = utils.get_default_jira_server()
            ticket_url = parse.urljoin(
                default_server,
                'browse/' + ticket_url + '/'
            )
        path = args.path[0] if args.path else None

        self.clone(path, ticket_url, jira)

    def clone(self, path, ticket_url, jira):
        match = re.match('.*\/browse\/(\w+-\d+)\/?', ticket_url)
        if not match:
            raise exceptions.JirafsError(
                "\'%s\' is not a valid JIRA ticket URL." % (
                    ticket_url
                )
            )
        if not path:
            path = match.group(1)
        path = os.path.realpath(path)
        os.mkdir(path)
        folder = TicketFolder.initialize_ticket_folder(ticket_url, path, jira)
        commands = utils.get_installed_commands()
        commands['pull']().pull(folder)
        return folder

    def add_arguments(self, parser):
        parser.add_argument(
            'ticket_url',
            nargs=1,
            type=six.text_type
        )
        parser.add_argument(
            'path',
            nargs='*',
            type=six.text_type,
        )
