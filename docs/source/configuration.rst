Configuration
=============

Settings affecting all issues are set in the following files:

* ``~/.jirafs_config``: Global configuration values affecting all issues.
* ``~/.jirafs_ignore``: Global list of patterns to ignore when looking through
  issue directories for files to upload to JIRA.  See `Ignore File Format`_
  for details.
* ``~/.jirafs_remote_ignore``: A list of patterns to ignore when looking
  through files attached to a JIRA issue.  Files matching any of these
  patterns will not be downloaded.  See `Ignore File Format`_ for details.

You may also add any of the below files into any issue directory (in this
example, ``MYISSUE-1024``):

* ``MYISSUE-1024/.jirafs_ignore``: A list of patterns to ignore when looking
  through this specific issue directory.  This list of patterns is in
  addition to patterns entered into ``~/.jirafs_ignore`` above.  See
  `Ignore File Format`_ for details.
* ``MYISSUE-1024/.jirafs_remote_ignore``: A list of patterns to ignore
  when looking through files attached to this specific JIRA issue.  Files
  matching any of these patterns will not be downloaded.  These patterns
  are in addition to the patterns entered into ``~/.jirafs_remote_ignore``
  above.  See `Ignore File Format`_ for details.

