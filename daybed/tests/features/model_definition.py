from webtest import TestApp
from lettuce import before, after, step, world

from daybed import sync_couchdb_views


@before.all
def set_browser():
    browser = TestApp("config:development.ini",  relative_to=".")
    world.db_name = 'daybed-tests'
    browser.app.registry.settings['db_name'] = world.db_name
    db = browser.app.registry.settings['db_server'].create(world.db_name)
    sync_couchdb_views(db)
    world.browser = browser


@after.all
def destroy_db(step):
    del world.browser.app.registry.settings['db_server'][world.db_name]


@step(u'define an? (empty|malformed|incorrect|incomplete|correct) "([^"]*)" with (no|empty|malformed|incorrect|incomplete|unamed|correct|nochoice) fields')
def define_model_and_fields(step, modelaspect, model_name, fieldsaspect):
    modelaspects = {
        'empty': "{%s}",
        'malformed': '{"X"-: 4 %s}',
        'incorrect': '{"X": 4 %s}',
        'incomplete': '{"title": "Mushroom" %s}',
        'correct': '{"title": "Mushroom", "description": "Mushroom picking areas" %s}',
    }
    
    fieldsaspects = {
        'no': '',
        'empty': ', "fields": []',
        'malformed': ', "fields": [{"na"me": -"untyped"}]',
        'incorrect': ', "fields": [{"name": "strange", "type": "antigravity", "description" : 3}]',
        'incomplete': ', "fields": [{"name": "untyped", "description" : "no type"}]',
        'nochoice': ', "fields": [{"name": "choice", "type": "enum", "description" : "no choices"}]',
        'unamed': ', "fields": [{"name": "", "type": "string", "description" : ""}]',
        'correct': """, "fields": [
            {"name": "place", "type": "string", "description": "Where ?"},
            {"name": "size", "type": "int", "description": "How big ?"},
            {"name": "datetime", "type": "string", "description": "When ?"},
            {"name": "category", "type": "enum", "description": "What kind ?", "choices": ["beast", "zombie"]}
        ]
        """,
    }
    
    world.fields_order = []
    if fieldsaspect == 'correct':
        world.fields_order = [u'place', u'size', u'datetime', 'category']
    
    world.path = '/definitions/%s' % str(model_name.lower())

    if hasattr(world, 'token'):
        world.path += '?token=%s' % str(world.token)

    model = modelaspects[modelaspect] % fieldsaspects[fieldsaspect]
    world.response = world.browser.put(world.path, params=model, status='*')


@step(u'the status is (\d+)')
def status_is(step, status):
    expected = world.response.status
    assert expected.startswith(status), "Unexpected status %s" % expected


@step(u'post a correct "([^"]*)" with correct fields')
def post_correct_model(step, model_name):
    world.path = '/definitions/%s' % str(model_name.lower())
    model = """ {"title": "hey", "description": "ho", "fields": [
        {"name": "place", "type": "string", "description": "Where ?"}
    ]
    }
    """
    world.response = world.browser.post(world.path, params=model, status='*')


@step(u'the error is about fields? (".+",?)*')
def error_is_about_fields(step, fields):
    _json = world.response.json
    assert 'error' == _json.get('status'), 'Response has no error status'
    errors = dict([(f.get('name'), f.get('description')) for f in _json['errors']])
    errorfields = sorted(errors.keys())
    if fields:
        fields = fields.replace(' ', '').replace('"', '').split(',')
        for field in fields:
            assert field in errorfields, 'Error about "%s" not raised' % field
        for errorfield in errorfields:
            assert errorfield in fields, 'Unexpected error about "%s" : %s' % (errorfield, errors[errorfield])


@step(u'retrieve the "([^"]*)" definition')
def retrieve_the_model_definition(step, model_name):
    world.path = '/definitions/%s' % str(model_name.lower())
    world.response = world.browser.get(world.path, status='*')


@step(u'the fields order is the same')
def the_fields_order_is_the_same(step):
    fields = [f['name'] for f in world.response.json['fields']]
    assert world.fields_order == fields, '%r != %r' % (world.fields_order, fields)


@step(u'obtain a model id token')
def obtain_token(step):
    assert 'token' in world.response.json, 'No token received : %s' % world.response


@step(u'provide (no|bad|same) token')
def provide_token(step, tokenaspect):
    tokenaspects = {
        'no': None,
        'bad': '12345',
        'same': world.response.json.get('token')
    }
    world.token = tokenaspects[tokenaspect]
