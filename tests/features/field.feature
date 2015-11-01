Feature: Getting field values

    @wip
    Scenario: Getting a single field's value
        Given a cloned ticket with the following fields
         | key         | value                          | 
         | summary     | "This is a ticket summary"     | 
         | description | "This is a ticket description" | 
        When the command "jirafs field summary" is executed
        Then the output will contain the text "This is a ticket summary"
        When the command "jirafs field description" is executed
        Then the output will contain the text "This is a ticket description"
