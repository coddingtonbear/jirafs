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

Jirafs provides a Plugin API allowing you to simplify your workflow in Jira;
several plugins already exist, including the following tools:

* For including programmatically-generated images in your Jira issues without
  ever leaving your editor:

  * `jirafs-graphviz <http://github.com/coddingtonbear/jirafs-graphviz>`_:
    Embed Graphviz (e.g. ``dot`` or ``neato``) graphs using Graphviz's
    ubiquitous graph description language.
  * `jirafs-matplotlib <http://github.com/coddingtonbear/jirafs-matplotlib>`_:
    Embed graphs generated with the common Python charting library Matplotlib
    by writing simple python scripts.
  * `jirafs-plantuml <http://github.com/coddingtonbear/jirafs-plantuml>`_:
    Embed UML (e.g. timing, sequence, or activity) diagrams
    generated via PlantUML's easy-to-use text format.
  * `jirafs-mermaid <http://github.com/coddingtonbear/jirafs-mermaid>`_:
    Embed beautiful diagrams (e.g. pie, gantt, or class)
    using Mermaid's markdown-ish diagram description language.

* For making tables more easily:

  * `jirafs-csv-table <http://github.com/coddingtonbear/jirafs-csv-table>`_:
    Include tables in Jira by generating them from local CSV files.
  * `jirafs-list-table <http://github.com/coddingtonbear/jirafs-list-table>`_:
    Create tables in Jira by using a simple list-based syntax.

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
