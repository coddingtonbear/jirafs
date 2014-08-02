Writing your own Plugins
==============================

Jirafs plugins come in two different varieties:

* "Folder Plugins" are used for altering the behavior of existing
  commands when interacting with a Ticket Folder.  They can be disabled
  or enabled on a per-folder basis, too.
* "Command Plugins" are used for adding new commands to Jirafs.  These
  are always enabled when installed.

.. note::

   All existing Jirafs commands ('clone', 'pull', 'push', etc.) are 
   "Command Plugins".

.. toctree::
   :maxdepth: 2

   writing_folder_plugins
   writing_command_plugins

