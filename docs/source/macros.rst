Using Macros
============

Macros are special kinds of plugins that perform simple functions for
transforming text you enter into fields into something else when
submitting them to JIRA.


Built-in Macros
---------------

Currently there's just one built-in macro -- ``{list-table}``:


List Table (``{list-table}``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The list table macro is used for transforming a list into a table, for example::

  {list-table}
  *
  ** Capital
  ** Population (millions)
  * Canada
  ** Ottawa, Ontario
  ** 35.16
  * United States of America
  ** Washington, DC
  ** 318.9
  * Mexico
  ** Mexico City, DF
  ** 122.3
  * Guatemala
  ** Guatemala City
  ** 15.47
  {list-table}

will be automatically transformed into JIRA's special markup::

  || ||Canada||United States of America||Mexico||Guatemala||
  |Capital|Ottawa, Ontario|Washington, DC|Mexico City, DF|Guatemala City|
  |Population (millions)|35.16|318.9|122.3|15.47|

which, when rendered by JIRA, will look something like this:

+------------+-----------------+--------------------------+-----------------+----------------+
|            | Canada          | United States of America | Mexico          | Guatemala      |
+============+=================+==========================+=================+================+
| Capital    | Ottawa, Ontario | Washington, DC           | Mexico City, DF | Guatemala City |
+------------+-----------------+--------------------------+-----------------+----------------+
| Population | 35.16           | 318.9                    | 122.3           | 15.47          |
| (millions) |                 |                          |                 |                |
+------------+-----------------+--------------------------+-----------------+----------------+

Writing your own Macros
-----------------------

Macros are really just special kinds of plugins; you can find more information about
writing your own plugins in :ref:`macro_plugins`.
