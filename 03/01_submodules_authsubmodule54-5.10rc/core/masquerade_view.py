from flask import request
from flask import jsonify
from flask import make_response
from flask import current_app as app
from flask.views import MethodView
from flask_cors import cross_origin

from .actions.masquerade_actions import MasqueradePermAction


class MasqueradeOn(MethodView):
    """
    @POST Use site as client@
    """
    @cross_origin()
    def post(self):
        data = request.json
        masquerade_uuid = data.get('actor_uuid')

        primary_session, masquerade_session = MasqueradePermAction(masquerade_uuid).execute()

        return make_response(jsonify(dict(
            primary_session=primary_session,
            masquerade_session=masquerade_session,
        )), 200)


