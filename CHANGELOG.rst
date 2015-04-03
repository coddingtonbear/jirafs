1.7.0
-----

* Fetching an issue will automatically clone all subtasks.
* Adds new ``subtask`` command that allows one to create new subtasks.

1.6.0
-----

* Separates concepts of ``.jirafs_ignore`` from ``.jirafs_local``; you can now
  keep files out of JIRA and prevent them from being tracked in the local
  git repository simultaneously.

1.5.0
-----

* Adds Python 3.0 support.

1.4.0
-----

* It's now possible to edit non-string/integer fields; they'll appear
  in your fields file as editable JSON.

1.3.0
-----

* Adds new ``field`` command that allows one to fetch the value of any
  ticket field from the command-line.

1.2.0
-----

* Adds functionality for cloning issues from git repositories.
* Adds new ``transition`` command that allows one to transition an issue
  from one status to another.
* Adds better formatting for error messages.

1.0.0
-----

* Close enough to the beginning that it doesn't really matter all that much.
