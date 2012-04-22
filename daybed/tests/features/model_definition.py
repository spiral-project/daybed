import json

from webtest import TestApp
from lettuce import before, after, step, world


@before.all
def set_browser():
    browser = TestApp("config:development.ini",  relative_to=".")
    world.db_name = 'daybed-tests'
    browser.app.registry.settings['db_name'] = world.db_name
    browser.app.registry.settings['db_server'].create(world.db_name)
    world.browser = browser

@after.all
def destroy_db(step):
    del world.browser.app.registry.settings['db_server'][world.db_name]

@step(u'I access with empty model name')
def access_empty_model_name(step):
    path = '/definition'
    world.browser.put(path, status=404)
    world.browser.post(path, status=404)
    world.browser.get(path, status=404)

@step(u'I want to define a (.*)')
def define(step, name):
    world.name = name
    world.path = '/definition/%s' % str(name.lower())

@step(u'I access with a wrong method')
def access_wrong_method(step):
    world.browser.post(world.path, status=405)

@step(u'I send "(.*)", the status is (\d+)')
def sending_and_receive(step, data, status):
    world.response = world.browser.put(world.path, params=data, status=int(status))

@step(u'The error is about "(.*)" field')
def error_field_is(step, field):
    _json = world.response.json
    assert 'error' == _json.get('status'), 'Response has no error status'
    fields = [f['name'] for f in _json['errors']]
    assert field in fields, 'Field "%s" has no error' % field

@step(u'I define the fields "(.*)", the status is (\d+)')
def define_fields_and_receive(step, fields, status):
    data = dict(
        title=world.name.capitalize(),
        description=world.name,
        fields=json.loads(fields),
    )
    world.response = world.browser.put(world.path, params=json.dumps(data), status=int(status))

@step(u'I define a list of fields')
def define_a_list_of_fields(step):
    fields = """[
        {"name": "place", "type": "string", "description": "Where ?"},
        {"name": "size", "type": "int", "description": "How big ?"},
        {"name": "datetime", "type": "string", "description": "When ?"}
    ]
    """
    world.fields_order = [u'place', u'size', u'datetime']
    define_fields_and_receive(step, fields, 200)

@step(u'I obtain a model id token')
def obtain_token(step):
    assert 'token' in world.response.json, 'No token received : %s' % world.response

@step(u'I retrieve the model definition')
def retrieve_the_model_definition(step):
    world.response = world.browser.get(world.path, status=200)

@step(u'Then the fields order is the same')
def then_the_fields_order_is_the_same(step):
    fields = [f['name'] for f in world.response.json['fields']]
    assert world.fields_order == fields, '%r != %r' % (world.fields_order, fields)

