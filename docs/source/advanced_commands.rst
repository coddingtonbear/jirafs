Advanced Commands
=================

You will probably not have a need to use the below commands, but they
are available for adventurous users.

``fetch``
---------

Fetch upstream changes from JIRA, but do not apply them to your local
copy.  To apply the fetched changes to your local copy, run ``merge``.

``merge``
---------

From within an issue folder, merges previously-fetched but unmerged changes
into your local copy.

``init``
--------

From within a folder named after an issue, converts the existing
folder into a Jirafs issue folder.  This can be useful if you have
already been storing issue-specific files on your filesystem.

``diff``
--------

From within an issue folder, will display any local changes that you have
made.

``log``
-------

From within an issue folder, will print out the log file recording actions
Jirafs has performed for this ticket folder.

``git``
-------

From within an issue folder, will provide direct access to this issue folder's
internal git repository.  This interface is not intended for non-developer
use; please make sure you know what you're doing before performing git
operations directly.

``debug``
---------

From within an issue folder, will open up a python shell having access
to a variable named ``folder`` holding the Python object representing
the ticket folder you are currently within.
