Writing Plugins
===============

For a working example of a folder plugin, check out
`Jirafs-Pandoc's Github Repository <https://github.com/coddingtonbear/jirafs-pandoc>`_.

.. _entry_points:

Setuptools Entrypoint
---------------------

* Add a setuptools entrypoint to your plugin's ``setup.py``::

    entry_points={
      'jirafs_plugins': [
          "my_plugin_name = module.path:ClassName"
      ]
    }

* Write a subclass of ``jirafs.plugin.Plugin`` implementing
  one or more methods using the interface described in `Folder Plugin API`_.

Folder Plugin API
-----------------

The following properties **must** be defined:

* ``MIN_VERSION``: The string version number representing the minimum version
  of Jirafs that this plugin will work with.
* ``MAX_VERSION``: The string version number representing the first version
  at which your plugin would *not* be guaranteed to becompatible.  Note
  that this means that your Jirafs version must be *below* this number, and
  that users running a version of Jirafs matching this will see an error
  message.  Note: Jirafs uses semantic versioning, so you should set this
  value to the next major version about the highest version you've tested.

Pre/Post Command Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All commands (including user-installed commands) can have plugins altering
their behavior by defining ``pre_*COMMAND*`` and ``post_*COMMAND*`` methods.
For the below, please replace ``*COMMAND*`` with the command your plugin
would like to alter the behavior of.

* ``pre_*COMMAND*(**kwargs)``:

  * Executed before handling ``*COMMAND*``.  Receives (as ``**kwargs``)
    all parameters that will be passed-in to the underlying command. 
  * You may alter the parameters that will be passed-in to the underlying
    command by returning a new or altered ``**kwargs`` dictionary.
  * Return ``None`` or the original ``**kwargs`` dictionary to pass
    original arguments to the command without alteration.

* ``post_*COMMAND*(returned)``:

  * Executed after handling ``*COMMAND*``.  Receives as an argument the
    result returned by the underlying command.

.. note::

   Although the return values of commands are not in the scope of this
   specification, many commands return a ``jirafs.utils.PostStatusResponse``
   instance.

   Such an instance is a named tuple containing two properties:

   * (bool) ``new``: Whether the command's action had an effect on the
     underlying git repository.
   * (string) ``hash``: The hash of the relevant repository branch's head
     commit following the action.

Properties
~~~~~~~~~~

The plugin will have the following properties and methods at its disposal:

* ``self.ticketfolder``: An instance of ``jirafs.ticketfolder.TicketFolder`` representing
  the jira issue that this plugin is currently operating upon.
* ``self.get_configuration()``: Returns a dictionary of configuration settings for this
  plugin.
* ``self.get_metadata()``: Returns a dictionary containing metadata stored
  for this plugin.
* ``self.set_metadata(dict)``: Allows plugin to store metadata.  Data **must**
  be JSON serializable.


.. _macro_plugins:

Macro Plugin API
----------------

Macro plugins are special kinds of folder plugins that are instead subclasses of
either ``jirafs.plugin.BlockElementMacroPlugin`` or ``jirafs.plugin.VoidElementMacroPlugin``,
but same setuptools entrypoints apply as are described in :ref:`entry_points`.

Block Element Macros
~~~~~~~~~~~~~~~~~~~~

Block element macros are macros that wrap a body of text -- for example::

    <jirafs:my-macro>
    Some content
    </jirafs:my-macro>

.. note::
    
   See :ref:`macro_parameters` for more information about parameters.

Your ``execute_macro`` method is expected to return text that should be sent
to JIRA instead of your macro.

Void Element Macros
~~~~~~~~~~~~~~~~~~~

Void element macros and block element macros share a lot of similarities, except
that void element macros do not have their own content and are self-closed;
for example::

    <jirafs:my-macro />

Your ``execute_macro`` method is expected to return text that should be sent
to JIRA instead of your macro.  Note that the method signature remains
identical to that of a block element macro, but instead of receiving
the content of the block, you will receive ``None``.

.. _macro_parameters:

Parameters
~~~~~~~~~~

Both block and void elements can receive any number of parameters; they're
specified following the same conventions you might use for providing an HTML
tag with attributes; for example:

    <jirafs:flag-image country_code="US" size=300 alternate=True />
    {flag-image:country_code=US|size=300|alternate}

* ``country_code``: ``US`` (string)
* ``size``: ``300.0`` (float)
* ``alternate``: ``True`` (boolean)

Example Macro Plugin
~~~~~~~~~~~~~~~~~~~~

The following plugin isn't exactly useful, but it does demonstrate
the basic functionality of a plugin:

.. code-block:: python

    class Plugin(BlockElementMacroPlugin):
        COMPONENT_NAME = 'upper-cased'

        def execute_macro(self, data, prefix='', **kwargs):
            return prefix + data.upper()

When you enter the following text into a JIRA ticket field::

    <jirafs:upper-cased prefix="Hello, ">my name is Adam.</jirafs:upper-cased>

the following content will be sent to JIRA instead::

    Hello, MY NAME IS ADAM.

.. warning::

   Note that it's always a good idea to make sure your ``execute_macro``
   method has a final parameter of ``**kwargs``!  In future versions of
   Jirafs, we may add more keyword arguments that will be sent automatically.
