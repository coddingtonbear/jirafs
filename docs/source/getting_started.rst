Getting Started
===============

Installation
------------

It is recommended that you install the program using ``pip`` while in a
Python 3 virtualenv;  you can install using ``pip`` by running::

    pip install jirafs

After Jirafs successfully installs, you'll have access to the ``jirafs``
command that you can use for interacting with JIRA.

Working with a JIRA issue
-------------------------

First, you'll need to "clone" the issue you want to work with using
Jirafs by running the following
(replacing ``http://my.jira.server/browse/MYISSUE-1024`` with the
issue url you are concerned about)::

    jirafs clone http://my.jira.server/browse/MYISSUE-1024

The first time you run this command, Jirafs will ask you for a series of details
that it will use for communicating with JIRA; don't worry: although all of this
information will be stored in a plaintext file at ``~/.jirafs_config``, Jirafs will
not store your password unless you give it permission to do so.

Once the command runs successfully, it will have created a new folder named
after the issue you've cloned, and inside that folder it will place a series of
text files representing the issue's contents in JIRA as well as copies of
all attachments currently attached to the issue in JIRA.

The following text files are created:

* ``fields.jira``:  This file will show all currently-set field values
  for this JIRA issue (except fields written to their own files; see
  ``description.jira`` below).  You **can** change field values here
  by editing the field values in the file.  See :ref:`editing_fields`
  for more information.
* ``description.jira``: This file will show the issue's current
  description.  You **can** change the issue's description by editing
  the contents of this file.
* ``links.jira``: This file lists all of the links associated with this
  JIRA issue.  You can add new links (or remove links) by adding or
  removing bulleted items from this list; see :ref:`adding_removing_links`
  for more information.
* ``comments.read_only.jira``: This file shows all comments currently
  posted to this issue.  Note that you **cannot** edit the comments in
  this file.
* ``new_comment.jira``: This file starts out empty, but if you would
  like to add a new comment, you **can** create one by entering text
  into this file.

In order to update any of the above data or upload an asset, either
make the change to a field in ``fields.jira``, edit the issue's
description in ``description.jira``, write a comment into
``new_comment.jira``, or copy a new asset into this folder, then run::

    jirafs status

to see both what changes you've marked as ready for being submitted
to JIRA as well as which changes you have made, but not yet committed.

.. note::

   Unlike when working with a git repository, you do not need to 'stage'
   files using a command analogous to git's "add" command when working with
   a JIRA issue using Jirafs.  All uncommitted files will
   automatically be included in any commit made.

Once you're satisfied with the changes that are about to be submitted to
JIRA, run::

    jirafs submit

.. note::

   ``jirafs submit`` really just runs ``jirafs commit`` followed by
   ``jirafs push`` (which itself runs ``jirafs pull`` to get your
   local copy up-to-date with what it saw in JIRA), so although
   ``jirafs submit`` is probably the path you want to take, feel
   free to use the lower-level more-git-like commands if you want.

Please consider this to be just a simple overview -- there are a
variety of other commands you can run to have finer-grained control
over how the issue folder is synchronized with JIRA; see :doc:`commands`
for more details.

.. note::

   If you are a VIM user, there is a :ref:`vim-plugin`  available that provides
   syntax highlighting for JIRA/Confluence's wikimarkup.

.. _editing_fields:

Editing Issue Fields
--------------------

In most cases, you can simply edit the field's contents directly -- just
make sure to indent the field contents by four spaces.

For text fields, editing field contents is as simple as typing-in a new
value, but many issue fields are are JSON dictionaries or lists that
require you to edit the data in a more-structured way.  If the data
you enter is not valid JSON, when ``push``-ing up changes, you will
receive an error, but don't worry -- if you encounter such an error, edit
the contents to be valid JSON, ``commit``, and ``push`` again.  You 
may need to consult with JIRA's documentation to develop an understanding
of how to change these values.

.. note::

   You don't always need to enter values for every field in a JSON
   dictionary; in some cases, JIRA will infer the missing information
   for you.

.. _adding_removing_links:

Adding, Removing or Changing Links
----------------------------------

Each line of ``links.jira`` starts with a bullet (``*``), and although 
links to other issues (in JIRA terminology -- "issue links") and links
to arbitrary URLs ("remote links") appear similar, they have slightly
different formats.

Issue Links
~~~~~~~~~~~

You can link other issues to your JIRA issue by adding bulleted lines in
the following format::

    * LINK TYPE: TICKET NUMBER

So, if there is an issue relationship named "blocks", and your JIRA issue
is blocked by a ticket numbered "JFS-284", you could add a line::

    * Blocks: JFS-284


.. note::

   Both the issue relationship and ticket number are case-insensitive,
   but that if you enter a relationship name that does not exist, you will
   receive an error message when ``push``-ing up your changes.  If you see
   such an error message, don't fret -- just change your relationship name
   to one of the suggested names, ``commit``, and ``push`` again.

Remote Links
~~~~~~~~~~~~

You can add links to arbitrary URLs by adding bulleted lines in the following
format::

    * NAME: URL

If you, for example, wanted to add a link to your issue that pointed users
toward your favorite cat video, you could, for example, add a line::

    * Cat scares compilation: https://www.youtube.com/watch?v=DBRgFLHra48

Macros
------

One of the most powerful features of Jirafs is how it can make your workflow
vastly easier if you commonly need to do things like insert tables or
graphs or charts in your issues.  There are a handful of macros available
on PyPI including:

* `jirafs-csv-table <https://github.com/coddingtonbear/jirafs-csv-table>`_:
  Makes it easy for you to include tables in your Jira issue by just
  referencing a local CSV file.
* `jirafs-graphviz <https://github.com/coddingtonbear/jirafs-graphviz>`_:
  Make it easy for you to include graphviz charts generated with programs
  like ``dot`` or ``neato`` into your Jira issue by typing your graph
  descriptions directly into your macro content.
