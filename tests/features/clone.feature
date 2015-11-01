Feature: Cloning a ticket

    Scenario: Simple Clone
        Given jirafs is installed and configured
        When the command "jirafs clone {known_ticket_url}" is executed
        Then the output will contain the text "{known_ticket_url} cloned successfully"
