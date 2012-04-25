Feature: Model data posting, simple usage
    Simple use-case to post and retrieve model data

    Scenario: Nominal use-case
        Given I define a correct "Event" with correct fields
        If I post "Event" records
          | size | place     | datetime   |
          | 14   | Holy wood | 2012-04-25 |
        Then the status is 200
        And I obtain a record id
    
    Scenario: Retrieve records
        If I retrieve the "Event" records
        Then the status is 200
        And the results are :
          | size | place     | datetime   |
          | 14   | Holy wood | 2012-04-25 |
