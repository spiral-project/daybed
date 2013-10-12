import json

from cornice import Service
from pyramid.httpexceptions import HTTPNotFound, HTTPConflict, HTTPForbidden

from daybed.validators import validate_against_schema
from daybed.schemas import PolicyValidator
from daybed.backends.exceptions import PolicyAlreadyExist, PolicyNotFound

policies = Service(name='policies', path='/policies')

policy = Service(name='policy', path='/policies/{policy_id}',
                 description='Policy', renderer="jsonp", cors_origins=('*',))


def policy_validator(request):
    policy = json.loads(request.body)
    validate_against_schema(request, PolicyValidator(policy), policy)
    request.validated['policy'] = policy


@policies.get()
def get_policies(request):
    return request.db.get_policies()


@policy.delete()
def delete_policy(request):
    """Deletes a policy and its matching associated data."""
    policy_id = request.matchdict['policy_id']
    # Test if somebody is using the policy.
    if not request.db.policy_is_used(policy_id):
        request.db.delete_policy(policy_id)
        return "ok"
    return HTTPForbidden("%s is used by some models." % policy_id)


@policy.get()
def get_policy(request):
    """Returns the full policy definition."""
    policy_id = request.matchdict['policy_id']

    try:
        policy = request.db.get_policy(policy_id),
    except PolicyNotFound:
        raise HTTPNotFound()

    return policy


@policy.put(validators=(policy_validator,))
def put_policy(request):
    policy_id = request.matchdict['policy_id']

    try:
        request.db.set_policy(policy_id, request.validated['policy'])
    except PolicyAlreadyExist:
        raise HTTPConflict('%s already exists.' % policy_id)
    return "ok"
