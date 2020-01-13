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
* ``self.metadata``: Returns a dictionary containing metadata stored for this plugin.  This dictionary is modifyable, and will be preserved between plugin executions.

.. _macro_methods:

Methods
~~~~~~~

* ``execute_macro(data: str, attrs: Dict, config: Dict) -> str``:
  **REQUIRED** 
  Your macro function.  It will receive a series of parameters:

  * ``data``: The content of your macro.
  * ``attrs``: Any attributes of your macro.
  * ``config``: Jirafs config parameters.

  and is expected to return a string of text that your macro will
  be replaced when when sending content to Jira.
* ``execute_macro_reversal(data: str) -> str``:
  If provided, will be expected to perform the reversal of
  ``execute_macro`` above.  It will receive as parameters the full
  text of each field.
* ``cleanup()``: Perform any cleanup following macro processing for
  a ticket folder.  If you need more-granular control, you can define
  methods for ``cleanup_pre_process()`` and ``cleanup_post_process()``
  if you need to segment your cleanup process between before and after
  running macro processing methods.

.. _macro_plugins:

Macro Plugins
-------------

Macro plugins are special kinds of folder plugins that are instead subclasses of ``jirafs.plugin.MacroPlugin``
but same setuptools entrypoints apply as are described in :ref:`entry_points`.

Macros can be executed using either a block element format; for example::

    <jirafs:my-macro>
    Some content
    </jirafs:my-macro>

.. note::

   See :ref:`macro_attributes` for more information about attributes and
   the special ``src`` attribute.

or as a void element::

    <jirafs:my-macro src="some_file_to_read_as_content.ext" />

.. note::

   The trailing slash at the end of your macro is important!

Your ``execute_macro`` method is expected to return text that should be sent
to JIRA instead of your macro.  Note that the method signature remains
identical to that of a block element macro, but instead of receiving
the content of the block, you will receive ``None``.

.. _macro_attributes:

Reserved Attributes
~~~~~~~~~~~~~~~~~~~

* ``src``: All macro plugins can be provided in either a block or void
  elements.  When using a block element version of your macro, you
  provide content directly within the content of your tag.  If you
  would like the content to be imported from a file instead, you
  can provide the path to the file to import via the ``src`` attribute.


Attributes
~~~~~~~~~~

Both block and void elements can receive any number of attributes; they're
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

    class Plugin(MacroPlugin):
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


Automatically-Reversed Macro Plugins
------------------------------------

It's not a ton of fun to have to handle reversing your own macros; so
if your macro's content will produce unique content for provided input,
you can use the ``AutomaticReversalMacroPlugin`` as your base class
instead of ``MacroPlugin``.  If you do so, your macro will automatically
be reversed when returning content from Jira by scanning the content
received from Jira and replacing any output generated by your macro
during the most recent run with the macro content that generated that
output.

In general, you won't need to make any special modifications, but there
are useful methods for overriding in special circumstances:

* ``should_rerender(data: str, cache_entry: Dict, config: Dict) -> bool``:
  Control whether this given input content (``data``)
  should be re-rendered.  By default, ``should_rerender`` returns
  ``True`` only if ``cache_entry`` is empty.  Values available in
  the ``cache_entry`` dictionary include:

  * ``filenames``: A list of filenames generated by your macro while
    during processing of this input text.
  * ``attrs``: Macro attributes set for your macro when running for
    this input text.
  * ``replacement``: The replacement text generated by your macro
    for this input text.
  * ``is_temp``: Whether or not this macro result was the result of
    generating content for your current working directory (``is_temp==False``),
    or if it was the result of processing historical content for
    identifying changes (``is_temp==True``).

See :ref:`macro_methods` for other methods that may be necessary for
your macro.

Examples
~~~~~~~~

See one of the following repositories for an example of this type of macro:

* `jirafs-csv-table <https://github.com/coddingtonbear/jirafs-csv-table>`_


Image Macros
------------

A particularly powerful Macro type is the "Image Macro".  Use of a macro
of this type will allow you to automatically generate and embed images
in your Jira content by passing your macro's contents through a tool
like Graphviz' ``dot`` or ``plantuml``.

In the case of this type of macro, you need to define just one method:

* ``get_extension_and_image_data(data: str, attrs: Dict) -> Tuple[str, bytes]``:
  For a given input text (``data``) and macro attributes (``attrs``),
  return a 2-tuple of the file extension to use for the file to be
  created, and the bytes of that file.


See :ref:`macro_methods` for other methods that may be necessary for
your macro.

.. note::

   Unlike most subclasses of ``MacroPlugin``, you should not define
   your own ``execute_macro`` method!

Examples
~~~~~~~~

See one of the following repositories for an example of this type of
macro:

* `jirafs-graphviz <https://github.com/coddingtonbear/jirafs-graphviz>`_

.. note::

   Image Macros are automatically reversed.
