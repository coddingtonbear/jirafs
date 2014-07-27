Available Plugins
=================

Jirafs-Pandoc
-------------

Allows you to automatically convert pandoc-supported documents into PDF
files (or any other pandoc-supported output format) when uploading to JIRA.

Install from PyPI::

    pip install jirafs-pandoc

Enable for your ticket folder::

    jirafs config --set plugins.pandoc enabled

Or, enable globally::

    jirafs config --global --set plugins.pandoc enabled

More information on
`Jirafs-Pandoc's Github Repository <https://github.com/coddingtonbear/jirafs-pandoc>`_.

Jirafs-Graphviz
---------------

Allows you to automatically convert graphviz documents into PNG images when
uploading them to JIRA.

Install from PyPI::

    pip install jirafs-graphviz

Enable for your ticket folder::

    jirafs config --set plugins.graphviz enabled

Or, enable globally::

    jirafs config --global --set plugins.graphviz enabled

More information on
`Jirafs-Graphviz's Github Repository <https://github.com/coddingtonbear/jirafs-graphviz>`_.
