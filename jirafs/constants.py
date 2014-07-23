# Metadata filenames
TICKET_DETAILS = 'fields.jira'
TICKET_COMMENTS = 'comments.read_only.jira'
TICKET_NEW_COMMENT = 'new_comment.jira'
TICKET_FILE_FIELD_TEMPLATE = '{field_name}.jira'

# Generic settings
IGNORE_FILE = '.jirafs_ignore'
REMOTE_IGNORE_FILE = '.jirafs_remote_ignore'
TICKET_OPERATION_LOG = 'operation.log'
METADATA_DIR = '.jirafs'
GLOBAL_CONFIG = '.jirafs_config'

# Config sections
CONFIG_JIRA = 'jira'

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

MINIMUM_REPO_VERSION = 5
CURRENT_REPO_VERSION = 5

VERSION_CEILINGS = {
    4: '6.0'
}
