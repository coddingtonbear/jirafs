from jirafs import __version__ as version

# Metadata filenames
TICKET_DETAILS = 'fields.jira'
TICKET_COMMENTS = 'comments.read_only.jira'
TICKET_NEW_COMMENT = 'new_comment.jira'
TICKET_FILE_FIELD_TEMPLATE = '{field_name}.jira'

# Generic settings
IGNORE_FILE = '.jirafs_ignore'
REMOTE_IGNORE_FILE = '.jirafs_remote_ignore'
GIT_IGNORE_FILE = '.jirafs/gitignore'
TICKET_OPERATION_LOG = 'operation.log'
METADATA_DIR = '.jirafs'
GLOBAL_CONFIG = '.jirafs_config'
GIT_AUTHOR = 'Jirafs %s <jirafs@adamcoddington.net>' % (
    version
)

# Config sections
CONFIG_JIRA = 'jira'
CONFIG_PLUGINS = 'plugins'

NO_DETAIL_FIELDS = [
    'comment',
    'watches',
    'attachment'
]
FILE_FIELDS = [
    'description',
]
FILE_FIELD_BLACKLIST = [
    'new_comment',
    'fields'
]

CURRENT_REPO_VERSION = 13
