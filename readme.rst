Jirafs
======

.. image:: https://travis-ci.org/coddingtonbear/jirafs.svg?branch=master
    :target: https://travis-ci.org/coddingtonbear/jirafs

.. image:: https://badge.fury.io/py/jirafs.png
    :target: http://badge.fury.io/py/jirafs

Pronounced like 'giraffes', but totally unrelated to wildlife, this
library lets you stay out of JIRA as much as possible by letting
you edit your JIRA issues as a collection of text files using an
interface inspired by ``git`` and ``hg``.

.. image:: http://coddingtonbear-public.s3.amazonaws.com/github/jirafs/readme_demo_20150719.gif

Read more details in `the docs <http://jirafs.readthedocs.org/>`_.

Plugins and Macros Too
----------------------

Additionally provides a Plugin API allowing one to write scripts to simplify
your workflow.  Currently, existing plugins include:

* `jirafs-csv-table <http://github.com/coddingtonbear/jirafs-csv-table>`_:
  Make JIRA tables a little more easily by including local CSV files.
* `jirafs-graphviz <http://github.com/coddingtonbear/jirafs-graphviz>`_:
  Embed graphviz dot or neato graphs in your Jira
  issues without leaving your editor.
* `jirafs-mermaid <http://github.com/coddingtonbear/jirafs-mermaid>`_:
  Embed mermaid diagrams in your Jira issues without ever leaving
  your editor.
* `jirafs-plantuml <http://github.com/coddingtonbear/jirafs-plantuml>`_:
  Embed PlantUML diagrams in your Jira issues without ever leaving
  your editor.

Requirements
------------

* ``git >= 1.8``
* ``python3 >= 3.6``

----------

- Documentation for Jirafs is available on
  `ReadTheDocs <http://jirafs.readthedocs.org/>`_.
- Please post issues on
  `Github <http://github.com/coddingtonbear/jirafs/issues>`_.
- Test status available on
  `Travis-CI <https://travis-ci.org/coddingtonbear/jirafs>`_.
- Questions? Ask them on
  `Gitter <https://gitter.im/coddingtonbear/jirafs>`_.
