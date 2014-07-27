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
