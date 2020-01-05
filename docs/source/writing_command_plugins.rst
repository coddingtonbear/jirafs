Writing Command Plugins
=======================

For a working example of a command plugin, check out
`the source of Jirafs existing commands <https://github.com/coddingtonbear/jirafs/tree/1.x/jirafs/commands>`_.

Setuptools Entrypoint
---------------------

* Add a setuptools entrypoint to your plugin's ``setup.py``::

    entry_points={
      'jirafs_commands': [
          "my_command_name = module.path:ClassName"
      ]
    }

* Write a subclass of ``jirafs.plugin.CommandPlugin`` implementing
  one or more methods using the interface described in `Plugin API`_.

Plugin API
----------

The following properties **must** be defined:

* ``MIN_VERSION``: The string version number representing the minimum version
  of Jirafs that this plugin will work with.
* ``MAX_VERSION``: The string version number representing the first version
  at which your plugin would *not* be guaranteed to becompatible.  Note
  that this means that your Jirafs version must be *below* this number, and
  that users running a version of Jirafs matching this will see an error
  message.  Note: Jirafs uses semantic versioning, so you should set this
  value to the next major version about the highest version you've tested.

The following methods may be defined to control the behavior of your
command plugin:

* ``handle(self, args, folder, jira, path, **kwargs)``: (**REQUIRED**)
  This method (and methods called from here) is where you should write
  the bulk of your plugin's functionality.  ``handle`` receives several
  keyword arguments:

  * ``args``: An instance of ``argparse.Namespace`` holding arguments
    specified on the command line.  See ``add_arguments`` and
    ``parse_arguments`` for details.
  * ``folder``: A ``jirafs.ticketfolder.TicketFolder`` instance 
    corresponding with the current path.  If you are writing a command
    that does not require a ticketfolder, set an attribute on your class
    named ``AUTOMATICALLY_INSTANTIATE_FOLDER`` to ``False`` (Note that
    this option makes the value of ``TRY_SUBFOLDERS`` irrelevant) and
    this value will always be ``None`` whether or not your command was
    invoked from within a ticket folder.
  * ``jira``: A callable (accepting, optionally, the string domain
    of a JIRA instance) which will return an instance of ``jira.client.JIRA``
    corresponding with the domain you've specified, or the default JIRA
    connection if no JIRA domain was specified.
  * ``path``: The string path from which this command was called.  This
    can be used to create a ``jirafs.ticketfolder.TicketFolder`` instance
    representing the current ticket folder if so desired.
  * ``**kwargs``: Keyword arguments **may** be added in the future; it is
    extremely important that your ``handle`` method accept arbitrary
    keyword arguments in order to prevent your plugin from breaking
    when new keyword arguments are added in the future.

* ``add_arguments(self, parser)``: Using this method, you can add
  arguments that your command requires.  Follow the guidelines in Python's
  ``argparse`` documentation for an overview of how arguments are handled.

  * ``parser``: An ``argparse.ArgumentParser`` instance.

* ``parse_arguments(self, parser, extra_arguments)``: Potentially useful
  as a method to place argument validation.

  * ``parser``: An ``argparse.ArgumentParser`` instance.  Note that this
    instance will have already had attached all arguments added in the
    ``add_arguments`` method above.
  * ``extra_arguments``: A list of string arguments unused by Jirafs.

You may also use any of the following properties
to alter the behavior of Jirafs:

* ``TRY_SUBFOLDERS``: Set this class property to ``True`` if this command
  should be applied to all Jirafs ticket folders in subdirectories in the
  event that the current folder is not a ticket folder.
* ``RUN_FOR_SUBTASKS``: Set this class property to ``True`` if you would like
  your command to be automatically executed for subtask when being executed
  for a ticket having subtasks.

Example Plugin
--------------

.. literalinclude:: ../../jirafs/commands/git.py

