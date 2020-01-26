Configuration
=============

Settings affecting all issues are set in the following files:

* ``~/.jirafs_config``: Global configuration values affecting all issues.
* ``~/.jirafs_ignore``: Global list of patterns to ignore completely; these
  files differ from ``.jirafs_local`` below in that they **will not** be
  tracked in the underlying git repository.
  See :ref:`ignore-file-format` for details.
* ``~/.jirafs_local``: Global list of patterns to ignore when looking through
  issue directories for files to upload to Jira. Note that these files
  **will** continue to be tracked in the underlying git repository.
  See :ref:`ignore-file-format` for details.
* ``~/.jirafs_remote_ignore``: A list of patterns to ignore when looking
  through files attached to a Jira issue.  Files matching any of these
  patterns will not be downloaded.  See :ref:`ignore-file-format` for details.

You may also add any of the below files into any issue directory (in this
example, ``MYISSUE-1024``):

* ``MYISSUE-1024/.jirafs/config``: Configuration overrides for this specific
  issue folder.  Settings set in this file will override -- for this folder
  only -- any values you have set in ``~/.jirafs_config``.
* ``MYISSUE-1024/.jirafs_ignore``: A list of patterns to ignore completely;
  these files differ from ``.jirafs_local`` below in that they **will not**
  be tracked in the underlying git repository.
  See :ref:`ignore-file-format` for details.
* ``MYISSUE-1024/.jirafs_local``: A list of patterns to ignore when looking
  through this specific issue directory.  This list of patterns is in
  addition to patterns entered into ``~/.jirafs_ignore`` above. Note that
  these files **will** continue to be tracked in the underlying git
  repository.  See :ref:`ignore-file-format` for details.
* ``MYISSUE-1024/.jirafs_remote_ignore``: A list of patterns to ignore
  when looking through files attached to this specific Jira issue.  Files
  matching any of these patterns will not be downloaded.  These patterns
  are in addition to the patterns entered into ``~/.jirafs_remote_ignore``
  above.  See :ref:`ignore-file-format` for details.

Using an untrusted HTTPS certificate
------------------------------------

If your Jira instance uses a self-signed certificate or you are working
in an enterprise environment having a non-standard certificate authority,
you can manually configure your Jira connection to either not verify the
certificate, or to instead use a non-standard certificate authority
certificate.

1. First, find the configuration section in your ``~/.jirafs_config`` named
   after the address of your Jira server.
2. Then, after the lines starting with ``username`` and ``password``, add a
   line reading ``verify = <VALUE>`` replacing ``<VALUE>`` with one of two
   options:

   * If your Jira instance uses a self-signed certificate: the string ``false``.
   * If your Jira instance's certificate uses a non-standard certificate
     authority, the absolute path to a place on your computer where your
     certificate authority's certificate is stored.

For example:

.. code-block:: ini
   :linenos:
   :emphasize-lines: 4

   [https://jira.mycompany.org]
   username = myusername
   password = mypassword
   verify = /path/to/certificate/or/false

Disabling "Save Jira Password" prompt
-------------------------------------

If you would never like to save your Jira password in Jirafs, you can disable
the "Save Jira Password" prompt by setting the ``ask_to_save`` setting to ``false`` in the ``main`` section of your ``~/.jirafs_config`` file.

For example:

.. code-block:: ini
   :linenos:
   :emphasize-lines: 2

   [main]
   ask_to_save = false


Setting a Date Format for Rendered Comments
-------------------------------------------

By default, Jirafs will render a date using the following international
date format::

     %Y-%m-%d at %H:%M:%S %Z

But you can configure the format to one more familiar to you by setting the
``main.date_format`` configuration setting using the formatting codes
described here: `https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes`_

.. code-block:: ini
   :linenos:
   :emphasize-lines: 2

   [main]
   date_format = %d %B %Y at %h:%M %p
