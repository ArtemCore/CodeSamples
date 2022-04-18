"""
Actor views for receiving information/changes from auth service and apply it on your service. All of methods are
could be used only if auth service sent this information.
"""
from flask import current_app as app
from flask import jsonify, make_response, request
from flask.views import MethodView
from flask_babel import gettext as _
from flask_cors import cross_origin

from .actions.actor_actions import (CreateActorAction, DeleteActorAction,
                                    UpdateActorAction)
from .decorators import data_parsing, service_only
from .ecdsa_lib import verify_signature
from .service_view import GetActorByEmail, SendCallback
from .utils import create_response_message, json_dumps


class BaseActorView:
    @staticmethod
    def verify_request_data():
        data = request.json
        signature = data.pop("signature")
        if not data or not signature:
            response = create_response_message(
                message=_("Invalid request data."), error=True
            )
            return response, True

        if not verify_signature(
            app.config["AUTH_PUB_KEY"], signature, json_dumps(data, sort_keys=True)
        ):
            response = create_response_message(
                message=_("Signature verification failed."), error=True
            )
            return response, True

        return data, False


class ActorView(MethodView, BaseActorView):
    """
    @POST Submodule Biom mode. Create actor based on request body, only for auth service@
    @PUT Submodule Biom mode. Update actor partially based on request body, only for auth service@
    @DELETE Delete actor based on request body, only for auth service@
    """

    @service_only
    @cross_origin()
    def post(self):
        """
        Create actor. Only for auth service.
        @subm_flow Create actor. Only for auth service.
        """
        data, error = self.verify_request_data()
        actor = data.get("actor")
        if not error:
            response, status_code = CreateActorAction(actor).execute()
            SendCallback(
                action_type="create_actor", data=self.get_callback_data(data)
            ).send_callback()
        else:
            response = data
            status_code = 400
        return make_response(jsonify(response), status_code)

    @service_only
    @cross_origin()
    def put(self):
        """
        Update actor. Only for auth service.
        @subm_flow   Update actor. Only for auth service.
        """
        data, error = self.verify_request_data()
        if not error:
            response, status_code = UpdateActorAction(data=data).execute()

            SendCallback(
                action_type="update_actor", data=self.get_callback_data(data)
            ).send_callback()
        else:
            response = data
            status_code = 400
        return make_response(jsonify(response), status_code)

    @service_only
    @cross_origin()
    def delete(self):
        """
        Delete actor. Only for auth service
        @subm_flow Delete actor. Only for auth service
        """
        data, error = self.verify_request_data()
        if not error:
            response, status_code = DeleteActorAction(data=data).execute()
            SendCallback(
                action_type="delete_actor", data=self.get_callback_data(data)
            ).send_callback()
        else:
            response = data
            status_code = 400
        return make_response(jsonify(response), status_code)

    def get_callback_data(self, data):
        return {
            "sync_package_id": data.get("sync_package_id"),
            "object_uuid": data.get("object_uuid"),
        }


class GetActorsViewByEmail(MethodView):
    """
    @POST Submodule Biom mode. Get actor by email@
    """

    @cross_origin()
    @data_parsing
    def post(self, data):
        """
        POST get actor by email
        @subm_flow POST get actor by email

        """
        data = GetActorByEmail(data.get("email")).execute()
        result = {"error": True, "message": _("Such actor does not exist")}
        status_code = 400
        if data.json().get("actors"):
            action = CreateActorAction(data=data.json().get("actors")[0])
            result = action.actor
            message, status_code = action.execute()
            if status_code != 200:
                result = message
        return make_response(jsonify(result), status_code)
