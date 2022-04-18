from flask import jsonify, request
from flask.views import MethodView
from typing import List

from flask_cors import cross_origin
from .decorators import data_parsing, service_only
from .utils import insert_or_update_group_permaction
from .utils import insert_or_update_actor_permaction
from .ecdsa_lib import verify_signature
from flask import current_app as app
from .utils import json_dumps
from flask_babel import gettext as _
from flask import make_response
from .service_view import SendCallback


def get_callback_data(data):
    return {
        'sync_package_id': data.get('sync_package_id'),
        'object_uuid': data.get('permactions')[0].get('actor_uuid')
    }


class ActorPermactionView(MethodView):
    """
    @POST Update permactions for user @
    @DELETE Delete permactions for user@
    """
    @service_only
    @cross_origin()
    @data_parsing
    def post(self, data, **kwargs):
        """
        Update permactions for user
        @subm_flow Update permactions for user
        """

        response = dict(
            message=_("Permactions update failed.")
        )
        status_code = 400
        if data and verify_signature(
            app.config['AUTH_PUB_KEY'],
            data.pop("signature"),
            json_dumps(data, sort_keys=True)
        ):
            insert_or_update_actor_permaction(data.get("permactions"))
            status_code = 200
            response["message"] = ("Permactions successfully updated.")
            SendCallback(action_type='create_actor_permaction', data=get_callback_data(data)).send_callback()
        return make_response(jsonify(response), status_code)

    @service_only
    @cross_origin()
    @data_parsing
    def delete(self, data, **kwargs):
        """
        Delete permactions for user
        @subm_flow Delete permactions for user
        """
        response = dict(
            message=_("Permactions update failed.")
        )
        status_code = 400
        if data and verify_signature(
            app.config['AUTH_PUB_KEY'],
            data.pop("signature"),
            json_dumps(data, sort_keys=True)
        ):
            order = ["permaction_uuid", "actor_uuid", "service_uuid"]
            query, values = self.delete_permactions(
                order=order, permactions=data.get("permactions")
            )
            app.db.execute(query, tuple(values))
            status_code = 200
            response["message"] = ("Permactions successfully updated.")
            SendCallback(action_type='delete_actor_permaction', data=get_callback_data(data)).send_callback()
        return make_response(jsonify(response), status_code)

    @staticmethod
    def delete_permactions(order, permactions):
        parts: List[str] = list()
        values: List = list()
        query = "DELETE FROM actor_permaction WHERE "
        for permaction in permactions:
            parts.append(f"({' AND '.join([f'{key}=%s' for key in order])})")
            values.extend([permaction.get(key) for key in order])
        query += " OR ".join(parts) + ";"
        return query, values

class GroupPermactionView(MethodView):
    """
    @POST Update permactions for group @
    @DELETE Delete permactions for group@
    """
    @service_only
    @cross_origin()
    @data_parsing
    def post(self, data, **kwargs):
        """
        Update permactions for group
        @subm_flow Update permactions for group
        """
        response = dict(
            message=_("Permactions update failed.")
        )
        status_code = 400

        if data and verify_signature(
            app.config['AUTH_PUB_KEY'],
            data.pop("signature"),
            json_dumps(data, sort_keys=True)
        ):
            insert_or_update_group_permaction(data.get("permactions"))
            status_code = 200
            response["message"] = ("Permactions successfully updated.")
            SendCallback(action_type='create_group_permaction', data=get_callback_data(data)).send_callback()
        return make_response(jsonify(response), status_code)

    @service_only
    @cross_origin()
    @data_parsing
    def delete(self, data, **kwargs):
        """
        Delete permactions for group
        @subm_flow Delete permactions for group
        """
        response = dict(
            message=_("Permactions update failed.")
        )
        status_code = 400
        if data and verify_signature(
            app.config['AUTH_PUB_KEY'],
            data.pop("signature"),
            json_dumps(data, sort_keys=True)
        ):
            order = ["permaction_uuid", "actor_uuid", "service_uuid"]
            query, values = self.delete_permactions(
                order=order, permactions=data.get("permactions")
            )
            app.db.execute(query, tuple(values))
            status_code = 200
            response["message"] = ("Permactions successfully updated.")
            SendCallback(action_type='delete_group_permaction', data=get_callback_data(data)).send_callback()
        return make_response(jsonify(response), status_code)

    @staticmethod
    def delete_permactions(order, permactions):
        parts: List[str] = list()
        values: List = list()
        query = "DELETE FROM group_permaction WHERE "
        for permaction in permactions:
            parts.append(f"({' AND '.join([f'{key}=%s' for key in order])})")
            values.extend([permaction.get(key) for key in order])
        query += " OR ".join(parts) + ";"
        return query, values

