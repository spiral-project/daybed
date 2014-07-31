from cornice import Service
from colander import required, drop

from daybed.schemas import registry


fields = Service(name='fields',
                 path='/fields',
                 description='The resource containing all the fields')


@fields.get()
def list_fields(request):
    common_params = ['name', 'type', 'label', 'hint', 'required']
    fields = []
    # Iterate registered field types
    for name in registry.names:
        typefield = registry.type(name)
        field = dict(name=name, default_hint=typefield.hint)
        # Describe field parameters using Colander children
        for parameter in registry.definition(name).children:
            if parameter.name not in common_params:
                fieldtype = parameter.typ.__class__.__name__.lower()
                extras = dict(name=parameter.name,
                              label=parameter.title,
                              type=fieldtype)
                # Special case for sequence
                if fieldtype == 'sequence':
                    node = parameter.children[0].typ  # sample node (first)
                    itemtype = node.__class__.__name__.lower()
                    extras['type'] = 'array'
                    extras['items'] = dict(type=itemtype)
                # Show default only if present
                if parameter.missing not in (required, drop):
                    extras['default'] = parameter.missing
                field.setdefault('parameters', []).append(extras)
        fields.append(field)
    return fields
