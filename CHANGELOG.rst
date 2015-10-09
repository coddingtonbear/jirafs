1.2
---

* Adds new ``match`` command allowing you to test whether fields match (or
  do not match) expected values.  This is particularly useful for running
  commands on any ticket folders in a specific folder that might match a
  certain condition (e.g: that they're closed).
* Cleanup of existing internal plugins such that the ``main`` method
  performs the majority of the task's work instead of the method named
  after the command's name.
* Added functionality to existing plugin architecture allowing one to
  control the return value of the command.

1.13.2
------

* Fixing a bug that prevented multiple macros from successfully being
  applied to a file.

1.13.1
------

* Patch version bump because I ran the release for 1.13.0 from the wrong
  branch, so it was missing some minor bugfixes.

1.13.0
------

* Changes functionality of "Macro Plugins" to apply only to file-based
  fields.  This will prevent misbehaving macros from making the general
  field file from becoming conflicted.

1.12.0
------

* Adds enable/disable functionality to macro plugins.
* Moved ``{list-table}`` plugin out into its own repository.  To install this
  macro again, see https://github.com/coddingtonbear/jirafs-list-table.
* Adds new ``macropatch`` command allowing you to reset or see the existing
  macropatch.  This is especially important for use in situations where you
  disable a macro plugin.
* Fixed a bug in config handling where on Python 2.7 configparser would
  raise an error when attempting to enable a plugin.

1.11.0
------

* Adds new "Macro Plugins" support including a new built-in macro --
  ``{list-table}`` used for making tables a little bit simpler.
* Alters ``field`` command to return text *after* being processed
  by macros.  Use the ``--raw`` argument to instead return the
  pre-processed field contents.

1.10.0
------

* Adds new ``create`` command providing you with a way of interactively
  creating a new issue.  Note that ``create`` will automatically
  clone the issue once you've supplied the requisite informaiton.
* Adds new ``submit`` command which runs a ``commit`` followed by
  a ``push`` (which itself automatically runs ``pull``); although
  the lower-level git-like commands are still available, using ``submit``
  is now the preferred method of interacting with Jirafs.

1.9.0
-----

* Adds new ``search_users`` command allowing one to search for users.  This
  is particularly useful for when attempting to mention somebody in a ticket
  comment, but you're not sure what their user name is.
* When running ``merge`` (even via ``pull``) messages will be displayed
  indicating remote changes that are being merged-in to your working copy.
* Adds basic integration tests; this should add a lot of insulation preventing
  me (or anybody else) from accidentally breaking Jirafs for versions of
  Python not in use by the writer.

1.8.0
-----

* Adds link-management functionality.  You can now create, remove, and modify
  remote (arbitrary http links) and issue (links to other JIRA issues) by
  editing the ``links.rst`` file.
* Adds new ``--subtask`` command-line argument allowing one to run a command
  upon subtasks even if that command is not configured to do so automatically.
  This is particularly useful for getting the status of a task and all
  subtasks simultaneously by running ``jirafs status --subtask``.
* Now displays a summary of changes from JIRA when ``merge``-ing or
  ``pull``-ing.

1.7.0
-----

* Fetching an issue will automatically clone all subtasks.
* Adds new ``subtask`` command that allows one to create new subtasks.

1.6.0
-----

* Separates concepts of ``.jirafs_ignore`` from ``.jirafs_local``; you can now
  keep files out of JIRA and prevent them from being tracked in the local
  git repository simultaneously.

1.5.0
-----

* Adds Python 3.0 support.

1.4.0
-----

* It's now possible to edit non-string/integer fields; they'll appear
  in your fields file as editable JSON.

1.3.0
-----

* Adds new ``field`` command that allows one to fetch the value of any
  ticket field from the command-line.

1.2.0
-----

* Adds functionality for cloning issues from git repositories.
* Adds new ``transition`` command that allows one to transition an issue
  from one status to another.
* Adds better formatting for error messages.

1.0.0
-----

* Close enough to the beginning that it doesn't really matter all that much.
