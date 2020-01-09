import json
import os
import tempfile
import webbrowser

from jirafs.plugin import CommandPlugin


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
        parser.add_argument("field_name")

    def handle(self, args, folder, **kwargs):
        return self.cmd(folder, args.field_name, output=args.output)

    def main(self, folder, field_name, output=None, **kwargs):
        special_fields = {
            "new_comment": folder.get_new_comment,
            "links": folder.get_links,
            "fields": folder.get_fields,
        }
        if field_name in special_fields:
            data = special_fields[field_name]()
        else:
            data = folder.get_field_value_by_dotpath(field_name)

        url = folder.jira._get_url("../1.0/render")
        response = folder.jira._session.post(
            url,
            headers={"Accept": "text/html, */*; q=0.01",},
            data=json.dumps(
                {
                    "issueKey": folder.ticket_number,
                    "rendererType": "atlassian-wiki-renderer",
                    "unrenderedMarkup": data,
                }
            ),
        )

        if output:
            with open(os.path.expanduser(output), "o") as outf:
                outf.write(response.text)
        else:
            with tempfile.NamedTemporaryFile("w", suffix=".html") as outf:
                outf.write(
                    """
                    <html>
                        <style type="text/css">
                            body {
                                font-family: sans-serif;
                            }
                            table {
                                border-collapse: collapse;
                            }
                            table, th, td {
                                border: 1px solid black;
                            }
                        </style>
                        <body>
                """
                )
                outf.write(response.text)
                outf.write(
                    """
                        </body>
                    </html>
                """
                )
                outf.flush()

                webbrowser.open(outf.name)

                input("Press <Enter> to continue")
