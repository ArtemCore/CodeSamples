"""
Communication with other services as actor with session.
BaseServiceCommunication base class for getting apt54 and session_token on target service and adding it in send_request
method. This is required for using functionality of some other service like usual actor.
"""
import json
from collections import namedtuple
from typing import Dict
from urllib.parse import urljoin

import requests
from flask import current_app as app
from flask_babel import gettext as _

from .actions.actor_actions import (CreateActorAction, DeleteActorAction,
                                    UpdateActorAction)
from .actor import Actor
from .ecdsa_lib import sign_data
from .exceptions import (ServiceAPT54Error, ServiceInvalidData,
                         ServiceIsNotActorError, ServiceRequestError,
                         ServiceSaltError, ServiceSessionError)
from .utils import (apt54_expired, create_response_message,
                    get_language_header, json_dumps)


class BaseServiceCommunication:
    """
    Base class for service-service communication as actor.
    """

    def __init__(self, service=None):
        if service and not isinstance(service, Actor):
            raise ServiceIsNotActorError("Unknown service type")

        self.standalone_message = {
            "error": True,
            "message": "You're in standalone mode.",
        }

        self.default_class = namedtuple(
            "MockClass",
            ("data", "execute",),
            defaults=(None, lambda: self.standalone_message),
        )

        self._local_handlers = {
            "/create/actor": CreateActorAction,
            "/update/actor": UpdateActorAction,
            "/delete/actor": DeleteActorAction,
        }

        self.auth_service = (
            Actor.objects.get(initial_key=app.config["AUTH_PUB_KEY"])
            if not app.config.get("AUTH_STANDALONE")
            else None
        )

        self.endpoint = None
        self.service = service or self.auth_service
        self.method = "post"

    def get_apt54(self):
        """
        Get service apt54 from database.
        """
        apt54 = app.db.fetchone(
            """SELECT apt54 FROM service_session_token WHERE uuid = %s AND service_uuid = %s""",
            [app.config["SERVICE_UUID"], self.service.uuid],
        )

        if not apt54:
            apt54 = self.update_apt54()
        else:
            apt54 = apt54.get("apt54")
            if apt54_expired(apt54.get("expiration")):
                apt54 = self.update_apt54()

        return apt54

    def update_apt54(self):
        """
        Get new apt54 for your service.
        """
        url = urljoin(self.auth_service.uinfo.get("service_domain"), "/apt54/")
        request_data = dict(uuid=app.config["SERVICE_UUID"])

        salt = self.get_salt(url, request_data)
        if not salt:
            raise ServiceSaltError(message="Error with getting salt")

        signature = sign_data(app.config["SERVICE_PRIVATE_KEY"], salt)

        request_data.update(dict(step=2, signed_salt=signature))
        response = requests.post(url, json=request_data, headers=get_language_header())
        if response.status_code == 452:
            raise ServiceAPT54Error(
                message="There is no such user with request data - %s. \n "
                "Content - %s" % (request_data, response.content)
            )
        elif not response.ok:
            raise ServiceAPT54Error(
                message="Error with getting apt54. \n Content - %s" % response.content
            )

        content = json.loads(response.content)
        apt54 = json.loads(content.get("apt54"))
        return apt54

    def get_session_token(self):
        """
        Get session token from database.
        """
        session_token = app.db.fetchone(
            """SELECT session_token, apt54 FROM service_session_token WHERE uuid = %s 
        AND service_uuid = %s ORDER BY created DESC""",
            [app.config["SERVICE_UUID"], self.service.uuid],
        )

        if not session_token:
            return None

        apt54 = session_token.get("apt54")
        if apt54_expired(apt54.get("expiration")):
            apt54 = self.update_apt54()
            return self.update_session_token(apt54=apt54)

        return session_token.get("session_token")

    def update_session_token(self, apt54=None):
        """
        Get new session token for your service

        """
        if (
            apt54
            and isinstance(apt54, dict)
            and apt54.get("user_data")
            and isinstance(apt54.get("user_data"), dict)
            and apt54.get("user_data").get("uuid") == app.config["SERVICE_UUID"]
        ):
            pass
        else:
            apt54 = self.get_apt54()

        url = urljoin(self.service.uinfo.get("service_domain"), "/auth/")
        request_data = dict(apt54=apt54)

        salt = self.get_salt(url, request_data)
        if not salt:
            return

        signature = sign_data(app.config["SERVICE_PRIVATE_KEY"], salt)

        data = dict(step=2, signed_salt=signature, apt54=apt54)
        response = requests.post(url, json=data, headers=get_language_header())
        if not response.ok:
            raise ServiceSessionError("Error with getting session")

        content = json.loads(response.content)
        session_token = content.get("session_token")
        if content.get("apt54"):
            try:
                apt54 = json.loads(content.get("apt54"))
            except json.JSONDecodeError:
                pass

        try:
            self.save_session(session_token, apt54)
        except Exception as e:
            print("Your service is not registered on your side.\n Exception - %s" % e)

        return session_token

    def send_request(self, *args, **kwargs):
        if app.config.get("AUTH_STANDALONE"):
            result = self._execute_locally(*args, **kwargs)
        else:
            result = self._send_request(*args, **kwargs)
        return result

    def _execute_locally(self, data, *args, **kwargs):
        return self._local_handlers.get(self.endpoint, self.default_class)(
            data
        ).execute()

    def _send_request(
        self,
        data=None,
        custom_headers: dict = None,
        is_json: bool = True,
        is_signed: bool = True,
        timeout: float = 10,
    ):
        """
        General function for sending request on service. Can be rewrite if you need
        :param data: dict. request data
        :param custom_headers: dict. Custom headers
        :param is_json: bool. Optional. If request not json.
        :param is_signed: bool. Optional. If no need service_uuid in request and data signing.
        Need for service_only decorator.
        :param timeout: integer. Optional. Request timeout.
        :return: response
        @subm_flow
        """
        if not self.endpoint:
            raise ServiceInvalidData

        if not data or not isinstance(data, dict):
            data = dict()

        session_token = self.get_session_token()
        if not session_token:
            session_token = self.update_session_token()

        headers = dict()
        headers["Session-Token"] = session_token
        headers["content-type"] = "application/json"
        if custom_headers and isinstance(custom_headers, dict):
            headers.update(custom_headers)

        if is_signed:
            data.update(dict(service_uuid=app.config["SERVICE_UUID"]))
            data["signature"] = sign_data(
                app.config["SERVICE_PRIVATE_KEY"], json_dumps(data, sort_keys=True)
            )

        url = urljoin(self.service.uinfo.get("service_domain"), self.endpoint)
        try:
            _method = getattr(requests, self.method.lower())
            if is_json:
                response = _method(url, headers=headers, json=data, timeout=timeout)
            else:
                response = _method(url, headers=headers, data=data, timeout=timeout)
        except Exception as e:
            print("Error - %s" % e)
            raise ServiceRequestError

        return response

    def save_session(self, session_token, apt54):
        """
        Save new session in database
        """
        if not isinstance(apt54.get("user_data"), dict):
            raise ServiceSessionError("Error with apt54")

        if apt54["user_data"].get("uuid") != app.config["SERVICE_UUID"]:
            raise ServiceSessionError("Invalid uuid for session")

        query = "SELECT session_token, uuid FROM service_session_token WHERE session_token = %s"
        values = [session_token]
        session_token_exists = app.db.fetchone(query, values)
        if not session_token_exists:
            query = (
                "INSERT INTO service_session_token(session_token, uuid, apt54, service_uuid) "
                "VALUES(%s, %s, %s::jsonb, %s)"
            )
            values = [
                session_token,
                app.config["SERVICE_UUID"],
                json_dumps(apt54),
                self.service.uuid,
            ]

        elif (
            session_token.get("session_token") == session_token
            and session_token.get("uuid") == app.config["SERVICE_UUID"]
        ):
            query = "UPDATE service_session_token SET apt54 = apt54 WHERE session_token= %s AND uuid = %s"
            values = [apt54, session_token, app.config["SERVICE_UUID"]]
        else:
            self.update_session_token(apt54)

        app.db.execute(query, values)
        return

    @staticmethod
    def get_salt(url, request_data: dict):
        """
        Get salt from target service
        """
        data = dict(step=1)
        if not isinstance(request_data, dict):
            return None

        data.update(request_data)
        response = requests.post(url, json=data, headers=get_language_header())

        if not response.ok:
            return None

        response_data = json.loads(response.content)
        return response_data.get("salt", None)


class GetAndUpdateActor(BaseServiceCommunication):
    """
    Get and update locally actor by uuid. Use it if your service working locally and registered on some auth that is
    on some other server.
    """

    def __init__(self, uuid=None):
        service = Actor.objects.get(initial_key=app.config["AUTH_PUB_KEY"])
        super().__init__(service=service)
        self.endpoint = "/service/get_actors/"
        self.uuid = uuid
        self.data = dict()

    def update_actor(self):
        if self.uuid:
            self.data.update(uuid=self.uuid)

        response = self.send_request(data=self.data)
        if not response.ok:
            return None

        actors = json.loads(response.content).get("actors")
        if isinstance(actors, dict):
            query = (
                "INSERT INTO actor SELECT * FROM jsonb_populate_record(null::actor, jsonb %s) ON CONFLICT(uuid) "
                "DO UPDATE SET initial_key=EXCLUDED.initial_key, uinfo=EXCLUDED.uinfo;"
            )
        elif isinstance(actors, list):
            query = (
                "INSERT INTO actor SELECT * FROM jsonb_populate_recordset(null::actor, jsonb %s) ON CONFLICT(uuid) "
                "DO UPDATE SET initial_key=EXCLUDED.initial_key, uinfo=EXCLUDED.uinfo;"
            )
        else:
            return None

        values = [json_dumps(actors)]
        app.db.execute(query, values)
        return actors


class GetAndUpdateGroups(BaseServiceCommunication):
    """
    Get and update locally actor(groups) by uuid. Use it if your service working locally and registered on some auth
    that is on some other server.
    """

    def __init__(self, data=None):
        service = Actor.objects.get(initial_key=app.config["AUTH_PUB_KEY"])
        super().__init__(service=service)
        self.endpoint = "/service/get_groups/"
        self.data = data if data else dict()

    def update_groups(self):
        data = dict(data=self.data)
        response = self.send_request(data=data)
        if not response.ok:
            return None

        actors = json.loads(response.content)
        if not actors:
            return None

        actors = actors.get("groups")
        query = (
            "INSERT INTO actor SELECT * FROM jsonb_populate_recordset(null::actor, jsonb %s) ON CONFLICT (uuid) "
            "DO UPDATE SET uinfo = EXCLUDED.uinfo WHERE actor.uuid = EXCLUDED.uuid"
        )
        values = [json_dumps(actors)]
        app.db.execute(query, values)
        if not self.data:
            # Need to delete groups that not in list. Cause we got all groups
            groups_uuid = [value.get("uuid") for value in actors]
            query = "DELETE FROM actor WHERE actor_type = 'group' AND NOT (uuid = ANY(%s::uuid[]))"
            values = [groups_uuid]
            app.db.execute(query, values)

        return actors


class GetAndUpdatePermissions(BaseServiceCommunication):
    """
    Get and update locally permissions. Use it if your service working locally and registered on some auth that is
    on some other server.
    """

    def __init__(self, data=None):
        service = Actor.objects.get(initial_key=app.config["AUTH_PUB_KEY"])
        super().__init__(service=service)
        self.endpoint = "/service/get_permissions/"
        self.data = data if data else dict()

    def update_permissions(self):
        data = dict(data=self.data)
        response = self.send_request(data=data)
        if not response.ok:
            return None

        content = json.loads(response.content)
        permissions = content.get("permissions")
        if not self.data and permissions:
            # Need to remove old perms, cause they may be deleted on auth
            groups = [value.get("actor_id") for value in permissions]
            query = "DELETE FROM permissions WHERE actor_id = ANY(%s::uuid[])"
            values = [groups]
            app.db.execute(query, values)

        if permissions:
            actors = content.get("actors")
            query = (
                "INSERT INTO actor SELECT * FROM jsonb_populate_recordset(null::actor, jsonb %s) ON "
                "CONFLICT(uuid) DO UPDATE SET secondary_keys = EXCLUDED.secondary_keys, "
                "uinfo= EXCLUDED.uinfo"
            )
            values = [json_dumps(actors)]
            app.db.execute(query, values)

            query = """SELECT * FROM insert_or_update_perms(%s::jsonb)"""
            values = [json_dumps(permissions)]
            app.db.execute(query, values)

        return permissions


class SendCallback(BaseServiceCommunication):
    """
    Send callback request on auth service, that information was updated on your service.
    @subm_flow Send callback request on auth service, that information was updated on your service.
    """

    def __init__(self, action_type, data=None):

        service = Actor.objects.get(initial_key=app.config["AUTH_PUB_KEY"])
        super().__init__(service=service)
        self.action_type = action_type
        self.data = data if data and isinstance(data, dict) else dict()
        self.method = "post"
        self.endpoint = "/service/callback/"

    def send_callback(self):
        """
            Send callback request on auth service, that information was updated on your service.
            @subm_flow Send callback request on auth service, that information was updated on your service.
            """
        self.data["action_type"] = self.action_type
        self.send_request(data=self.data, timeout=5)


class UpdateActorPassword(BaseServiceCommunication):
    """
    Send request on auth service to update password for classic_user
    @subm_flow
    """

    def __init__(self, actor_uuid, new_password):
        service = Actor.objects.get(initial_key=app.config.get("AUTH_PUB_KEY"))
        super().__init__(service=service)
        self.actor_uuid = actor_uuid
        self.new_password = new_password
        self.method = "post"
        self.endpoint = "/update/password"

    def update_password(self):
        if not Actor.objects.exists(uuid=self.actor_uuid):
            response = create_response_message(
                message=_("Error with updating password. There is no such actor."),
                error=True,
            )
            return response

        data = dict(uuid=self.actor_uuid, password=self.new_password)
        response = self.send_request(data=data, is_signed=False, timeout=10)
        return response


class UpdateActor(BaseServiceCommunication):
    """
    Send request on auth service to update actor
    @subm_flow
    """

    def __init__(self, actor_uuid: str, uinfo: dict, actor_type: str = "classic_user"):
        super().__init__()
        self.actor_uuid = actor_uuid
        self.uinfo = uinfo
        self.actor_type = actor_type
        self.method = "post"
        self.endpoint = "/update/actor"

    def update_actor(self):
        """
        Update actor
        @subm_flow
        """
        if not Actor.objects.exists(uuid=self.actor_uuid):
            response = create_response_message(
                message="Error with updating user. There is no such actor.", error=True
            )
            return response

        data = dict(uuid=self.actor_uuid, uinfo=self.uinfo, actor_type=self.actor_type)
        response = self.send_request(data=data, is_signed=False)
        return response


class GetActorByEmail(BaseServiceCommunication):
    def __init__(self, email):
        super().__init__()
        self.email: Dict = {"uinfo": {"email": email}}
        self.method: str = "post"
        self.endpoint: str = "/get/actors"

    def execute(self) -> Dict:
        response: Dict = self.send_request(data=self.email, is_signed=False)
        return response
