Feature: Model definitions
    Model definition API usage.

    Scenario: Wrong methods and dummy data
        If I access with empty model name
        If I want to define a Mushroom
        If I access with a wrong method
        If I send "", the status is 400
        If I send "{'X'-: 4}", the status is 400

    Scenario: Malformed model definition
        When I want to define a Mushroom
        And I send "{"title": "Mushroom"}", the status is 400
        Then The error is about "description" field
        And The error is about "fields" field
        
        When I send "{"title": "Mushroom", "description": "Mushroom picking areas"}", the status is 400
        Then The error is about "fields" field

    Scenario: Malformed model fields definition
        When I want to define a Mushroom
        And I define the fields "[]", the status is 400
        Then The error is about "fields" field
        When I define the fields "[{"name": "untyped"}]", the status is 400
        Then The error is about "fields" field
        When I define the fields "[{"name": "", "type": "string", "description" : ""}]", the status is 400
        Then The error is about "fields" field
        And The error is about "fields.name" field

    Scenario: A model definition
        When I define the fields "[{"name": "place","type": "string", "description": "Where ?"}]", the status is 200
        Then I obtain a model id token
        And I retrieve the model definition

        When I want to define a Flower
        And I define a list of fields
        And I retrieve the model definition
        Then the fields order is the same

