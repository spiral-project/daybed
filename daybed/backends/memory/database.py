from copy import deepcopy

from daybed.backends.exceptions import (
    UserAlreadyExist, UserNotFound, ModelNotFound,
    PolicyNotFound, PolicyAlreadyExist, DataItemNotFound
)


class Database(object):
    """Object handling all the db interactions."""

    def __init__(self, db, generate_id):
        self._db = db
        self.generate_id = generate_id

    def __get_model(self, model_id):
        try:
            return deepcopy(self._db['models'][model_id])
        except KeyError:
            raise ModelNotFound(model_id)

    def get_model_definition(self, model_id):
        return self.__get_model(model_id)['definition']

    def __get_records(self, model_id):
        # Check that model_id exists and raises if not.
        self.__get_model(model_id)
        return self._db['data'].get(model_id, {}).values()

    def get_records(self, model_id):
        records = []
        for item in self.__get_records(model_id):
            item['data']['id'] = item['_id']
            records.append(deepcopy(item['data']))
        return records

    def __get_record(self, model_id, record_id):
        try:
            return deepcopy(self._db['data'][model_id][record_id])
        except KeyError:
            raise DataItemNotFound(u'(%s, %s)' % (model_id, record_id))

    def get_record(self, model_id, record_id):
        doc = self.__get_record(model_id, record_id)
        return doc['data']

    def get_record_authors(self, model_id, record_id):
        doc = self.__get_record(model_id, record_id)
        return doc['authors']

    def put_model(self, definition, roles, policy_id, model_id=None):
        if model_id is None:
            model_id = self.generate_id()

        # Check that policyid exists and raises if not.
        self.get_policy(policy_id)

        self._db['models'][model_id] = {
            'type': 'definition',
            '_id': model_id,
            'definition': definition,
            'roles': roles,
            'policy_id': policy_id
        }
        self._db['data'][model_id] = {}
        return model_id

    def put_record(self, model_id, data, authors, record_id=None):
        doc = {
            'type': 'data',
            'authors': authors,
            'model_id': model_id,
            'data': data
        }

        if record_id is not None:
            try:
                old_doc = self.__get_record(model_id, record_id)
            except DataItemNotFound:
                doc['_id'] = record_id
            else:
                authors = list(set(authors) | set(old_doc['authors']))
                doc['authors'] = authors
                old_doc.update(doc)
                doc = old_doc
        else:
            record_id = self.generate_id()
            doc['_id'] = record_id

        self._db['data'][model_id][record_id] = doc
        return record_id

    def delete_record(self, model_id, record_id):
        doc = self.__get_record(model_id, record_id)
        if doc:
            del self._db['data'][model_id][record_id]
        return doc

    def delete_records(self, model_id):
        results = self.__get_records(model_id)
        for result in results:
            self.delete_record(model_id, result['_id'])
        return results

    def delete_model(self, model_id):
        self.delete_records(model_id)
        del self._db['models'][model_id]

    def put_roles(self, model_id, roles):
        doc = self.__get_model(model_id)
        doc['roles'] = roles
        self._db['models'][model_id] = doc
        return doc

    def add_role(self, model_id, role_name, users):
        doc = self.__get_model(model_id)
        roles = doc['roles']
        existing_users = set(roles.get(role_name, []))
        roles[role_name] = list(existing_users | set(users))
        self._db['models'][model_id] = doc

    def get_roles(self, model_id):
        doc = self.__get_model(model_id)
        return doc['roles']

    def get_groups(self, username):
        """Return the groups for a specific user"""
        return self.get_user(username)['groups']

    def add_group(self, username, group):
        """Adds an user to an existing group"""
        doc = self.__get_user(username)
        groups = doc['user']['groups']
        if not group in groups:
            groups.append(group)
        self._db['users'][username] = doc

    def __get_user(self, username):
        try:
            return deepcopy(self._db['users'][username])
        except KeyError:
            raise UserNotFound(username)

    def get_user(self, username):
        """Returns the information associated with an user"""
        user = self.__get_user(username)
        return user['user']

    def add_user(self, user):
        # Check that the user doesn't already exist.
        try:
            username = user['name']
            user = self.__get_user(username)
            raise UserAlreadyExist(username)
        except UserNotFound:
            pass

        user = user.copy()

        if not 'groups' in user:
            user['groups'] = []

        doc = dict(user=user, name=username, type='user')
        self._db['users'][username] = doc
        return user

    def get_policies(self):
        policies = []
        for item in self._db['policies'].values():
            policies.append(item['name'])
        return policies

    def __get_policy(self, policy_name):
        try:
            return self._db['policies'][policy_name]
        except KeyError:
            raise PolicyNotFound(policy_name)

    def get_policy(self, policy_name):
        policy = self. __get_policy(policy_name)['policy']
        return policy

    def set_policy(self, policy_name, policy):
        try:
            self.__get_policy(policy_name)
            raise PolicyAlreadyExist(policy_name)
        except PolicyNotFound:
            self._db['policies'][policy_name] = {
                'type': 'policy',
                'name': policy_name,
                'policy': policy
            }

    def delete_policy(self, policy_name):
        doc = self.__get_policy(policy_name)
        if doc:
            del self._db['policies'][policy_name]
        return doc

    def get_model_policy(self, model_id):
        doc = self.__get_model(model_id)
        return self.get_policy(doc['policy_id'])

    def get_model_policy_id(self, model_id):
        doc = self.__get_model(model_id)
        return doc['policy_id']

    def policy_is_used(self, policy_name):
        for model in self._db['models'].values():
            policy = model['policy_id']
            if policy == policy_name:
                return True
        return False
