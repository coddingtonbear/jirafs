Jirafs
======

.. image:: https://travis-ci.org/coddingtonbear/jirafs.svg?branch=master
    :target: https://travis-ci.org/coddingtonbear/jirafs

.. image:: https://badge.fury.io/py/jirafs.png
    :target: http://badge.fury.io/py/jirafs

.. image:: https://pypip.in/d/jirafs/badge.png
    :target: https://pypi.python.org/pypi/jirafs

Pronounced like 'giraffes', but totally unrelated to wildlife, this
library lets you stay out of JIRA as much as possible by letting
you edit your JIRA issues as text files using an interface
modeled off of ``git``.


Getting Started
---------------

Installation
~~~~~~~~~~~~

It is recommended that you install the program using ``pip`` while in a
Python 3 virtualenv;  you can install using ``pip`` by running::

    pip install jirafs

After the program successfully installs, you'll have access to the ``jirafs``
command that you can use for both downloading attachments and files from JIRA
as well as updating issues and adding comments.

Cloning a JIRA issue
~~~~~~~~~~~~~~~~~~~~

You'll need to have a local copy of the JIRA issues you'd like to edit
before you can update the contents of issues, so you will want to find
a place that you can "clone" (create a text-file based copy of) the
issue you're concerned about, then run the following (replacing
``MYISSUE-1024`` with the issue number you are concerned about)::

    jirafs clone MYISSUE-1024

The first time you run this command, it will ask you for a series of details
that it will use for communicating with JIRA; don't worry: although all of this
information will be stored in plaintext at ``~/.jirafs_config``, Jirafs will
not store your password unless you give it permission to do so.

Once the command runs successfully, it will create a new folder named after
the issue you've cloned, and inside that folder it will place a series of
text files and copies of all attachments currently attached to the issue in JIRA.

The following text files are created:

* ``fields.jira``:  This file will show all currently-set field values
  for this JIRA issue (except fields written to their own files; see
  ``description.jira`` below).  You *can* change field values here
  by editing the field values in the file, but this functionality has
  only been tested for fields storing text data.
* ``description.jira``: This file will show the issue's current
  description.  You *can* change the issue's description by editing
  the contents of this file.
* ``comments.read_only.jira``: This file shows all comments currently
  posted to this issue.  Note that you **cannot** edit the comments in
  this file.
* ``new_comment.jira``: This file starts out empty, but if you would
  like to add a new comment, simply enter some text into this file.

In order to update any of the above data or upload an asset, either
make the change to a field in ``fields.jira``, edit the issue's
description in ``description.jira``, write a comment into
``new_comment.jira``, or copy a new asset into this folder, then run::

    jirafs commit

from within the folder ``jirafs`` created earlier.

.. note::

   Unlike git, you need not 'stage' files using a command analogous to
   git's "add" command when using Jirafs; all uncommitted files will
   automatically be included in any commit made.

Running this command will mark the changes you've made as ready for
submission to JIRA.  At any time, you can run::

    jirafs status

to see both what changes you've marked as ready for being submitted
to JIRA as well as which changes you have made, but not yet committed.

Once you're satisfied with the changes that are about to be submitted to
JIRA, run::

    jirafs push

Please keep in mind that updates that others have made in JIRA outside of 
Jirafs won't be available in your local copy until you pull them in by
running::

    jirafs pull

Please consider the above to be just a simple overview -- there are a
variety of other commands you can run to have finer-grained control
over how the issue folder is synchronized with JIRA; see `Commands`_
for more details.


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

``clone MYISSUE-1024``
~~~~~~~~~~~~~~~~~~~~

Create a new issue folder for ``MYISSUE-1024`` (replace ``MYISSUE-1024`` with
an actual JIRA issue number), and download any assets attached to said issue.

``commit``
~~~~~~~~~~

From within an issue folder, commits local changes and marks them for
submission to JIRA next time ``push`` is run.

.. note::

   Unlike using git (but like mercurial), you need not stage files
   (by running a command analogous to git's 'add') before committing.
   The commit operation will automatically commit changes to all
   un-committed files.

``pull`` *
~~~~~~~~~~

From within an issue folder, fetches remote changes from JIRA and merges
the changes into your local copy.  This command is identical to running
``fetch`` followed by ``merge``.

``push`` *
~~~~~~~~~~

From within an issue folder, discovers any local changes, and pushes your
local changes to JIRA.

``status`` *
~~~~~~~~~~~~

From within an issue folder, will report both any changes you have not
yet committed, as well as any changes that would take place were you to
run ``jirafs push``.

``open`` *
~~~~~~~~~~

From within an issue folder, opens the current JIRA issue in your
default web browser.

Advanced Commands
-----------------

You will probably not have a need to use the below commands, but they
are available for adventurous users.

``fetch``
~~~~~~~~~

Fetch upstream changes from JIRA, but do not apply them to your local
copy.  To apply the fetched changes to your local copy, run ``merge``.

``merge``
~~~~~~~~~

From within an issue folder, merges previously-fetched but unmerged changes
into your local copy.

``init``
~~~~~~~~

From within a folder named after an issue, converts the existing
folder into a Jirafs issue folder.  This can be useful if you have
already been storing issue-specific files on your filesystem.

``diff``
~~~~~~~~

From within an issue folder, will display any local changes that you have
made.

``log``
~~~~~~~

From within an issue folder, will print out the log file recording actions
Jirafs has performed for this ticket folder.

``git``
~~~~~~~

From within an issue folder, will provide direct access to this issue folder's
internal git repository.  This interface is not intended for non-developer
use; please make sure you know what you're doing before performing git
operations directly.

``debug``
~~~~~~~~~

From within an issue folder, will open up a python shell having access
to a variable named ``ticketfolder`` holding the Python object
representing the ticket folder you are currently within.


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

VIM Plugin
~~~~~~~~~~

If you're a vim user, I recommend you install my fork of the
`confluencewiki.vim plugin <https://github.com/coddingtonbear/confluencewiki.vim>`_;
if you do so, comment and description field files will use JIRA/Confluence's
WikiMarkup for syntax highlighting.
