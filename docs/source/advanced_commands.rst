Advanced Commands
=================

You will probably not have a need to use the below commands, but they
are available for adventurous users.

``fetch``
---------

Fetch upstream changes from JIRA, but do not apply them to your local
copy.  To apply the fetched changes to your local copy, run ``merge``.

``merge``
---------

From within an issue folder, merges previously-fetched but unmerged changes
into your local copy.

``diff``
--------

From within an issue folder, will display any local changes that you have
made.

``field <field name>``
----------------------

Write the content of the field named ``field name`` to the console.  Useful
in scripts for gathering, for example, the ticket's ``summary`` field.

Note that you can also access subkeys in fields containing JSON by using
a dotpath, and can access the following special fields:

* ``new_comment``: The formatted contents of your unsubmitted
  comment.
* ``links``: Returns a JSON structure representing this issue's
  links.
* ``fields``: Returns a JSON structure representing all field
  contents.

``setfield <field name> <value>``
---------------------------------

Set the value of the field named ``field name`` to the value ``value``.
This is useful for programmatically changing the status of various fields.

Note that you can also access subkeys in fields containing JSON by using
a dotpath.

``match <field name> <value>``
------------------------------

Return a status code of ``0`` if the field ``field name`` matches the value
``value``.  This is useful for allowing you to programmatically perform
certain actions on fields matching certain values -- for example: moving 
resolved issues into an archive folder.

As with all commands, check ``--help`` for this command; you'll find
utilities allowing you to invert the check (for returning ``0`` when
the check does **not** match) and utilities for executing a command
when the field does not match.

Note that you can also access subkeys in fields containing JSON by using
a dotpath.

``log``
-------

From within an issue folder, will print out the log file recording actions
Jirafs has performed for this ticket folder.

``config``
----------

Get, set, or list configuration values.  Requires use of one of the following
sub-options:

* ``--get <SETTING_NAME>``: Get the value of this specific parameter name.
* ``--set <SETTING_NAME> <VALUE>``: Set the value of this specific parameter.
* ``--list``: List all settings currently configured in the current context.
  When used within an issue folder, will list this issue's settings, but when
  used outside of an issue folder, will display only global configuration.

You may also use the ``--global`` argument to ensure that configuration
changes or lists use or affect only the global configuration.

``plugins``
-----------

List, activate, or deactivate plugins by name.

Plugins provides several sub-options:

* ``--verbose``: Display information about each plugin along with its name.
* ``--enabled-only``: List only plugins that are currently enabled.
* ``--disabled-only``: List only plugins that are available, but not currently
  enabled.
* ``--enable=PLUGIN_NAME``: Enable a plugin by name for the current issue
  folder.
* ``--disable=PLUGIN_NAME``: Disable a plugin by name for the current issue
  folder.
* ``--global``: Used with ``--enable`` or ``--disable`` above, will enable
  or disable a plugin globally.  Note: per-folder settings always take
  priority.

``git``
-------

From within an issue folder, will provide direct access to this issue folder's
internal git repository.  This interface is not intended for non-developer
use; please make sure you know what you're doing before performing git
operations directly.

``debug``
---------

From within an issue folder, will open up a python shell having access
to a variable named ``folder`` holding the Python object representing
the ticket folder you are currently within.

``search_users <term>``
-----------------------

Search for users matching the specified search term.  This is particularly
useful if you're not sure what somebody's username and you were hoping to
mention them in a ticket so they get an e-mail notification.

``create``
----------

Creates a new issue.  Provides the following options:

* ``--summary``: The summary to use for your new issue.
* ``--description``: The description to use for your new issue.
* ``--issuetype``: The issue type to use for your new issue (defaults
  to 'Task').
* ``--project``: The project key to use for your new issue.  This is
  the short, capitalized string you see next to issues.  For example,
  if your tickets were named something like KITTENS-12084, 'KITTENS'
  is the project key.
* ``--quiet``: Do not prompt user to provide values interactively.

If any of the above values are not specified, the user will be prompted to
provide them interactively.
