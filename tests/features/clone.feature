Feature: Cloning a ticket

    Scenario: Simple Clone
        Given jirafs is installed and configured
        When the command "jirafs clone {known_ticket_url}" is executed
        And we enter the ticket folder for "{known_ticket_url}"
        Then the output will contain the text "{known_ticket_url} cloned successfully"
        And the directory will contain a file named "static_image.png"
