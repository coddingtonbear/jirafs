# Metadata filenames
TICKET_DETAILS = 'fields.jira.rst'
TICKET_COMMENTS = 'comments.read_only.jira.rst'
TICKET_NEW_COMMENT = 'new_comment.jira.rst'
TICKET_FILE_FIELD_TEMPLATE = '{field_name}.jira.rst'

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

CURRENT_REPO_VERSION = 4
