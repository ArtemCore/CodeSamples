from . import auth_submodule
from .actor_view import ActorView
from .actor_view import GetActorsViewByEmail

from .auth_view import AboutView
from .auth_view import APT54View
from .auth_view import RegistrationView
from .auth_view import ClientAuthView
from .auth_view import GetQRCodeView
from .auth_view import SaveSession
from .auth_view import GetSession
from .auth_view import AuthorizationView
from .auth_view import AuthQRCodeAuthorizationView
from .auth_view import AuthSSOGenerationView
from .auth_view import AuthSSOAuthorizationView
from .admin_view import AdminView
from .admin_view import AdminActorView
from .admin_view import AdminActorsView
from .admin_view import AdminPermissionView
from .admin_view import AdminProfileView
from .invite_link_view import GetInviteLinkInfoView
from .permission_view import PermissionView
from .masquerade_view import MasqueradeOn
from .permaction_view import ActorPermactionView
from .permaction_view import GroupPermactionView
from .synchronization_view import GetSynchronizationHash
from .synchronization_view import ProcessForcedSynchroniationDataView



# Registration/authentication endpoints
auth_submodule.add_url_rule('/apt54/', view_func=APT54View.as_view('apt54'))  # Get APT54
auth_submodule.add_url_rule('/auth/', view_func=ClientAuthView.as_view('auth'))  # Authentication
auth_submodule.add_url_rule('/authorization/', view_func=AuthorizationView.as_view('authorization'))  # Get template
auth_submodule.add_url_rule('/reg/', view_func=RegistrationView.as_view('reg'))  # Registration
auth_submodule.add_url_rule('/save_session/', view_func=SaveSession.as_view('save_session'))  # Save session in cookie
auth_submodule.add_url_rule('/get_session/', view_func=GetSession.as_view('get_session'))  # Get session with temporary session
auth_submodule.add_url_rule('/auth_sso_generation/', view_func=AuthSSOGenerationView.as_view('auth-sso'))  # Auth Single Sign-On generation
auth_submodule.add_url_rule('/auth_sso_login/', view_func=AuthSSOAuthorizationView.as_view('auth_sso_login'))  # Login after redirect from Auth service
auth_submodule.add_url_rule('/auth_qr_code/', view_func=AuthQRCodeAuthorizationView.as_view('auth_qr_login'))  # Login after qr scanning

# Auth API endpoints
auth_submodule.add_url_rule('/actor/', view_func=ActorView.as_view('actor'))  # CRUD actor from auth
auth_submodule.add_url_rule('/perms/', view_func=PermissionView.as_view('permissions'))  # CRUD permissions from auth
auth_submodule.add_url_rule('/permaction/actor/',view_func=ActorPermactionView.as_view("actor_permaction")) # CRUD actor_permaction from auth
auth_submodule.add_url_rule('/permaction/group/',view_func=GroupPermactionView.as_view("group_permaction")) # CRUD group_permaction from auth
auth_submodule.add_url_rule('/synchronization/get_hash/',view_func=GetSynchronizationHash.as_view("get_synchronization_hash"))
auth_submodule.add_url_rule('/synchronization/force/',view_func=ProcessForcedSynchroniationDataView.as_view("process_force_synchronization_data"))


# Utility endpoints
auth_submodule.add_url_rule('/about/', view_func=AboutView.as_view('about'))  # Service/biom info
auth_submodule.add_url_rule('/get_qr_code/', view_func=GetQRCodeView.as_view('qr-code'))  # QR code generation

# Temporary endpoints
auth_submodule.add_url_rule('/get_invite_link_info/', view_func=GetInviteLinkInfoView.as_view('get_invite_link_info'))

# Admin panel in auth standalone
auth_submodule.add_url_rule('/auth_admin/', view_func=AdminView.as_view('admin'))
auth_submodule.add_url_rule('/auth_admin/profile/', view_func=AdminProfileView.as_view('admin_profile'))
auth_submodule.add_url_rule('/auth_admin/actors/', view_func=AdminActorsView.as_view('admin_actors'))
auth_submodule.add_url_rule('/auth_admin/actor/<uuid>/', view_func=AdminActorView.as_view('admin_actor'))
auth_submodule.add_url_rule('/auth_admin/permissions/', view_func=AdminPermissionView.as_view('admin_permissions'))

# Actors endpoints
auth_submodule.add_url_rule('/actors/get', view_func=GetActorsViewByEmail.as_view("get_submodule_actors"))

# Masquerade endpoint
auth_submodule.add_url_rule('/masquerade/on/', view_func=MasqueradeOn.as_view('masquerade_on'))
