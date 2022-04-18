import json

from docs_and_tests.dt_init import Flow


class Registration(Flow):
    def __init__(self):
        super().__init__()
        self._get_start_page()
        self.data = {
            "email": self.register_data.get("email"),
            "password": self.register_data.get("password"),
            "actor_type": self.register_data.get("actor_type")
        }

    def registration(self):
        """
        POST /reg/ endpoint
        @subm_flow POST /reg/ endpoint
        """
        self._post_reg()


    def run(self):
        self.delete_test_user(self.register_data.get('email'))
        self.registration()


class ClassicAuthorization(Flow):
    def __init__(self):
        super().__init__()


    def authorization_flow(self):
        """
        POST /auth/ endpoint
        @subm_flow POST /auth/ endpoint
        """
        self._post_auth()

    def run(self):
        self.authorization_flow()

class CreateActor(ClassicAuthorization):
    def __init__(self):
        super().__init__()
        self.authorization_flow()

    def create_actor_flow(self):
        """
        POST /actor/ endpoint
        @subm_flow POST /actor/ endpoint
        """
        self._post_create_actor()
    def run(self):
        # self._delete_created_actor()
        self.create_actor_flow()

class CreateActorGroup(ClassicAuthorization):
    def __init__(self):
        super().__init__()
        self.authorization_flow()

    def create_actor_flow(self):
        """
        POST /actor/ endpoint
        @subm_flow POST /actor/ endpoint
        """
        self._post_create_actor()
    def run(self):
        # self._delete_created_actor()
        self.create_actor_flow()

class UpdateActor(CreateActor):
    def __init__(self):
        super().__init__()
        self.authorization_flow()

    def update_actor(self):
        """
        POST /update/actor/ endpoint
        @subm_flow POST /update/actor/ endpoint
        """
        self._update_actor_data()


    def run(self):
        self.update_actor()

class SetPermactionActor(CreateActor):
    def __init__(self):
        super().__init__()
        self.authorization_flow()

    def post_set_permaction_actor(self):
        """
        POST /permaction/actor/ endpoint
        @subm_flow POST /permaction/actor/ endpoint
        """
        self._post_perm_actor()


    def run(self):
        self.post_set_permaction_actor()

class DeletePermactionActor(CreateActor):
    def __init__(self):
        super().__init__()
        self.authorization_flow()

    def post_set_permaction_actor(self):
        """
        DELETE /permaction/actor/ endpoint
        @subm_flow DELETE /permaction/actor/ endpoint
        """
        self._delete_permactions_actor()


    def run(self):
        self.post_set_permaction_actor()

class SetPermactionGroup(CreateActor):
    def __init__(self):
        super().__init__()
        self.authorization_flow()

    def post_set_permaction_group(self):
        """
        POST /permaction/group/ endpoint
        @subm_flow POST /permaction/group/ endpoint
        """
        self._post_set_permaction_group()
        self.send_callback()

    def run(self):
        self.post_set_permaction_group()

class DeletePermactionGroup(CreateActor):
    def __init__(self):
        super().__init__()
        self.authorization_flow()

    def post_set_permaction_actor(self):
        """
        DELETE /permaction/group/ endpoint
        @subm_flow DELETE /permaction/group/ endpoint
        """
        self._delete_permaction_group()


    def run(self):
        self.post_set_permaction_actor()



#
class DeleteActor(CreateActor):
    def __init__(self):
        super().__init__()
        self.authorization_flow()

    def delete_actor(self):
        """
        DELETE /actor/ endpoint
        @subm_flow DELETE /actor/ endpoint
        """
        self._delete_actor()


    def run(self):
        self.delete_actor()

class SyncGetHash(ClassicAuthorization):
    def __init__(self):
        super().__init__()
        self.authorization_flow()

    def sync_get_hash(self):
        """
        POST /synchronization/get_hash/
        @subm_flow POST /synchronization/get_hash/
        """
        self._get_hash()

    def run(self):
        self.sync_get_hash()
