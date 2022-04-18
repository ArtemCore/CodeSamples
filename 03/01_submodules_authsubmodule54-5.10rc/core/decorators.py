from functools import wraps

from flask import current_app as app
from flask import jsonify, make_response, redirect, request
from flask import session as flask_session
from flask import url_for
from flask_babel import gettext as _
from werkzeug.exceptions import Forbidden, Unauthorized, UnsupportedMediaType

from .action import BasePermAction
from .actor import Actor, ActorNotFound
from .perms.biom_level_chain import BiomLevelPermactionChain
from .utils import (apt54_expired, get_current_actor, get_session,
                    get_session_token)


def token_required(func):
    """
    This decorator is used for checking if user is logged in (has session token) and verify apt54 is not expired.
    """

    @wraps(func)
    def inner(self, *args, **kwargs):

        session_token = get_session_token()
        if not session_token:
            return redirect(url_for("auth_submodule.authorization"))
            # raise Unauthorized(_('Actor have no session token.'))

        session = get_session(session_token)
        if not session:
            raise Unauthorized(_("Actor have no session."))

        apt54 = session.get("apt54")
        if not apt54:
            with app.db.get_cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM actor WHERE uuid=%s AND actor_type='local'",
                    (session.get("uuid"),),
                )
                user_count = cur.fetchone()
                if user_count.get("count") == 1:
                    return func(self, *args, **kwargs)

        if not session or not apt54:
            raise Unauthorized(_("Actor have no session or APT54."))

        if apt54_expired(apt54.get("expiration")):
            raise Unauthorized(_("APT54 expired"))

        try:
            actor = Actor.objects.get(uuid=session.get("uuid"))
        except ActorNotFound:
            flask_session.pop("session_token")
            raise Unauthorized(_("Actor not found."))

        if actor.is_banned and not actor.is_root:
            if "session_token" in flask_session:
                flask_session.pop("session_token")

            raise Unauthorized(_("Actor is banned."))

        return func(self, *args, **kwargs)

    return inner


def required_data(required: list):
    """
    Auxiliary decorator used to validate required data parameters for application-json content type.
    Returns 422 error response if one or more of passed keys not in request.json.
    Usage: @required_data(['param1', 'param2', 'param3'])
    """

    def decorator(f):
        @wraps(f)
        def inner(*args, **kwargs):
            data = request.json
            keys = data.keys() if data else []
            missing = [r for r in required if r not in keys]
            if missing:
                missing_str = ", ".join(required)
                msg = f"Missing required data: {missing_str}"
                return make_response(jsonify({"message": msg}), 422)
            return f(*args, **kwargs)

        return inner

    return decorator


def set_attributes(*args, **kwargs):
    """
    Set attributes listed in dict to the function. Used for setting attributes to action permissions like
    perm_type and default_value
    """

    def inner(func):

        for attr, value in kwargs.items():
            setattr(func, attr, value)
        return func

    return inner


def perms_check(func):
    """
    This decorator calls main level chain, that calls all level permissions check
    """

    @wraps(func)
    def inner(self, *args, **kwargs):

        actor = get_current_actor(raise_exception=False)
        if not actor:
            raise Unauthorized(_("There is no such actor."))

        permaction_uuid = self.permaction_uuid()
        service_uuid = app.config["SERVICE_UUID"]
        chain = BiomLevelPermactionChain(
            service_uuid=service_uuid,
            user=actor,
            permaction_uuid=permaction_uuid,
            source_class=self,
        )

        if not chain.check():
            raise Forbidden(_("Permissions denied."))

        return func(self, *args, **kwargs)

    return inner


def data_parsing(func):
    """
    This decorator is used for parsing data from json object. Helper for auth communication parsing.
    """

    @wraps(func)
    def inner(self=None, *args, **kwargs):
        if "data" in kwargs:
            data = kwargs.get("data")
        elif args:
            data = args[0]
        elif request.is_json:
            try:
                data = request.json
            except:
                data = dict()
        elif request.method == "POST":
            if request.form:
                data = dict(request.form)
            else:
                raise UnsupportedMediaType(_("Unsupported Media Type."))
        else:
            # TODO: Rebuild on raise, problem with after_request function or stay like that
            data = dict()

        kwargs = dict(data=data)

        return func(self, **kwargs)

    return inner


def admin_only(func):
    """
    This decorator is used for checking if user is logged in (has session token), verify apt54 is not expired and
    actor is ADMIN or ROOT.
    So views that has this decorator could be called only by ADMIN or ROOT
    """

    @wraps(func)
    def inner(self, *args, **kwargs):
        """
        Decorator admin only
        @subm_flow Decorator admin only
        """
        session_token = get_session_token()
        if not session_token:
            return redirect(url_for("auth_submodule.authorization"))
            # raise Unauthorized(_('Actor have no session token.'))

        session = get_session(session_token)
        if not session:
            raise Unauthorized(_("Actor have no session."))

        apt54 = session.get("apt54")

        if not session or not apt54:
            raise Unauthorized(_("Actor have no session or APT54."))

        actor = Actor.objects.get(uuid=apt54["user_data"].get("uuid"))
        if not actor:
            raise Unauthorized(_("There is no such actor."))

        if apt54_expired(apt54.get("expiration")):
            raise Unauthorized(_("APT54 expired."))

        if actor.is_root:
            return func(self, *args, **kwargs)

        if not actor.is_admin or actor.is_banned:
            raise Forbidden(_("Permissions denied."))

        return func(self, *args, **kwargs)

    return inner


def root_only(func):
    """
    This decorator is used for checking if user is logged in (has session token), verify apt54 is not expired and
    actor is ROOT.
    So views that has this decorator could be called only by ROOT
    """

    @wraps(func)
    def inner(self, *args, **kwargs):
        """
        Decorator root only
        @subm_flow Decorator root only
        """
        session_token = get_session_token()
        if not session_token:
            return redirect(url_for("auth_submodule.authorization"))
            # raise Unauthorized(_('Actor have no session token.'))

        session = get_session(session_token)
        if not session:
            raise Unauthorized(_("Actor have no session."))

        apt54 = session.get("apt54")

        if not session or not apt54:
            raise Unauthorized(_("Actor have no session or APT54."))

        actor = Actor.objects.get(uuid=apt54["user_data"].get("uuid"))
        if not actor:
            raise Unauthorized(_("There is no such actor."))

        if apt54_expired(apt54.get("expiration")):
            raise Unauthorized(_("APT54 expired."))

        if not actor.is_root:
            raise Forbidden(_("Permissions denied."))

        return func(self, *args, **kwargs)

    return inner


def service_only(func):
    """
    This decorator is used executing functions only from service. If service sent this request. Service-service request.
    """

    @wraps(func)
    def inner(self, *args, **kwargs):
        """
        Decorator service only
        @subm_flow Decorator service only
        """
        if not request.is_json:

            raise UnsupportedMediaType(_("Unsupported Media Type."))

        data = request.json

        if not data.get("service_uuid"):
            raise Forbidden(_("Permissions denied."))

        if not app.db.fetchone(
            "SELECT EXISTS(SELECT 1 FROM actor WHERE uuid = %s AND actor_type = 'service')",
            [data.get("service_uuid")],
        ).get("exists"):
            raise Forbidden(_("Permissions denied."))
        return func(self, *args, **kwargs)

    return inner


def auth_service_only(func):
    """
    This decorator is used executing functions only if Auth service sent this request
    """

    @wraps(func)
    def inner(self, *args, **kwargs):
        data = request.json if request.is_json else dict(request.form)
        if not data.get("service_uuid"):
            raise Forbidden(_("Permissions denied."))

        if not app.db.fetchone(
            "SELECT EXISTS(SELECT 1 FROM actor WHERE uuid = %s AND actor_type = 'service' AND lower(uinfo->>'service_name') = 'auth')",
            [data.get("service_uuid")],
        ).get("exists"):
            raise Forbidden(_("Permissions denied."))

        return func(self, *args, **kwargs)

    return inner


def standalone_only(func):
    """
    This decorator is used for checking if standalone_mode is true
    So views that has this decorator could be called only on standalone_mode
    """

    @wraps(func)
    def inner(self, *args, **kwargs):
        """
        Decorator standalone only
        @subm_flow Decorator standalone only
        """
        if app.config.get("AUTH_STANDALONE") is False:
            raise Forbidden(
                _("Admin panel isn't available out of the standalone mode.")
            )
        return func(self, *args, **kwargs)

    return inner
