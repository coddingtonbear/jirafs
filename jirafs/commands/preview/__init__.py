from contextlib import closing
import html
import json
import mimetypes
import os
import socket
import time
import traceback
import uuid
import webbrowser
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler

from dateutil.parser import parse

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import jinja2

from jirafs import utils
from jirafs.plugin import CommandPlugin


SESSION_CONNECTED = None


class CountingEventHandler(FileSystemEventHandler):
    counter = 0

    def on_modified(self, event):
        self.counter += 1


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
            searchpath=os.path.join(os.path.dirname(__file__), "templates")
        )
        templates = jinja2.Environment(loader=loader)
        template = templates.get_template(template_name)
        return template.render(context)

    def get_all(self):
        lines = []

        lines.append(
            "Jump to: [#Description] | [New Comment|#NewComment] | [#Comments]"
        )
        lines.append(
            f"h1. {self.folder.issue.key}: {self.get_field_data('summary')}\n\n"
        )
        lines.append(f"h2. Description\n\n")
        description_data = self.get_field_data("description")
        if not description_data.strip():
            lines.append("_Empty_")
        else:
            lines.append(description_data)
        lines.append("\n")
        lines.append(f"h2. New Comment\n\n")
        comment_data = self.get_field_data("new_comment")
        if not comment_data:
            lines.append("_Empty_")
        else:
            lines.append(comment_data)
        lines.append("\n")
        lines.append(f"h2. Comments\n\n")
        lines.append(self.get_comments())

        return "\n".join(lines)

    def get_comments(self):
        lines = []

        for comment in self.folder.issue.fields.comment.comments:
            lines.append(
                "h3. On %s, [~%s] wrote:\n\n"
                % (
                    utils.format_date(self.folder, parse(comment.created)),
                    utils.get_comment_author_display(comment),
                )
            )
            lines.append(comment.body.replace("\r\n", "\n"))
            lines.append("\n")

        return "\n".join(lines)

    def get_field_data(self, dotpath):
        special_fields = {
            "": self.get_all,
            "new_comment": self.folder.get_new_comment,
            "comments": self.get_comments,
        }
        if dotpath in special_fields:
            data = special_fields[dotpath]()
        else:
            data = self.folder.get_field_value_by_dotpath(dotpath)

        return data

    def get_local_file_escaped_field_data(self, dotpath):
        data = self.get_field_data(dotpath)

        if not data:
            return {}, ""

        local_files = os.listdir(self.folder.path)

        referenced_files = utils.find_files_referenced_in_markup(data)

        matches_in_reverse_order = sorted(
            [
                (
                    filename,
                    match_data,
                )
                for filename, match_data in referenced_files.items()
            ],
            key=lambda match: -1 * match[1][2],
        )
        placeholders = {}
        for filename, (full, start, end) in matches_in_reverse_order:
            if filename not in local_files:
                continue

            id = uuid.uuid4()
            placeholder = f"JIRAFS-PLACEHOLDER:{id}"
            placeholders[placeholder] = (filename, full)
            data = "".join([data[:start], placeholder, data[end:]])

        return placeholders, data

    def get_issue_title(self, html_title):
        return f"[{self.folder.issue.key}]: {html_title}"

    def replace_placeholders(self, placeholders, data):
        for placeholder, (filename, full) in placeholders.items():
            if full.startswith("!"):
                data = data.replace(placeholder, f'<img src="files/{filename}" />')
            elif full.startswith("[^"):
                data = data.replace(
                    placeholder, f'<a href="files/{filename}">{filename}</a>'
                )

        return data

    def serve_preview_content(self, dotpath):
        content_type = "text/html"
        placeholders, data = self.get_local_file_escaped_field_data(dotpath)

        html_title = dotpath
        if not html_title:
            html_title = self.get_field_data("summary")

        if isinstance(data, str):
            response = self.get_rendered_template(
                "base.html",
                {
                    "content": self.replace_placeholders(
                        placeholders, get_converted_markup(self.folder, data)
                    ),
                    "title": self.get_issue_title(html_title),
                },
            )
        else:
            response = json.dumps(data)
            content_type = "application/json"
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header("Content-length", len(response))
        self.end_headers()
        self.wfile.write(response.encode("utf-8"))

    def serve_file(self, path):
        if path not in os.listdir(self.folder.path):
            self.send_response(404)
            self.send_header("Content-length", 0)
            self.end_headers()
            return

        with open(os.path.join(self.folder.path, path), "rb") as inf:
            self.send_response(200)
            inf.seek(0, 2)
            content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
            self.send_header("Content-type", content_type)
            self.send_header("Content-length", inf.tell())
            self.end_headers()
            inf.seek(0)
            self.wfile.write(inf.read())

    def send_eventsource_message(self, message):
        self.wfile.write(str(len(message.encode("utf-8")) + 2).encode("utf-8"))
        self.wfile.write("\r\n".encode("utf-8"))
        self.wfile.write(message.encode("utf-8"))
        self.wfile.write("\r\n".encode("utf-8"))

    def serve_eventsource(self):
        event_handler = CountingEventHandler()
        observer = Observer()
        observer.schedule(event_handler, path=self.folder.path, recursive=True)
        observer.start()

        self.send_response(200)
        self.send_header("Transfer-encoding", "chunked")
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()

        while True:
            self.send_eventsource_message(
                "event: counter\r\ndata: %s\r\n" % event_handler.counter
            )
            time.sleep(0.5)

    def do_DELETE(self):
        global SESSION_CONNECTED

        if self.path == "/eventsource/":
            SESSION_CONNECTED = False
            self.send_response(200)
        else:
            self.send_response(404)
        self.end_headers()

    def do_GET(self):
        global SESSION_COUNTER

        self.folder.clear_cache()

        try:
            if self.path.startswith("/files/"):
                self.serve_file(self.path[7:])
            elif self.path == "/eventsource/":
                SESSION_COUNTER = True

                self.serve_eventsource()
            else:
                self.serve_preview_content(self.path[1:].replace("/", "."))
        except BrokenPipeError:
            pass
        except Exception as e:
            self.send_response(500)
            response = self.get_rendered_template(
                "traceback.html",
                {
                    "content": html.escape(traceback.format_exc()),
                    "title": f"Error: {e}",
                },
            )
            self.send_header("Content-type", "text/html")
            self.send_header("Content-length", len(response))
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))


class Command(CommandPlugin):
    """Preview your Jira wiki markup"""

    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"

    def add_arguments(self, parser):
        parser.add_argument(
            "--port",
            "-p",
            help=(
                "Start a webserver on this port; defaults to asking "
                "the operating system for any available port."
            ),
            type=int,
            default=0,
        )
        parser.add_argument(
            "--no-browser",
            "-n",
            action="store_true",
            default=False,
            help=("Do not open a webbrowser to the created webserver."),
        )
        parser.add_argument(
            "--serve-forever",
            "-f",
            action="store_true",
            default=False,
            help=(
                "Do not automatically terminate preview session "
                "when user navigates away from preview URL."
            ),
        )
        parser.add_argument("field_name", nargs="?")

    def handle(self, args, folder, **kwargs):
        return self.cmd(
            folder,
            args.field_name or "",
            port=args.port,
            open_browser=not args.no_browser,
            serve_forever=args.serve_forever,
        )

    def continue_serving(self, serve_forever=True):
        if serve_forever:
            return True

        if SESSION_CONNECTED is None or SESSION_CONNECTED:
            return True

        return False

    def main(
        self,
        folder,
        field_name,
        port=0,
        open_browser=True,
        serve_forever=True,
        **kwargs,
    ):
        if os.path.isfile(field_name) and field_name.endswith(".jira"):
            field_name = field_name.split(".")[0]

        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(("", port))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            port = s.getsockname()[1]
            path = field_name.replace(".", "/")

            IssueRequestHandler.folder = folder
            IssueRequestHandler.get_converted_markup = get_converted_markup

            server = HTTPServer(("", port), IssueRequestHandler)
            server.timeout = 0.1
            print(f"Serving from http://127.0.0.1:{port}")
            print("Press <Ctrl+C> to Exit")

            if open_browser:
                webbrowser.open(f"http://127.0.0.1:{port}/{path}")

            try:
                while self.continue_serving(serve_forever):
                    server.handle_request()
            except KeyboardInterrupt:
                pass
