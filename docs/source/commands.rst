Common Commands
===============

The following commands are sure to be commonly used.  Be sure to 
check out :doc:`advanced_commands` if you are curious about
less-commonly-used functionality.

.. note::

   Commands marked with an asterisk can be ran from either an issue
   folder, or from within a folder containing many issue folders.

   In the latter case, the command will be ran for every subordinate
   issue folder.


``clone http://my.jira.server/browse/MYISSUE-1024``
---------------------------------------------------

Possible forms include:

* ``clone http://my.jira.server/browse/MYISSUE-1024 [PATH]``
* ``clone MYISSUE-1024 [PATH]`` (will use default JIRA instance)

Create a new issue folder for ``MYISSUE-1024`` (replace ``MYISSUE-1024`` with
an actual JIRA issue number), and clone the relevant issue into this folder.

Note that you may specify a full URL pointing to an issue, but if you do not
specify a full URL, your default JIRA instance will be used; if you have
not yet set one, you will be asked to specify one.

Although by default, the issue will be cloned into a folder matching the name
of the issue, you may specify a path into which the issue should be cloned.

``commit``
----------

From within an issue folder, commits local changes and marks them for
submission to JIRA next time ``push`` is run.

.. note::

   Unlike git (but like mercurial), you do not need to stage files
   by running a command analogous to git's 'add' before committing.
   The commit operation will automatically commit changes to all
   un-committed files.

``pull`` *
----------

From within an issue folder, fetches remote changes from JIRA and merges
the changes into your local copy.  This command is identical to running
``fetch`` followed by ``merge``.

``push`` *
----------

From within an issue folder, discovers any local changes, and pushes your
local changes to JIRA.

``status`` *
------------

From within an issue folder, will report both any changes you have not
yet committed, as well as any changes that would take place were you to
run ``jirafs push``.

``open`` *
----------

From within an issue folder, opens the current JIRA issue in your
default web browser.

``transition``
----------------------------------------

From within an issue folder, allows you to transition an issue into any
state available in your workflow.

Possible forms include:

* ``transition``: The user will be presented with state options for
  selection at runtime.
* ``transition 10``: Transition into the state with the ID of '10'.
* ``transition "closed"``: Transition into the state with the name
  "closed".  Note that state names are case-insensitive.

.. note::

   Note that the options available are dependent upon the user account
   used for authentication.

