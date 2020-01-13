from jirafs import __version__ as version

# Metadata filenames
TICKET_DETAILS = "fields.jira"
TICKET_COMMENTS = "comments.read_only.jira"
TICKET_NEW_COMMENT = "new_comment.jira"
TICKET_LINKS = "links.jira"
TICKET_FILE_FIELD_TEMPLATE = u"{field_name}.jira"

# Generic settings
LOCAL_ONLY_FILE = ".jirafs_local"
REMOTE_IGNORE_FILE = ".jirafs_remote_ignore"
GIT_IGNORE_FILE_PARTIAL = ".jirafs_ignore"
GIT_IGNORE_FILE = ".jirafs/combined_ignore"
GIT_EXCLUDE_FILE = ".jirafs/git/info/exclude"
TICKET_OPERATION_LOG = "operation.log"
METADATA_DIR = ".jirafs"
GLOBAL_CONFIG = ".jirafs_config"
TEMP_GENERATED_FILES = ".jirafs/temp-generated"
GIT_AUTHOR = "Jirafs %s <jirafs@localhost>" % (version)

# Config sections
CONFIG_JIRA = "jira"
CONFIG_MAIN = "main"
CONFIG_PLUGINS = "plugins"

NO_DETAIL_FIELDS = ["comment", "watches", "attachment"]
FILE_FIELDS = [
    "description",
]
FILE_FIELD_BLACKLIST = [
    "new_comment",
    "fields",
    "links",
]

ALLOW_USER_INPUT = True

CURRENT_REPO_VERSION = 16


from environmental_override import override  # noqa

override(locals(), "JIRAFS_")
