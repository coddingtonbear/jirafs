Interesting Details
===================

.. _ignore-file-format:

Ignore File Format
------------------

The files ``.jirafs_local``, ``.jirafs_ignore`` and
``.jirafs_remote_ignore`` use a subset
of the globbing functionality supported by ``git``'s ``gitignore`` file
syntax.  Specifically, you can have comments, blank lines, and 
globbing patterns of files that you would not like to upload.

For example, if you'd like to ignore files having a ``.diff`` extension,
and would like to add a comment indicating why those are ignored, you
could enter the following into any ``*_ignore`` file::

    # Hide diffs I've generated for posting to reviewboard
    *.diff

Directory Structure
-------------------

Each issue folder includes a hidden folder named ``.jirafs`` that
stores metadata used by Jirafs for this issue.  There may be
many things in this folder, but two highlights include the following
files/folders:

* ``git``: The issue folder is tracked by a git repository to enable
  future features, provide for a way of easily rolling-back or reviewing
  an issue's previous state.
* ``operation.log``: This file logs all operations engaged in on this
  specific issue folder.  You can review this log to see what ``jirafs``
  has done in the past.

.. _vim-plugin:

VIM Plugin
----------

If you're a vim user, I recommend you install my fork of the
`confluencewiki.vim plugin <https://github.com/coddingtonbear/confluencewiki.vim>`_;
if you do so, comment and description field files will use JIRA/Confluence's
WikiMarkup for syntax highlighting.
