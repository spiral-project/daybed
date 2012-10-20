from functools import partial
import json

from schemas import DefinitionValidator, SchemaValidator
import colander


def validator(request, schema):
    """Validates the request according to the given schema"""
    try:
        body = request.body
        dictbody = json.loads(body) if body else {}
        schema.deserialize(dictbody)
    except ValueError, e:
        request.errors.add('body', 'body', str(e))
    except colander.Invalid, e:
        for error in e.children:
            # here we transform the errors we got from colander into cornice
            # errors
            for field, error in error.asdict().items():
                request.errors.add('body', field, error)


#  Validates a request body according model definition schema.
definition_validator = partial(validator, schema=DefinitionValidator())


def schema_validator(request):
    """Validates a request body according to its model definition.
    """
    model_name = request.matchdict['model_name']

    definition = request.db.get_definition(model_name)
    schema = SchemaValidator(definition)
    return validator(request, schema)
