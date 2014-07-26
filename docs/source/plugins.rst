Plugins
=======

Included Plugins
----------------

* dot-to-png
* rst-to-html

Using a plugin
--------------

* Enable the plugin for a given ticket folder::

  jirafs config --set my_plugin_name enabled

Writing your own Plugin
-----------------------

* Add a setuptools entrypoint to your plugin's setup.py::

  entry_points={
    'jirafs_plugins': [
        "my_plugin_name = module.path:ClassName"
    ]
  }

* Write a subclass of ``jirafs.plugin.Plugin`` implementing
  one or more methods using the interface described in `Plugin API`_.

Plugin API
----------

The following properties **must** be defined:

* ``MIN_VERSION``: The string version number representing the minimum version
  of Jirafs that this plugin will work with.
* ``MAX_VERSION``: The string version number representing the maximum version
  of Jirafs that this plugin is compatible with.  Note: Jirafs uses semantic
  versioning, so you may set this value accordingly.

The following methods may be defined for altering Jirafs behavior.

Alteration Methods
~~~~~~~~~~~~~~~~~~

* ``alter_filter_ignored_files(filename_list)``:
  * Further filter the list of files to be processed by reducing this
    list further.
  * Return further filtered ``filename_list``.
* ``alter_new_comment(comment)``:
  * Alter the returned comment.
  * Return an altered ``comment`` string.
* ``alter_remotely_changed(filename_list)``:
  * Alter the list of remotely changed files if necessary.  
  * Return an altered ``filename_list``.
* ``alter_file_upload((filename, file_like_object, ))``:
  * Alter a file pre-upload.
  * Return a new tuple of ``(filename, file_like_object)``.
* ``alter_file_download((filename, file_content, ))``:
  * Alter a file pre-save from JIRA.
  * Return a new tuple of ``(filename, file_like_object)``.
* ``alter_get_remote_file_metadata(file_metadata)``:
  * Alter remote file metadata dictionary after retrieval.
  * Return an altered ``file_metadata`` dictionary.
* ``alter_set_remote_file_metadata(file_metadata)``:
  * Alter remote file metadata dictionary before storage.
  * Return an altered ``file_metadata`` dictionary.

.. note::

   For technical reasons, both ``alter_file_upload`` and
   ``alter_file_download`` accept a single tuple argument containing
   the filename and object rather than two arguments.

Pre/Post Interaction Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``pre_fetch(**kwargs)``:
  * Executed before running ``fetch``.
  * Return ``None`` or altered ``kwargs`` dict.
* ``post_fetch(status_response)``:
  * Executed after running ``fetch``.
  * ``status_response`` named tuple:
    * (bool) ``new``: Whether new content was retrieved during the
      fetch operation.
    * (string) ``hash``: The git SHA of the ``jira`` branch in the
      underlying git repository following the fetch operation.
  * Return ``None`` or new ``jirafs.utils.PostStatusResponse`` instance.
* ``pre_merge(**kwargs)``:
  Executed before running ``merge``
  * Return ``None`` or altered ``kwargs`` dict.
* ``post_merge(status_response)``:
  * Executed after running ``merge``.
  * ``status_response`` named tuple:
    * (bool) ``new``: Whether new content was retrieved during the
      fetch operation.
    * (string) ``hash``: The git SHA of the merge base between the
      ``jira`` and ``master`` branches in the underlying git repository.
  * Return ``None`` or new ``jirafs.utils.PostStatusResponse`` instance.
* ``pre_push(**kwargs)``:
  * Executed before running ``push``.
  * Return ``None`` or altered ``kwargs`` dict.
* ``post_push(status_response)``:
  * Executed after running ``push``.
  * ``status_response`` named tuple:
    * (bool) ``new``: Whether new content was retrieved during the
      fetch operation.
    * (string) ``hash``: The git SHA of the ``jira`` branch in the
      underlying git repository following the fetch operation.
  * Return ``None`` or new ``jirafs.utils.PostStatusResponse`` instance.
* ``pre_status(args=[], kwargs={})``:
  * Executed before running ``status``.
  * Return ``None`` or altered ``kwargs`` dict.
* ``post_status(status_dict)``:
  * Executed after running ``status``.
  * ``status_dict`` dictionary (see tests and source for details):
    * ``uncommitted``: A dictionary containing uncommitted changes.
    * ``ready``: A dictionary of changes ready for submission to JIRA.
    * ``up_to_date``: A boolean value indicating whether the current
      ``master`` branch is up-to-date with changes fetched in the
      ``jira`` branch.
  * Return ``None`` or altered ``status_dict``.

Properties
~~~~~~~~~~

The plugin will have the following properties and methods at its disposal:

* ``self.ticketfolder``: An instance of ``jirafs.ticketfolder.TicketFolder`` representing
  the jira issue that this plugin is currently operating upon.
* ``self.get_metadata()``: Returns a dictionary containing metadata stored
  for this plugin.
* ``self.set_metadata(dict)``: Allows plugin to store metadata.  Data **must**
  be JSON serializable.
