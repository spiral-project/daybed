import json

from lettuce import step, world


@step(u'post "([^"]*)" records?')
def post_record(step, model_name):
    world.path = '/data/%s' % str(model_name.lower())
    for record in step.hashes:
        data = json.dumps(record)
        world.response = world.browser.post(world.path, params=data, status='*')


@step(u'obtain a record id')
def obtain_a_record_id(step):
    assert 'id' in world.response.json


@step(u'retrieve the "([^"]*)" records')
def retrieve_records(step, model_name):
    world.path = '/data/%s' % str(model_name.lower())
    world.response = world.browser.get(world.path, status='*')

@step(u'results are :')
def results_are(step):
    results = world.response.json['data']
    assert len(results) >= len(step.hashes)
    for i, result in enumerate(results):
        step.hashes[i]['id'] = result['id'] # We cannot guess it
        assert result == step.hashes[i]
