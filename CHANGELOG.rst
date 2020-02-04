2.1.4
-----

* Fixes a bug in which search results from ``search_users`` were not
  being displayed.  (Issue #61)
* Fixes another field deletion/addition problem relating to Issue #59
  (see release notes for 2.1.3 for more).

2.1.3
-----

* Fixes a bug preventing the ``match`` subcommand from being able
  to properly obtain field values.  (Issue #60)
* Fixes a bug that would cause an exception to be raised when calculating
  field differences if one's Jira instance either added or removed fields
  between different ticketfolder versions.  (Issue #59)

2.1.2
-----

* Fixes several minor bugs relating to issue previews including:

  * In certain situations, the preview automatic change detection
    would become stuck in a loop causing the page to refresh
    continuously.
  * Preview document was not delivered with an UTF-8 charset,
    so non-latin-1 characters would be mangled.
  * Changes to Jira fields would not be refreshed when rendering
    preview after submitting changes.
  * Insufficient whitespace between comments may cause Jira to
    misinterpret headers as part of a previous comment's bulleted
    list.

2.1.1
-----

* Fixes bug that would cause an unhelpful traceback to be displayed if you
  were to run Jirafs commands outside of a ticketfolder.

2.1.0
-----

* Fixes to various bugs relating to merging upstream changes
  from Jira with un-pushed local changes.

  * User is now warned about conflicts were they to occur when merging-in
    upstream changes.
  * Conflicts are displayed on the ``status`` display should they exist,
    including instructions about how to resolve them.

* Additional polish for 'preview' function including:

  * Fixes to exception display in-console for harmless errors resulting
    from clients navigating away.
  * Defaulting behavior such that server will automatically self-terminate
    when the user navigates away.  If this behavior is not desired,
    a command-line argument ``--serve-forever`` is available.
  * Adding display of comments for 'all' preview mode.
  * Adds links allowing you to jump to the specific section you're interested
    in when in the 'all' preview mode.

* Macro reversal changes for ``comments.read_only.jira``: No longer will
  macros be reversed for read-only files given that the content of
  historical comments cannot be changed.
* Users can now set a preferred date format by setting a configuration
  value ``main.date_format``.
* Obsolete and undocumented "Clone" functionality allowing you to clone
  a Jira ticketfolder from a git repository (instead of directly from
  a Jira issue) was removed.
* Jira server URL inference when cloning by using an issue number instead
  of a ticket URL is improved to be more foolproof.

2.0.0
-----

* Major revamping of Plugin API to allow for more-reliable
  macro application and reversal, among other optimizations.
* New 'preview' command allowing you to preview content entered
  in any field for quickly verifying formatting and macro-generated content.
* Changes & improvements across the board.

1.2.0
-----

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
