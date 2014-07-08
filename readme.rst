JiraFS
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
information will be stored in plaintext at ``~/.jirafs_config``, JiraFS will
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

