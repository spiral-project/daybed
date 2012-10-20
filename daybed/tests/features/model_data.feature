Feature: Model data posting, simple usage
    Simple use-case to post and retrieve model data

    Scenario: Unknown model
        If I retrieve the "Schlimblick" records
        Then the status is 404

    Scenario: Nominal use-case
        Given I define a correct "Event" with correct fields
        Then the status is 200
        If I post "Event" records
          | size | place     | datetime   | category |
          | 14   | Holy wood | 2012-04-25 | beast    |
          | 110  | 日本語     | 2012-06-01 | beast    |
        Then the status is 201
        And I obtain a record id

    Scenario: Retrieve records
        If I retrieve the "Event" records
        Then the status is 200
        And the results are :
          | size | place     | datetime   | category |
          | 14   | Holy wood | 2012-04-25 | beast    |
          | 110  | 日本語     | 2012-06-01 | beast    |

    Scenario: Malformed posted data
        If I post "Event" record
          | size | place     | datetime   | category |
          | abc  | Holy wood | 2012-04-25 | elf      |
        Then the status is 400
        And the error is about fields "size", "category"
