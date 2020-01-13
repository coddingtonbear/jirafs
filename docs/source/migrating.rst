Migrating from 1.0
==================

There were a lot of changes between Jirafs v1 and Jirafs v2;
so you might be under the impression that you may need to
take special care with how you migrate forward to v2.
Fortunately, though, ticket folders created with Jirafs v1
are fully-compatible with those created by Jirafs v2.
You do, though, need to make one change to how you work with jirafs:
the syntax used for macros has changed, and the macro API
has been updated and will require you to upgrade the macros
you currently use to their latest versions.

If you had a macro named ``list-table`` installed, you previously
would have used that macro by using Jira-style curly-brace syntax::

    {list-table}
    *
    ** One
    ** Two
    * A
    ** B
    ** C
    {list-table}

As of Jirafs v2, we use an xml-inspired syntax for a variety of reasons,
most importantly that it makes it easier for Jirafs to tell the
difference between when you're intending to use Jira markup and when
you're intending that Jirafs run a macro for you::

    <jirafs:list-table>
    *
    ** One
    ** Two
    * A
    ** B
    ** C
    </jirafs:list-table>

Otherwise, behaviors will generally be the same.
