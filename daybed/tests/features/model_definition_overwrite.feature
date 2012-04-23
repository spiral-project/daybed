Feature: Model definition overwrite
    Simple use-case to update/overwrite a model definition

    Scenario: Defining a model works
        If I define a correct "Tree" with correct fields
        Then the status is 200
        And I obtain a model id token
    
    Scenario: Fails if no token is given
        If I provide no token
        And I define a correct "Tree" with correct fields
        Then the status is 403
        And the error is about field "token"
    
    Scenario: Fails if token is wrong    
        If I provide bad token
        And I define a correct "Tree" with correct fields
        Then the status is 403
        And the error is about field "token"

    Scenario: Success if token is correct
        If I define a correct "Flower" with correct fields
        Then the status is 200
        And I obtain a model id token
        
        If I provide same token
        And I define a correct "Flower" with correct fields
        Then the status is 200
        And I obtain a model id token
