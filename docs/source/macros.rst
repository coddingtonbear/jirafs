Using Macros
============

Macros are special kinds of plugins that perform simple functions for
transforming text you enter into fields into something else when
submitting them to Jira.

Existing Macros
---------------

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

Writing your own Macros
-----------------------

Macros are really just special kinds of plugins; you can find more information
about writing your own plugins in :ref:`macro_plugins`.
