import json

from webtest import TestApp
from lettuce import before, step, world


@before.all
def set_browser():
    world.browser = TestApp("config:development.ini",  relative_to="./")

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

@step(u'I obtain a model id token')
def obtain_token(step):
    assert 'token' in world.response.json, 'No token received : %s' % world.response
