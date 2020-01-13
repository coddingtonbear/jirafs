import json

from jirafs.plugin import CommandPlugin, CommandResult


class Command(CommandPlugin):
    """ Get the status of the current ticketfolder """

    TRY_SUBFOLDERS = True
    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"

    def handle(self, args, folder, **kwargs):
        return self.cmd(folder, args.format)

    def add_arguments(self, parser):
        parser.add_argument("--format", default="text", choices=["text", "json"])

    def main(self, folder, output_format="text"):
        return folder.status()

    def cmd(self, folder, output_format="text"):
        status = self.main(folder)
        if output_format == "json":
            return self.status_json(folder, status)
        return self.status_text(folder, status)

    def status_json(self, folder, status):
        result = CommandResult()
        result = result.add_line(json.dumps(status), no_format=True)
        return result

    def has_changes(self, section, *keys):
        if not keys:
            keys = ["files", "deleted", "fields", "new_comment", "links"]
        for key in keys:
            if key in section and section[key]:
                return True

    def status_text(self, folder, folder_status):
        result = CommandResult()

        result = result.add_line(
            u"On ticket {ticket} ({url})",
            ticket=folder.ticket_number,
            url=folder.cached_issue.permalink(),
        )
        if not folder_status["up_to_date"]:
            result = result.add_line(
                "{t.magenta}Warning: unmerged upstream changes exist; "
                "run `jirafs merge` to merge them into your local copy."
                "{t.normal}"
            )

        printed_changes = False
        ready = folder_status["ready"]
        if self.has_changes(ready):
            printed_changes = True
            result = result.add_line("")
            result = result.add_line(
                "Ready for upload; use `jirafs push` to update JIRA."
            )
            result = self.format_field_changes(ready, "green", result=result)

        staged = folder_status["uncommitted"]
        if self.has_changes(staged):
            printed_changes = True
            result = result.add_line("")
            result = result.add_line(
                "Uncommitted changes: use `jirafs submit` to submit changes "
                "to JIRA, or use `jirafs commit` to commit your changes "
                "for submission during a later `jirafs push`."
            )
            result = self.format_field_changes(staged, "red", result=result)

        local_uncommitted = folder_status["local_uncommitted"]
        if self.has_changes(local_uncommitted, "files"):
            printed_changes = True
            result = result.add_line("")
            result = result.add_line(
                "Uncommitted changes prevented from being sent to JIRA "
                "because they match at least one of the patterns in your "
                "`.jirafs_local` file; use `jirafs commit` to track these "
                "changes."
            )
            result = result.add_line(
                "Note: these files will {t.bold}not{t.normal} "
                "be uploaded to JIRA even after being committed."
            )
            result = self.format_field_changes(
                local_uncommitted, "cyan", no_upload=True, result=result,
            )

        if not printed_changes:
            result = result.add_line("No changes found")
        else:
            result = result.add_line("")
            result = result.add_line(
                "For more detail about these changes, run `jirafs diff`"
            )

        return result

    def format_field_changes(self, changes, color, no_upload=False, result=None):
        if result is None:
            result = CommandResult()

        for filename in changes.get("files", []):
            result = result.add_line(
                u"\t{t.%s}{filename}{t.normal} {post_message}" % color,
                filename=filename,
                post_message=(
                    "(track in repository)" if no_upload else "(upload attachment)"
                ),
            )
        for filename in changes.get("deleted", []):
            result = result.add_line(
                u"\t{t.%s}{filename}{t.normal} {post_message}" % color,
                filename=filename,
                post_message="(deleted)",
            )
        for link, data in changes.get("links", {}).get("remote", {}).items():
            orig = data[0]
            new = data[1]
            if new is not None:
                if new.get("description"):
                    description = new["description"]
                else:
                    description = "(Untitled)"

                result = result.add_line(
                    u"\t{t.%s}{description}: "
                    u"{link}{t.normal} {post_message}" % (color,),
                    description=description,
                    link=link,
                    post_message=(
                        " (changed remote link)" if orig else " (new remote link)"
                    ),
                )
            else:
                if orig.get("description"):
                    description = orig["description"]
                else:
                    description = "(Untitled)"

                result = result.add_line(
                    u"\t{t.%s}{description}: "
                    u"{link}{t.normal} {post_message}" % (color,),
                    description=description,
                    link=link,
                    post_message="(removed remote link)",
                )
        for link, data in changes.get("links", {}).get("issue", {}).items():
            orig = data[0]
            new = data[1]
            if new is not None:
                if new.get("status"):
                    status = new["status"]
                else:
                    status = "(Untitled)"
                result = result.add_line(
                    u"\t{t.%s}{status}: {link}{t.normal} {post_message}" % (color),
                    status=status.title(),
                    link=link,
                    post_message=(
                        "(changed issue link)" if orig else "(new issue link)"
                    ),
                )
            else:
                if orig.get("status"):
                    status = orig["status"]
                else:
                    status = "(Untitled)"

                result = result.add_line(
                    "\t{t.%s}{status}: {link}{t.normal} {post_message}" % (color,),
                    status=status.title(),
                    link=link,
                    post_message="(removed issue link)",
                )
        for field, value_set in changes.get("fields", {}).items():
            result = result.add_line("\t{t.%s}{field}{t.normal}" % color, field=field,)
        if changes.get("new_comment", ""):
            result = result.add_line("\t{t.%s}[New Comment]{t.normal}" % color)

        return result
