Jirafs
======

Pronounced like 'giraffes', but totally unrelated to wildlife, this
library lets you stay out of JIRA as much as possible by letting
you edit your JIRA issues locally.


Getting Started
---------------

Installing the library
~~~~~~~~~~~~~~~~~~~~~~

I recommend installing the program using ``pip`` while in a Python 3
virtualenv;  you can install using ``pip`` by running::

    pip install jirafs

After the library successfully installs, you'll have access to the ``jirafs``
command that you can use for both downloading assets and files from JIRA
as well as updating issues and adding comments.

Cloning a few issues
~~~~~~~~~~~~~~~~~~~~

You'll need to have a local copy of the JIRA issues you'd like to edit
before you can update the contents of issues, so you will wand to find
a place that you'll use to hold the issues you've cloned.

First, create a folder that you'll be cloning your JIRA issues into, and
``cd`` into it::

    mkdir my_jira_issues
    cd my_jira_issues

Then, you can clone any relevant issues by running (replacing ``MYISSUE-1024``
with an actual JIRA issue number in your issue tracking system)::

    jirafs get MYISSUE-1024

The first time you run this command, it will ask you for a series of details
that it will use for communicating with JIRA; don't worry: although all of this
information will be stored in plaintext at ``~/.jirafs_config``, Jirafs will
not store your password unless you give it permission to do so.

Once the command runs successfully, it will download all assets currently
attached to the issue and create a few text files that allow you to see and
edit the issue's contents.  These files include:

* ``details.jira.rst``:  This file will show all currently-set field values
  for this JIRA issue.  You *can* change field values here by editing the
  field values displayed here, but this functionality has only been tested
  for fields storing text data.
* ``comments.read_only.jira.rst``: This file shows all comments currently
  posted to this issue.  Note that you cannot edit the comments in this file.
* ``new_comment.jira.rst``: This file should be empty right now, but if you
  would like to add a new comment, simply enter some text into this field.

In order to update any of the above data or upload an asset, either
make the change to a field in ``details.jira.rst``, write a comment into
``new_comment.jira.rst``, or copy a new asset into this folder, then run::

    jirafs sync

from within the folder ``jirafs`` created earlier.  Running this command
will do the following things:

* Upload any assets in your folder that are not currently attached to this
  JIRA issue.
* Download any assets that are currently attached to this JIRA issue, but are
  not stored locally.
* Update the JIRA issue to reflect any changes to ``details.jira.rst`` that
  you have made.
* If you entered text into the ``new_comment.jira.rst`` file it will post
  a new comment to the JIRA issue using the text you entered.
* Update ``comments.read_only.jira.rst`` to show any comments that are now
  associated with this JIRA issue.

Since there are quite a lot of things going on there, and you might want to
get an idea of what is about to happen, you can list all of the pending
changes by running::

    jirafs status


Configuration
-------------

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


Commands
--------

.. note::

   Commands marked with an asterisk can be ran from either an issue
   folder, or from within a folder containing many issue folders.

   In the latter case, the command will be ran for every subordinate
   issue folder.

``sync`` *
~~~~~~~~~~

From within an issue folder, synchronizes the issue with JIRA.

Internally, this command first runs ``jirafs push`` followed by
a ``jirafs pull``.

``pull`` *
~~~~~~~~~~

From within an issue folder, fetches remote changes from JIRA and applies
the remote changes to your local copy.

``push`` *
~~~~~~~~~~

From within an issue folder, discovers any local changes, and pushes your
local changes to JIRA.

``open`` *
~~~~~~~~~~

From within an issue folder, opens the current JIRA issue in your
webbrowser.

``init``
~~~~~~~~

From within a folder named after an issue, converts the existing
folder into a Jirafs issue folder.  This can be useful if you have
already been storing issue-specific files on your filesystem.

``status`` *
~~~~~~~~~~~~

From within an issue folder, will report any changes that would take place
were you to run ``jirafs sync``.

``get MYISSUE-1024``
~~~~~~~~~~~~~~~~~~~~

Create a new issue folder for ``MYISSUE-1024`` (replace ``MYISSUE-1024`` with
an actual JIRA issue number), and download any assets attached to said issue.


Interesting Details
-------------------

Ignore File Format
~~~~~~~~~~~~~~~~~~

The files ``.jirafs_ignore`` and ``.jirafs_remote_ignore`` use a subset
of the globbing functionality supported by ``git``'s ``gitignore`` file
syntax.  Specifically, you can have comments, blank lines, and 
globbing patterns of files that you would not like to upload.

For example, if you'd like to ignore files having a ``.diff`` extension,
and would like to add a comment indicating why those are ignored, you
could enter the following into any ``*_ignore`` file::

    # Hide diffs I've generated for posting to reviewboard
    *.diff

Directory Structure
~~~~~~~~~~~~~~~~~~~

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
