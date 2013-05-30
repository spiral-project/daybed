from cornice import Service
from colander import required

from daybed.schemas import registry


fields = Service(name='fields',
                 path='/fields',
                 description='The resource containing all the fields',
                 renderer='jsonp')


@fields.get()
def list_fields(request):
    fields = []
    # Iterate registered field types
    for name in registry.names:
        field = dict(name=name)
        # Describe field parameters using Colander children
        for parameter in registry.definition(name).children:
            if parameter.name not in ['name', 'type', 'description']:
                extras = dict(name=parameter.name,
                              description=parameter.title,
                              type=parameter.typ.__class__.__name__.lower())
                # Show default only if present
                if parameter.missing != required:
                    extras['default'] = parameter.missing
                field.setdefault('parameters', []).append(extras)
        fields.append(field)
    return fields
