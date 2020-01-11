from contextlib import closing
import json
import os
import socket
import webbrowser
from http.server import ThreadingHTTPServer
from http.server import SimpleHTTPRequestHandler

import jinja2

from jirafs.exceptions import JirafsError
from jirafs.plugin import CommandPlugin


def get_converted_markup(folder, data):
    url = folder.jira._get_url("../1.0/render")
    response = folder.jira._session.post(
        url,
        headers={"Accept": "text/html, */*; q=0.01"},
        data=json.dumps(
            {
                "issueKey": folder.ticket_number,
                "rendererType": "atlassian-wiki-renderer",
                "unrenderedMarkup": data,
            }
        ),
    )

    return response.text


class IssueRequestHandler(SimpleHTTPRequestHandler):
    folder = None
    field_data = None

    def get_rendered_template(self, template_name, context):
        loader = jinja2.FileSystemLoader(
            searchpath=os.path.join(
                os.path.dirname(__file__),
                "templates"
            )
        )
        templates = jinja2.Environment(loader=loader)
        template = templates.get_template(template_name)
        return template.render(context)

    def get_comments(self):
        lines = []

        for comment in self.folder.issue.fields.comment.comments:
            lines.append(
                "h3. At %s, %s wrote:\n" % (
                    comment.created,
                    comment.author,
                )
            )
            lines.append(comment.body.replace("\r\n", "\n"))

        return '\n'.join(lines)

    def get_field_data(self, dotpath):
        special_fields = {
            "new_comment": self.folder.get_new_comment,
            "comments": self.get_comments
        }
        if dotpath in special_fields:
            data = special_fields[dotpath]()
        else:
            data = self.folder.get_field_value_by_dotpath(dotpath)

        return data

    def serve_preview_content(self, dotpath):
        self.send_response(200)

        data = self.get_field_data(dotpath)

        if isinstance(data, str):
            self.send_header('Content-type', 'text/html')
            response = self.get_rendered_template(
                "base.html",
                {
                    "content": get_converted_markup(
                        self.folder,
                        self.get_field_data(dotpath)
                    )
                }
            )
        else:
            self.send_header("Content-type", "application/json")
            response = json.dumps(data)

        self.send_header('Content-length', len(response))
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def do_GET(self):
        try:
            self.serve_preview_content(self.path[1:].replace('/', '.'))
        except JirafsError:
            # self.serve_static_content(self.path)
            self.send_response(404)
            self.send_header('Content-length', 0)
            self.end_headers()


class Command(CommandPlugin):
    """ Preview your Jira wiki markup """

    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            "-o",
            help=(
                "Instead of opening a preview in your browser, "
                "write HTML output to the specified path."
            ),
        )
        parser.add_argument(
            "--port",
            "-p",
            help=(
                "Start a webserver on this port; defaults to asking "
                "the operating system for any available port."
            ),
            type=int,
            default=0
        )
        parser.add_argument(
            "--no-browser",
            "-n",
            action="store_true",
            default=False,
            help=(
                "Do not open a webbrowser to the created webserver."
            )
        )
        parser.add_argument("field_name")

    def handle(self, args, folder, **kwargs):
        return self.cmd(
            folder,
            args.field_name,
            output=args.output,
            port=args.port,
            open_browser=not args.no_browser
        )

    def main(
        self,
        folder,
        field_name,
        output=None,
        port=0,
        open_browser=True,
        **kwargs
    ):
        if output:
            content = get_converted_markup(folder, field_name)
            with open(os.path.expanduser(output), "w") as outf:
                outf.write(content)
                return

        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(('', port))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            port = s.getsockname()[1]
            path = field_name.replace('.', '/')

            IssueRequestHandler.folder = folder
            IssueRequestHandler.get_converted_markup = get_converted_markup

            server = ThreadingHTTPServer(('', port), IssueRequestHandler)
            print(f"Serving from http://127.0.0.1:{port}")
            print("Press <Ctrl+C> to Exit")

            if open_browser:
                webbrowser.open(f'http://127.0.0.1:{port}/{path}')

            while True:
                server.handle_request()

            server.shutdown()
