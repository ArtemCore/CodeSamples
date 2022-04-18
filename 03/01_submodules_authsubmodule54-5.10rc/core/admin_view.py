from flask import g
from flask import jsonify
from flask import make_response
from flask import current_app as app
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import session
from flask.views import MethodView
from flask_cors import cross_origin

from werkzeug.exceptions import NotFound
from psycopg2 import errors

from .actor import Actor
from .actor import ActorNotFound
from .utils import get_current_actor
from .utils import create_response_message
from .decorators import admin_only
from .decorators import standalone_only
from .decorators import token_required
from .actions.actor_actions import CreateActorAction
from .actions.actor_actions import DeleteActorAction
from .actions.standalone_actions import UpdateProfileAction
from .actions.standalone_actions import UpdateActorAction
from .actions.permactions_actions import GetAllPermsAction
from .actions.permactions_actions import SetPermactionAction
from .actions.permactions_actions import DeletePermactionAction
from .actions.permactions_actions import UpdatePermactionAction


class AdminView(MethodView):
    """
    @GET Redirect to page with profile info@
    @POST Logout and redirect to home page@
    """

    @standalone_only
    @token_required
    @cross_origin()
    def get(self):
        """
        Redirect to page with profile info
        @subm_flow
        """
        return redirect(url_for('auth_submodule.admin_profile'))

    @standalone_only
    @token_required
    @cross_origin()
    def post(self):
        """
                Logout and redirect to home page
                @subm_flow
                """
        session.pop('session_token', None)
        response = make_response(redirect('/'))
        response.delete_cookie(app.config.get('SERVICE_NAME').capitalize())
        return response


class AdminActorsView(MethodView):
    """
    @GET Get page with list of actors@
    @POST Create a new actor based on request body@
    @DELETE Delete actor based on request body@
    """

    @standalone_only
    @admin_only
    @cross_origin()
    def get(self):
        """
        Get page with list of actors
        @subm_flow  Get page with list of actors
        """
        actors = Actor.objects.filter()
        groups = Actor.objects.filter(actor_type='group')
        return render_template('admin_panel/actors.html', actors=actors, groups=groups)

    @standalone_only
    @admin_only
    @cross_origin()
    def post(self):
        """
               Create a new actor based on request body
               @subm_flow Create a new actor based on request body
               """
        if not request.is_json or not request.json.get('uinfo') or not request.json.get('actor_type'):
            response = create_response_message(message='Invalid request type', error=True)
            return make_response(jsonify(response), 400)
        actor = request.json
        response, status = CreateActorAction(actor).execute()
        return make_response(jsonify(response), status)

    @standalone_only
    @admin_only
    @cross_origin()
    def delete(self):
        """
        Delete actor based on request body
        @subm_flow  Delete actor based on request body
        """
        if not request.is_json or not request.json.get('uuid'):
            response = create_response_message(message='Invalid request type', error=True)
            return make_response(jsonify(response), 400)
        data = request.json
        actor = Actor.objects.get(uuid=data.get('uuid'))
        response, status = DeleteActorAction(actor.__dict__).execute()
        return make_response(jsonify(response), status)


class AdminActorView(MethodView):
    """
    @GET Get page with actor detail based on uuid@
    @PUT Update an actor partially based on uuid and request body@
    """

    @standalone_only
    @admin_only
    @cross_origin()
    def get(self, uuid):
        """
        Get page with actor detail based on uuid
        @subm_flow
        """
        #TODO try catch for requests
        try:
            actor = Actor.objects.get(uuid=uuid)
        except ActorNotFound:
            raise NotFound('No actor with such UUID found')
        except errors.InvalidTextRepresentation:
            raise NotFound('Invalid UUID representation')

        uinfo = actor.uinfo
        if actor.actor_type in ['user', 'classic_user']:
            if actor.actor_type == 'classic_user':
                uinfo.pop('password')

        # perms = actor.get_permissions()
        perms = GetAllPermsAction(actor.uuid).execute()
        actor_groups = {group.uuid: group for group in actor.get_groups()}
        groups = Actor.objects.filter(actor_type='group')
        actors = Actor.objects.filter()
        return render_template('admin_panel/actor.html', actor=actor, perms=perms,
                               actor_groups=actor_groups, groups=groups, actors=actors)

    @standalone_only
    @admin_only
    @cross_origin()
    def put(self, uuid):
        """
        Update an actor partially based on uuid and request body
        @subm_flow
        """
        data = request.json
        response, status_code = UpdateActorAction(data, uuid).execute()
        return make_response(jsonify(response), status_code)


class AdminProfileView(MethodView):
    """
    @GET Get page with self admin profile info@
    @PUT Update self admin profile partially based on request body@
    """
    @standalone_only
    @token_required
    @cross_origin()
    def get(self):
        """
        Get page with self admin profile info
        @subm_flow
        """
        actor = get_current_actor()
        actor_groups = {group.uuid: group for group in actor.get_groups()}
        if not hasattr(g, 'actor'):
            setattr(g, 'actor', actor)
        perms = GetAllPermsAction(actor.uuid).execute()
        return render_template('admin_panel/profile.html', perms=perms, actor_groups=actor_groups)

    @standalone_only
    @token_required
    @cross_origin()
    def put(self):
        """
        Update self admin profile partially based on request body
        @subm_flow
        """
        data = request.json
        print(data)
        response, status_code = UpdateProfileAction(data).execute()
        return make_response(jsonify(response), status_code)


class AdminPermissionView(MethodView):
    """
    @POST Create permission @
    @PUT Update permission@
    @DELETE Delete permission@
    """

    @standalone_only
    @admin_only
    @cross_origin()
    def post(self):
        """
        Create permission
        @subm_flow
        """
        data = request.json
        response, status_code = SetPermactionAction(data).execute()
        return make_response(jsonify(response), status_code)

    @standalone_only
    @admin_only
    @cross_origin()
    def put(self):
        """
                Update permission
                @subm_flow
                """
        data = request.json
        response, status_code = UpdatePermactionAction(data).execute()
        return make_response(jsonify(response), status_code)

    @standalone_only
    @admin_only
    @cross_origin()
    def delete(self):
        """
                     Delete permission
                     @subm_flow
                     """
        data = request.json
        response, status_code = DeletePermactionAction(data).execute()
        return make_response(jsonify(response), status_code)
