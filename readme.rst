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

* `jirafs-graphviz <http://github.com/coddingtonbear/jirafs-graphviz>`_:
  Automatically transform graphviz (dot) files into PNG digraphs during
  upload.
* `jirafs-latex <http://github.com/coddingtonbear/jirafs-latex>`_:
  Automatically transform Latex markup into PDFs during upload.
* `jirafs-pandoc <http://github.com/coddingtonbear/jirafs-pandoc>`_:
  Automatically transform RST/Markdown markup into fancy PDFs during upload.
* `jirafs-list-table <http://github.com/coddingtonbear/jirafs-list-table>`_:
  Make JIRA tables a little more easily using a simple list-based markup.

Requirements
------------

* ``git >= 1.8``
* ``python >= 2.7`` or ``python3 >= 3.3``

----------

- Documentation for Jirafs is available on
  `ReadTheDocs <http://jirafs.readthedocs.org/>`_.
- Please post issues on
  `Github <http://github.com/coddingtonbear/jirafs/issues>`_.
- Test status available on
  `Travis-CI <https://travis-ci.org/coddingtonbear/jirafs>`_.
- Questions? Ask them on
  `Gitter <https://gitter.im/coddingtonbear/jirafs>`_.
