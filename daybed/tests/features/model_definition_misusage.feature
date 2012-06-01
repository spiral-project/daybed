Feature: Model definition API always behaves nicely
    Examples of some bad usage and malformed model definitions.
    The API should always return appropriate status and maximum of
    details about errors.

    Scenario: Wrong methods and bad data
        If I define a correct "" with correct fields
        Then the status is 404

        If I post a correct "Model" with correct fields
        Then the status is 405

    Scenario: Unknown model
        If I retrieve the "Schlimblick" definition
        Then the status is 404

    Scenario: Malformed model definition
        If I define a <model> "Model" with <fields> fields
        Then the status is <status>
        And the error is about fields <errors>

    Examples:
        | model      | fields     | status | errors                                  |
        | empty      | no         | 400    | "description", "title", "fields"        |
        | empty      | correct    | 400    | "body"                                  |
        | malformed  | correct    | 400    | "body"                                  |
        | incorrect  | correct    | 400    | "description", "title"                  |
        | incomplete | correct    | 400    | "description"                           |
        
        | correct    | no         | 400    | "fields"                                |
        | correct    | empty      | 400    | "fields"                                |
        | correct    | malformed  | 400    | "body"                                  |
        | correct    | incorrect  | 400    | "fields.0.type"                         |
        | correct    | incomplete | 400    | "fields.0.type"                         |
        | correct    | unamed     | 400    | "fields.0.name", "fields.0.description" |
        | correct    | nochoice   | 400    | "fields.0.choices"                      |
