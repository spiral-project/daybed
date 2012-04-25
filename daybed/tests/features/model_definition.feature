Feature: Model definition API simple usage
    Simple use-case to create and retrieve a model

    Scenario: Nominal use-case
        If I define a correct "Mushroom" with correct fields
        Then the status is 200
        And I obtain a model id token

        If I retrieve the "Mushroom" definition
        Then the status is 200
        And the fields order is the same
