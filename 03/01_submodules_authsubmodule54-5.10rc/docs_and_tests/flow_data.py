import json

from flask import current_app

from auth_perms.core.ecdsa_lib import sign_data


class Flow:
    def __init__(self):
        self.app = current_app
        self.language = "en"
        self.flow_app = self.app.test_client()
        self.register_data = {
            "uinfo": {"first_name": "DT_test", "last_name": "DT_test"},
            "email": 'umistalker@gmail.com',

            "password": 'mark',
            "password_confirmation": 'mark',
            "actor_type": "classic_user",
        }
        self.auth_data = {
            "email": 'mark@gmail.com',
            "password": 'mark',
            "actor_type": "classic_user",
        }

        self.create_actor_data = {'actor_type': 'classic_user',
                                  'uinfo': {'email': 'qwe@gmail.com', 'password': 'madamkda'}}
        self.create_actor_data2 = {'actor': {'uuid': '5648ee1f-85db-47ee-bb06-15065970a9d9',
                                             'root_perms_signature': None,
                                             'initial_key': None,
                                             'secondary_keys': None,
                                             'uinfo': {'email': 'umi234st3123@gmail.com',
                                                       'groups': ['4c97a2dc-c0df-4af0-a5c7-1753c46ca2e1'],
                                                       'birthday': None, 'password': 'ab56f1093b99e873092e51312fd36643',
                                                       'last_name': '123123', 'first_name': '123123'},
                                             'actor_type': 'classic_user'},
                                   'object_uuid': '5648ee1f-85db-47ee-bb06-15065970a9d9',
                                   'sync_package_id': 280,
                                   'service_uuid': 'd2275413-2bf6-44c3-9f8b-8143f88f9d66'}
        self.create_actor_data_update = {'actors': [{'uuid': '5648ee1f-85db-47ee-bb06-15065970a9d9',
                                                     'root_perms_signature': None,
                                                     'initial_key': None,
                                                     'secondary_keys': None,
                                                     'uinfo': {'email': 'umi234st3123@gmail.com',
                                                               'groups': ['4c97a2dc-c0df-4af0-a5c7-1753c46ca2e1'],
                                                               'birthday': None,
                                                               'password': 'ab56f1093b99e873092e51312fd36643',
                                                               'last_name': '123123', 'first_name': '123123'},
                                                     'actor_type': 'classic_user'}],
                                         'object_uuid': '5648ee1f-85db-47ee-bb06-15065970a9d9',
                                         'sync_package_id': 280,
                                         'service_uuid': 'd2275413-2bf6-44c3-9f8b-8143f88f9d66'}

        self.set_permaction_actor = {'actors': [{'uuid': '967e0917-ef22-4939-beeb-4c871cd77dc7',
                                                 'root_perms_signature': None,
                                                 'initial_key': '047503b6e92680cd6882c24a4aea3fd537dadbbba1a342c1a22202c395c55bcd06afb8f5dc9cc26462c4dcc9459c8ff5a9f2bf1c32a1bddd5d8fd312a44dda36we',
                                                 'secondary_keys': None,
                                                 'uinfo': {'service_name': 'test_test',
                                                           'service_domain': 'http://192.168.1.138:3001'},
                                                 'actor_type': 'service'}],
                                     'object_uuid': '967e0917-ef22-4939-beeb-4c871cd77dc7',
                                     'sync_package_id': 283,
                                     'service_uuid': 'd2275413-2bf6-44c3-9f8b-8143f88f9d66'}

        self.create_actor_group_data = {'actor_type': 'group',
                                        'uinfo': {'weight': '100', 'group_name': 'test_group_123'}}

    def actor_uuid(self, ):
        with self.app.db.get_cursor() as cur:
            cur.execute(
                "SELECT uuid FROM actor WHERE uinfo->>'email' = 'umistalker@gmail.com'",
            )
            actor_uuid = cur.fetchone().get("uuid")
        return actor_uuid

    def _get_session_token(self):
        """
        Get current session token
        @subm_flow
        """
        with self.app.db.get_cursor() as cur:
            cur.execute(
                "SELECT session_token FROM service_session_token WHERE uuid = 'ce42c1bc-85cd-46e8-9f62-aa70500fc2fd' ORDER BY created DESC ")
            session_token = cur.fetchone()
            for key, value in session_token.items():
                return value

    def _post_create_actor(self):
        """
        Create new user
        @subm_flow Create new user
        """
        data = self.create_actor_data2
        data['signature'] = self.get_signature(self.create_actor_data2)
        self.flow_app.post(
            f"/actor/",
            json=data,
            headers={
                'content-type': 'application/json',
                'session-token': self._get_session_token(),
            }
        )

    def _get_start_page(self):
        """
        Get start page flow
        @subm_flow Get start page flow
        """
        self.flow_app.get(f"/")

    def _post_reg(self):
        """
        POST /reg/
        @subm_flow POST /reg/
        """
        self.flow_app.post(
            "/reg/",
            data=json.dumps(self.register_data),
            content_type="application/json",
        )

    def _post_auth(self, data=None):
        """
        POST /auth/
        @subm_flow POST /auth/
        """
        if not data:
            data = self.auth_data
        self.flow_app.post(
            "/auth/",
            data=json.dumps(data),
            content_type='application/json',
        )

    def delete_test_user(self, email):
        self.app.db.execute(
            "DELETE FROM actor WHERE uinfo->>'email' = %s", [email]
        )

    def _delete_created_actor(self):
        self.app.db.execute(
            "DELETE FROM actor WHERE uinfo->>'email' = 'qwe@gmail.com'"
        )

    def _post_get_actor_by_uuid(self):
        """
        POST Get actor by UUID
        @subm_flow POST Get actor by UUID
        """
        self.flow_app.post(
            f"/get/actor/7b96aa74-15cc-412e-aea2-4b09ce156059",
            headers={
                'content-type': 'application/json',
                'session-token': self._get_session_token()
            }
        )

    def _get_about_page(self):
        """
        GET /about/ endpoint
        @subm_flow  GET /about/ endpoint
        """
        self.flow_app.get(
            '/about/'
        )

    def _get_auth_admin(self):
        """
         GET /auth_admin/ endpoint
        @subm_flow  GET /auth_admin/ endpoint
        """
        self.flow_app.get(
            '/auth_admin/'
        )

    def _get_auth_admin_actors(self):
        """
         GET /auth_admin/actors/ endpoint
        @subm_flow  GET /auth_admin/actors/ endpoint
        """
        self.flow_app.get(
            '/auth_admin/actors/'
        )

    def _get_auth_admin_profile(self):
        """
         GET /auth_admin/actors/ endpoint
        @subm_flow  GET /auth_admin/actors/ endpoint
        """
        self.flow_app.get(
            "/auth_admin/profile/"
        )

    def _update_actor_data(self):
        """
        POST Update actor
        @subm_flow  Update actor
        """
        data = self.create_actor_data_update
        data['signature'] = self.get_signature(self.create_actor_data_update)

        self.flow_app.put(
            '/actor/',
            json=data,
            headers={
                'content-type': 'application/json',
                'session-token': self._get_session_token()
            },

        )

    def _post_append_user_on_group(self):
        """
        POST Append user on group
        @subm_flow Append user on group
        """
        self.flow_app.post(
            '/append/group/',
            data=json.dumps(
                {'actor_type': 'classic_user',
                 'root_perms_signature': None,
                 'secondary_keys': None,
                 'uinfo': {'email': 'qwe@gmail.com', 'groups': ['cc2f6ce2-c473-4741-99f6-fd7aec45d073']},
                 'uuid': self.actor_uuid()}
            ),
            headers={
                'content-type': 'application/json',
                'session-token': self._get_session_token()
            },

        )

    def _post_delete_user_in_group(self):
        """
        POST Delete user on group
        @subm_flow Delete user on group
        """
        self.flow_app.post(
            '/append/group/',
            data=json.dumps(
                {'actor_type': 'classic_user', 'created': 'Fri, 25 Mar 2022 11:17:42 GMT',
                 'root_perms_signature': None,
                 'secondary_keys': None,
                 'uinfo': {'email': 'qwe@gmail.com', 'groups': []},
                 'uuid': self.actor_uuid()}
            ),
            headers={
                'content-type': 'application/json',
                'session-token': self._get_session_token()
            },

        )

    def permaction_uuid(self):
        with self.app.db.get_cursor() as cur:
            cur.execute(
                "SELECT permaction_uuid FROM default_permaction WHERE title = 'Append group'",
            )
            actor_uuid = cur.fetchone()
            for key, value in actor_uuid.items():
                return value

    def service_uuid(self):
        with self.app.db.get_cursor() as cur:
            cur.execute(
                "SELECT uuid FROM actor WHERE actor_type = 'service'",
            )
            actor_uuid = cur.fetchone()
            for key, value in actor_uuid.items():
                return value

    def _post_perm_actor(self):
        """
        POST /permaction/actor/ endpoint
        @subm_flow POST /permaction/actor/ endpoint
        """
        data = {'permactions': [{'permaction_uuid': '5645021d-4f15-4b23-8a85-3b2ca16eb97e',
                                 'actor_uuid': self.actor_uuid(),
                                 'service_uuid': 'd2275413-2bf6-44c3-9f8b-8143f88f9d66',
                                 'value': 1,
                                 'params': {}}],
                'object_uuid': '5648ee1f-85db-47ee-bb06-15065970a9d9',
                'sync_package_id': 280,
                'service_uuid': 'd2275413-2bf6-44c3-9f8b-8143f88f9d66'}
        data['signature'] = self.get_signature(data)
        self.flow_app.post(
            '/permaction/actor/',
            json=data,
            headers={
                'content-type': 'application/json',
                'session-token': self._get_session_token()
            },
        )

    def get_signature(self, data):
        """
        Get signature
        @subm_flow Get signature
        """
        signature = sign_data(current_app.config['SERVICE_PRIVATE_KEY'],
                              json.dumps(data, sort_keys=True))

        return signature

    def _post_create_group(self):
        """
        Create group POST /actor/ endpoint
        @subm_flow  Create group POST  /actor/ endpoint
        """
        self.flow_app.post(
            '/create/actor/',
            data=json.dumps(self.create_actor_group_data),
            headers={
                'content-type': 'application/json',
                'session-token': self._get_session_token()
            },
        )

    def get_group_uuid(self):
        with self.app.db.get_cursor() as cur:
            cur.execute(
                "SELECT uuid FROM actor WHERE uinfo->>'group_name'= 'test_group_123'",
            )
            actor_uuid = cur.fetchone().get("uuid")
        return actor_uuid

    def _post_set_permaction_group(self):
        """
        POST /permaction/group/ endpoint
        @subm_flow POST /permaction/group/ endpoint
        """
        data = {'permactions': [{'permaction_uuid': '5645021d-4f15-4b23-8a85-3b2ca16eb97e',
                                 'actor_uuid': self.actor_uuid(),
                                 'service_uuid': 'd2275413-2bf6-44c3-9f8b-8143f88f9d66',
                                 'value': 1,
                                 'weight': 12,
                                 'params': {}}],
                'object_uuid': '5648ee1f-85db-47ee-bb06-15065970a9d9',
                'sync_package_id': 280,
                'service_uuid': 'd2275413-2bf6-44c3-9f8b-8143f88f9d66'}
        data['signature'] = self.get_signature(data)
        self.flow_app.post(
            '/permaction/group/',
            json=data,
            headers={
                'content-type': 'application/json',
                'session-token': self._get_session_token()
            },
        )

    def _delete_permactions_actor(self):
        """
       DELETE /permaction/actor/ endpoint
       @subm_flow DELETE /permaction/actor/ endpoint
       """
        data = {'permactions': [{'permaction_uuid': '5645021d-4f15-4b23-8a85-3b2ca16eb97e',
                                 'actor_uuid': self.actor_uuid(),
                                 'service_uuid': 'd2275413-2bf6-44c3-9f8b-8143f88f9d66',
                                 'value': 1,
                                 'params': {}}],
                'object_uuid': '5648ee1f-85db-47ee-bb06-15065970a9d9',
                'sync_package_id': 280,
                'service_uuid': 'd2275413-2bf6-44c3-9f8b-8143f88f9d66'}
        data['signature'] = self.get_signature(data)
        self.flow_app.post(
            '/permaction/actor/',
            json=data,
            headers={
                'content-type': 'application/json',
                'session-token': self._get_session_token()
            },
        )

    def _delete_permaction_group(self):
        """
       DELETE /permaction/group/ endpoint
       @subm_flow DELETE /permaction/group/ endpoint
       """
        data = {'permactions': [{'permaction_uuid': '5645021d-4f15-4b23-8a85-3b2ca16eb97e',
                                 'actor_uuid': self.actor_uuid(),
                                 'service_uuid': 'd2275413-2bf6-44c3-9f8b-8143f88f9d66',
                                 'value': 1,
                                 'weight': 12,
                                 'params': {}}],
                'object_uuid': '5648ee1f-85db-47ee-bb06-15065970a9d9',
                'sync_package_id': 280,
                'service_uuid': 'd2275413-2bf6-44c3-9f8b-8143f88f9d66'}
        data['signature'] = self.get_signature(data)
        self.flow_app.delete(
            '/permaction/group/',
            json=data,
            headers={
                'content-type': 'application/json',
                'session-token': self._get_session_token()
            },
        )

    def _delete_actor(self):
        """
        POST /actor/ endpoint
        @subm_flow POST /actor/ endpoint
        """
        data = self.create_actor_data2
        data['signature'] = self.get_signature(self.create_actor_data2)
        self.flow_app.delete(
            f"/actor/",
            json=data,
            headers={
                'content-type': 'application/json',
                'session-token': self._get_session_token()
            }
        )

    def send_callback(self):
        """
        Send callback request on auth service, that information was updated on service.
        @subm_flow
        """
        pass

    def _get_hash(self):
        """
        Get hash
        @subm_flow Get hash
        """
        self.flow_app.post(
            '/synchronization/get_hash/',
            data=json.dumps({
                'service_uuid': self.service_uuid(),
                'signature': self.get_signature({'service_uuid': self.service_uuid()})
            }),
            headers={
                'content-type': 'application/json',
                'session-token': self._get_session_token()
            }
        )

    def _get_sync_info(self):
        """
        Get sync info
        @subm_flow Get sync info
        """

        self.flow_app.post(
            '/services/synchronization_info',
            headers={
                'content-type': 'application/json',
                'session-token': self._get_session_token()
            }
        )

    def _post_save_session(self):
        """
        Save session
        @subm_flow Save session
        """

        self.flow_app.post(
            '/save_session/',
            headers={
                'content-type': 'application/json',
                'session-token': self._get_session_token()
            }
        )

