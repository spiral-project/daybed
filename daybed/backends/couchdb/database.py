from . import views
from daybed.backends.exceptions import (
    UserAlreadyExist, UserNotFound, ModelNotFound,
    PolicyNotFound, PolicyAlreadyExist, RecordNotFound
)


class Database(object):
    """Object handling all the connections to the couchdb server."""

    def __init__(self, db, generate_id):
        self._db = db
        self.generate_id = generate_id

    def __get_model(self, model_id):
        try:
            doc = views.model_definitions(self._db)[model_id].rows[0]
            return doc.value
        except IndexError:
            raise ModelNotFound(model_id)

    def get_model_definition(self, model_id):
        return self.__get_model(model_id)['definition']

    def __get_records(self, model_id):
        return views.records(self._db)[model_id]

    def get_records(self, model_id):
        records = []
        for item in self.__get_records(model_id):
            item.value['data']['id'] = item.value['_id'].split('-')[1]
            records.append(item.value['data'])
        return records

    def __get_record(self, model_id, record_id):
        key = u'-'.join((model_id, record_id))
        try:
            return views.records_all(self._db)[key].rows[0].value
        except IndexError:
            raise RecordNotFound(u'(%s, %s)' % (model_id, record_id))

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

        definition_id, _ = self._db.save({
            'type': 'definition',
            '_id': model_id,
            'definition': definition,
            'roles': roles,
            'policy_id': policy_id})
        return definition_id

    def put_record(self, model_id, record, authors, record_id=None):
        doc = {
            'type': 'data',
            'authors': authors,
            'model_id': model_id,
            'data': record}

        if record_id is not None:
            try:
                old_doc = self.__get_record(model_id, record_id)
            except RecordNotFound:
                doc['_id'] = '-'.join((model_id, record_id))
            else:
                authors = list(set(authors) | set(old_doc['authors']))
                doc['authors'] = authors
                old_doc.update(doc)
                doc = old_doc
        else:
            record_id = self.generate_id()
            doc['_id'] = '-'.join((model_id, record_id))

        self._db.save(doc)
        return record_id

    def delete_record(self, model_id, record_id):
        doc = self.__get_record(model_id, record_id)
        if doc:
            self._db.delete(doc)
        return doc

    def delete_records(self, model_id):
        results = self.__get_records(model_id)
        for result in results:
            self._db.delete(result.value)
        return results

    def delete_model(self, model_id):
        """DELETE ALL THE THINGS"""

        # Delete the associated data if any.
        self.delete_records(model_id)

        try:
            doc = views.model_definitions(self._db)[model_id].rows[0].value
        except IndexError:
            raise ModelNotFound(model_id)

        # Delete the model definition if it exists.
        self._db.delete(doc)
        return doc

    def put_roles(self, model_id, roles):
        """Record roles associated to the a model.

        :param roles: is a dictionary containing the name of the role as a key
                      and the related users as a value.
        """
        doc = self.__get_model(model_id)
        doc['roles'] = roles

        self._db.save(doc)

        return doc

    def add_role(self, model_id, role_name, users):
        """Add some users to a role"""
        doc = self.__get_model(model_id)

        roles = doc['roles']
        existing_users = set(roles.get(role_name, []))
        roles[role_name] = list(existing_users | set(users))
        self._db.save(doc)

    def get_roles(self, model_id):
        """Returns the roles defined for a model.

        It returns a dict with the name of the role as a key and the users
        / groups as a list of values associated to it.

        For instance::

            {'admins': ['group:pirates', 'group:flibustiers'],
             'users': ['Remy', 'Alexis']}
        """
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

        self._db.save(doc)

    def __get_user(self, username):
        try:
            return views.users(self._db)[username].rows[0].value
        except IndexError:
            raise UserNotFound(username)

    def get_user(self, username):
        """Returns the information associated with an user"""
        user = dict(**self.__get_user(username))
        return user['user']

    def add_user(self, user):
        # Check that the user doesn't already exist.
        try:
            user = self.__get_user(user['name'])
            raise UserAlreadyExist(user['name'])
        except UserNotFound:
            pass

        user = user.copy()

        if not 'groups' in user:
            user['groups'] = []

        doc = dict(user=user, name=user['name'], type='user')
        self._db.save(doc)
        return user

    def __get_policies(self):
        return views.policies(self._db)

    def get_policies(self):
        policies = []
        for item in self.__get_policies():
            policies.append(item.value['name'])
        return policies

    def __get_policy(self, policy_name):
        try:
            doc = views.policies(self._db)[policy_name].rows[0]
            return doc.value
        except IndexError:
            raise PolicyNotFound(policy_name)

    def get_policy(self, policy_name):
        policy = self. __get_policy(policy_name)['policy']
        return policy

    def set_policy(self, policy_name, policy):
        try:
            policy = self.__get_policy(policy_name)
            raise PolicyAlreadyExist(policy_name)
        except PolicyNotFound:
            self._db.save({
                'type': 'policy',
                'name': policy_name,
                'policy': policy
            })

    def delete_policy(self, policy_name):
        doc = self.__get_policy(policy_name)
        if doc:
            self._db.delete(doc)
        return doc

    def get_model_policy(self, model_id):
        doc = self.__get_model(model_id)
        return self.get_policy(doc['policy_id'])

    def get_model_policy_id(self, model_id):
        doc = self.__get_model(model_id)
        return doc['policy_id']

    def __get_policy_definitions(self, policy_name):
        return views.policy_definitions(self._db)[policy_name]

    def policy_is_used(self, policy_name):
        definitions = self.__get_policy_definitions(policy_name)
        return len(definitions) > 0
