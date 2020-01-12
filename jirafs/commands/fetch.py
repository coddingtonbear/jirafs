import io
import json
import os
import textwrap

from jirafs import constants, utils
from jirafs.plugin import CommandPlugin


class Command(CommandPlugin):
    """ Fetch remote changes """

    TRY_SUBFOLDERS = True
    RUN_FOR_SUBTASKS = False
    MIN_VERSION = "2.0.0"
    MAX_VERSION = "3.0.0"

    def get_field_map(self, folder):
        fields = {}
        for field in folder.jira.fields():
            fields[field["id"]] = field["name"]

        return fields

    def main(self, folder, **kwargs):
        folder.clear_cache()

        file_meta = folder.get_remote_file_metadata(shadow=True)
        original_hash = folder.run_git_command("rev-parse", "jira")

        for filename in folder.get_remotely_changed():
            for attachment in folder.issue.fields.attachment:
                if attachment.filename == filename:
                    folder.log(
                        'Download file "%s"', (attachment.filename,),
                    )
                    content = io.BytesIO(attachment.get())
                    save_path = folder.get_shadow_path(filename)
                    with open(save_path, "wb") as save_file:
                        content.seek(0)
                        save_file.write(content.read())
                        file_meta[filename] = attachment.created

        folder.set_remote_file_metadata(file_meta, shadow=True)

        field_map = self.get_field_map(folder)
        detail_path = folder.get_shadow_path(constants.TICKET_DETAILS)
        with io.open(detail_path, "w", encoding="utf-8") as dets:
            for field in sorted(folder.issue.raw["fields"].keys()):
                value = folder.issue.raw["fields"][field]
                if isinstance(value, str):
                    value = value.replace("\r\n", "\n").strip()
                elif value is None:
                    value = ""
                elif field in constants.NO_DETAIL_FIELDS:
                    continue

                if not isinstance(value, str):
                    value = json.dumps(
                        value, sort_keys=True, indent=4, ensure_ascii=False
                    )
                else:
                    value = folder.process_macro_reversals(value)

                if field in constants.FILE_FIELDS:
                    # Write specific fields to their own files without
                    # significant alteration

                    file_field_path = folder.get_shadow_path(
                        constants.TICKET_FILE_FIELD_TEMPLATE
                    ).format(field_name=field)
                    with io.open(
                        file_field_path, "w", encoding="utf-8"
                    ) as file_field_file:
                        file_field_file.write(str(value))
                        file_field_file.write("\n")  # For unix' sake
                else:
                    # Normal fields, though, just go into the standard
                    # fields file.
                    if value is None:
                        continue
                    elif field in constants.NO_DETAIL_FIELDS:
                        continue

                    human_readable = field_map.get(field)
                    dets.write("* %s (%s):\n" % (human_readable, field))
                    for line in value.replace("\r\n", "\n").split("\n"):
                        dets.write("    %s\n" % line)

        links_path = folder.get_shadow_path(constants.TICKET_LINKS)
        with io.open(links_path, "w", encoding="utf-8") as links_handle:
            # Write issue links
            for link in folder.issue.fields.issuelinks:
                category = "outward"
                if "inwardIssue" in link.raw:
                    category = "inward"

                links_handle.write(
                    "* {status}: {key}\n".format(
                        status=getattr(link.type, category).title(),
                        key=getattr(link, "%sIssue" % category).key,
                    )
                )

            # Write remote links
            for link in folder.jira.remote_links(folder.issue):
                if link.object.title:
                    links_handle.write(
                        "* {title}: {url}\n".format(
                            title=link.object.title, url=link.object.url
                        )
                    )
                else:
                    links_handle.write(
                        "* {url}\n".format(title=link.object.title, url=link.object.url)
                    )

        comments_filename = folder.get_shadow_path(constants.TICKET_COMMENTS)
        with io.open(comments_filename, "w", encoding="utf-8") as comm:
            for comment in folder.issue.fields.comment.comments:
                comm.write(
                    "h3. At %s, %s wrote:\n\n" % (comment.created, comment.author)
                )
                final_lines = []
                lines = folder.process_macro_reversals(
                    comment.body.replace("\r\n", "\n")
                ).split("\n")
                for line in lines:
                    if not line:
                        final_lines.append("")
                    else:
                        final_lines.extend(
                            textwrap.wrap(
                                line,
                                width=70,
                                expand_tabs=False,
                                replace_whitespace=False,
                                break_long_words=False,
                            )
                        )
                for line in final_lines:
                    comm.write("%s\n" % line)
                comm.write("\n")

        folder.store_cached_issue()

        # Clone subtasks
        subtasks = folder.issue.fields.subtasks
        if len(subtasks) > 0:
            commands = utils.get_installed_commands()
            jira = utils.lazy_get_jira()
            with open(folder.get_metadata_path("subtasks"), "w") as out:
                for issue in subtasks:
                    out.write("%s\n" % issue.key)
                    issue_path = folder.get_path(issue.key)
                    if not os.path.exists(issue_path):
                        command_name = "clone"
                        args = [issue.permalink(), issue_path]
                        path = folder.path
                        commands[command_name].execute_command(
                            args, jira=jira, path=path, command_name=command_name
                        )
        folder.build_ignore_files()

        folder.run_git_command("add", "-A", shadow=True)
        folder.run_git_command(
            "commit", "-m", "Fetched remote changes", failure_ok=True, shadow=True
        )

        folder.run_git_command("push", "origin", "jira", shadow=True)
        final_hash = folder.run_git_command("rev-parse", "jira")
        if original_hash != final_hash:
            folder.log("Updated 'jira' to %s" % final_hash)

        return utils.PostStatusResponse(original_hash == final_hash, final_hash)
