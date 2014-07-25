Configuration
=============

Settings affecting all issues are set in the following files:

* ``~/.jirafs_config``: Global configuration values affecting all issues.
* ``~/.jirafs_ignore``: Global list of patterns to ignore when looking through
  issue directories for files to upload to JIRA.  See :ref:`ignore-file-format`
  for details.
* ``~/.jirafs_remote_ignore``: A list of patterns to ignore when looking
  through files attached to a JIRA issue.  Files matching any of these
  patterns will not be downloaded.  See :ref:`ignore-file-format` for details.

You may also add any of the below files into any issue directory (in this
example, ``MYISSUE-1024``):

* ``MYISSUE-1024/.jirafs/config``: Configuration overrides for this specific
  issue folder.  Settings set in this file will override -- for this folder
  only -- any values you have set in ``~/.jirafs_config``.
* ``MYISSUE-1024/.jirafs_ignore``: A list of patterns to ignore when looking
  through this specific issue directory.  This list of patterns is in
  addition to patterns entered into ``~/.jirafs_ignore`` above.  See
  :ref:`ignore-file-format` for details.
* ``MYISSUE-1024/.jirafs_remote_ignore``: A list of patterns to ignore
  when looking through files attached to this specific JIRA issue.  Files
  matching any of these patterns will not be downloaded.  These patterns
  are in addition to the patterns entered into ``~/.jirafs_remote_ignore``
  above.  See :ref:`ignore-file-format` for details.

