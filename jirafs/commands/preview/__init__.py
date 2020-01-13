from contextlib import closing
import html
import json
import mimetypes
import os
import re
import socket
import time
import traceback
import uuid
import webbrowser
from http.server import ThreadingHTTPServer
from http.server import SimpleHTTPRequestHandler

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import jinja2

from jirafs.plugin import CommandPlugin


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

    def get_comments(self):
        lines = []

        for comment in self.folder.issue.fields.comment.comments:
            lines.append("h3. At %s, %s wrote:\n" % (comment.created, comment.author,))
            lines.append(comment.body.replace("\r\n", "\n"))

        return "\n".join(lines)

    def get_field_data(self, dotpath):
        special_fields = {
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

        local_files = os.listdir(self.folder.path)

        image_finder = re.compile(r"(!(?P<filename>[^!]+)!)")
        to_replace = []
        for match in image_finder.finditer(data):
            filename = match.groupdict()["filename"]
            if "|" in filename:
                filename = filename.split("|", 1)[0]

            if filename in local_files:
                to_replace.append(
                    (filename, match.group(0), match.start(0), match.end(0),)
                )

        placeholders = {}
        for filename, full, start, end in reversed(to_replace):
            id = uuid.uuid4()
            placeholder = f"JIRAFS-PLACEHOLDER:{id}"
            placeholders[placeholder] = (filename, full)
            data = "".join([data[:start], placeholder, data[end:]])

        return placeholders, data

    def replace_placeholders(self, placeholders, data):
        for placeholder, (filename, full) in placeholders.items():
            if full.startswith("!"):
                data = data.replace(placeholder, f'<img src="files/{filename}" />')

        return data

    def serve_preview_content(self, dotpath):
        content_type = "text/html"
        placeholders, data = self.get_local_file_escaped_field_data(dotpath)
        if isinstance(data, str):
            response = self.get_rendered_template(
                "base.html",
                {
                    "content": self.replace_placeholders(
                        placeholders, get_converted_markup(self.folder, data)
                    )
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
        print(path)

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

    def do_GET(self):
        try:
            if self.path.startswith("/files/"):
                self.serve_file(self.path[7:])
            elif self.path == "/eventsource/":
                self.serve_eventsource()
            else:
                self.serve_preview_content(self.path[1:].replace("/", "."))
        except Exception:
            self.send_response(500)
            response = self.get_rendered_template(
                "traceback.html", {"content": html.escape(traceback.format_exc())}
            )
            self.send_header("Content-type", "text/html")
            self.send_header("Content-length", len(response))
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))


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
            default=0,
        )
        parser.add_argument(
            "--no-browser",
            "-n",
            action="store_true",
            default=False,
            help=("Do not open a webbrowser to the created webserver."),
        )
        parser.add_argument("field_name")

    def handle(self, args, folder, **kwargs):
        return self.cmd(
            folder,
            args.field_name,
            output=args.output,
            port=args.port,
            open_browser=not args.no_browser,
        )

    def main(
        self, folder, field_name, output=None, port=0, open_browser=True, **kwargs
    ):
        if output:
            content = get_converted_markup(folder, field_name)
            with open(os.path.expanduser(output), "w") as outf:
                outf.write(content)
                return

        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(("", port))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            port = s.getsockname()[1]
            path = field_name.replace(".", "/")

            IssueRequestHandler.folder = folder
            IssueRequestHandler.get_converted_markup = get_converted_markup

            server = ThreadingHTTPServer(("", port), IssueRequestHandler)
            print(f"Serving from http://127.0.0.1:{port}")
            print("Press <Ctrl+C> to Exit")

            if open_browser:
                webbrowser.open(f"http://127.0.0.1:{port}/{path}")

            while True:
                server.handle_request()

            server.shutdown()
