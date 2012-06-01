import json

from lettuce import step, world

@step(u'post "([^"]*)" records?')
def post_record(step, modelname):
    world.path = '/%s' % str(modelname.lower())
    for record in step.hashes:
        data = json.dumps(record)
        world.response = world.browser.post(world.path, params=data, status='*')


@step(u'obtain a record id')
def obtain_a_record_id(step):
    assert 'id' in world.response.json


@step(u'retrieve the "([^"]*)" records')
def retrieve_records(step, modelname):
    world.path = '/%s' % str(modelname.lower())
    world.response = world.browser.get(world.path, status='*')

@step(u'results are :')
def results_are(step):
    results = world.response.json['data']
    assert len(results) >= len(step.hashes)
    for i, result in enumerate(results):
        assert result == step.hashes[i]
