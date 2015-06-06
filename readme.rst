Jirafs
======

.. image:: https://travis-ci.org/coddingtonbear/jirafs.svg?branch=master
    :target: https://travis-ci.org/coddingtonbear/jirafs

.. image:: https://badge.fury.io/py/jirafs.png
    :target: http://badge.fury.io/py/jirafs

Pronounced like 'giraffes', but totally unrelated to wildlife, this
library lets you stay out of JIRA as much as possible by letting
you edit your JIRA issues as text files using an interface
modeled off of ``git`` and ``hg``.

.. image:: https://s3-us-west-2.amazonaws.com/coddingtonbear-public/github/jirafs/readme_demo_final.gif

Read more details in `the docs <http://jirafs.readthedocs.org/>`_.

Plugins and Macros Too
----------------------

Additionally provides a Plugin API allowing one to write scripts to simplify
your workflow.  Currently, existing plugins include:

* `jirafs-pandoc <http://github.com/coddingtonbear/jirafs-pandoc>`_: Automatically
  transform RST/Markdown markup into fancy PDFs during upload.
* `jirafs-graphviz <http://github.com/coddingtonbear/jirafs-graphviz>`_:
  Automatically transform graphviz (dot) files into PNG digraphs during
  upload.

and makes it possible for you to write your own "macros" for processing content
you enter into ticket fields.

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
