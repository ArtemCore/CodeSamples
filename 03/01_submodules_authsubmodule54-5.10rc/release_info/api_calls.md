# API calls:

| Method | Endpoint | Description | View |
| ------ | ------ | ------ | ------ |
| ![#0000ff](https://via.placeholder.com/15/0000ff/000000?text=+) **GET** | /about/ | Get page with json information about service | AboutView |
| ![#ff0000](https://via.placeholder.com/15/ff0000/000000?text=+) **DELETE** | /actor/ | Delete actor based on request body, only for auth service | ActorView |
| ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | /actor/ | Create actor based on request body, only for auth service | ActorView |
| ![#FFA500](https://via.placeholder.com/15/FFA500/000000?text=+) **PUT** | /actor/ | Update actor partially based on request body, only for auth service | ActorView |
| ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | /apt54/ | Authentication with getting apt54 | APT54View |
| ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | /auth/ |  | ClientAuthViewService |
| ![#0000ff](https://via.placeholder.com/15/0000ff/000000?text=+) **GET** | /auth_admin/ | Redirect to page with profile info | AdminView |
| ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | /auth_admin/ | Logout and redirect to home page | AdminView |
| ![#0000ff](https://via.placeholder.com/15/0000ff/000000?text=+) **GET** | /auth_admin/actor/{uuid}/ | Get page with actor detail based on uuid | AdminActorView |
| ![#FFA500](https://via.placeholder.com/15/FFA500/000000?text=+) **PUT** | /auth_admin/actor/{uuid}/ | Update an actor partially based on uuid and request body | AdminActorView |
| ![#ff0000](https://via.placeholder.com/15/ff0000/000000?text=+) **DELETE** | /auth_admin/actors/ | Delete actor based on request body | AdminActorsView |
| ![#0000ff](https://via.placeholder.com/15/0000ff/000000?text=+) **GET** | /auth_admin/actors/ | Get page with list of actors | AdminActorsView |
| ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | /auth_admin/actors/ | Create a new actor based on request body | AdminActorsView |
| ![#ff0000](https://via.placeholder.com/15/ff0000/000000?text=+) **DELETE** | /auth_admin/permissions/ | Delete permissions to actor based on request body | AdminPermissionView |
| ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | /auth_admin/permissions/ | Set permissions to actor based on request body | AdminPermissionView |
| ![#FFA500](https://via.placeholder.com/15/FFA500/000000?text=+) **PUT** | /auth_admin/permissions/ | Update permissions to actor based on request body | AdminPermissionView |
| ![#0000ff](https://via.placeholder.com/15/0000ff/000000?text=+) **GET** | /auth_admin/profile/ | Get page with self admin profile info | AdminProfileView |
| ![#FFA500](https://via.placeholder.com/15/FFA500/000000?text=+) **PUT** | /auth_admin/profile/ | Update self admin profile partially based on request body | AdminProfileView |
| ![#0000ff](https://via.placeholder.com/15/0000ff/000000?text=+) **GET** | /auth_authorization/ | Allow to authenticate with Auth session | AuthSSOView |
| ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | /auth_authorization/ | Session generation: generate tamporary session and accepts session from 
| ![#0000ff](https://via.placeholder.com/15/0000ff/000000?text=+) **GET** | /authorization/ |  | AuthorizationView |
| ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | /choose/phantom |  | SetChosenPhantomActorView |
| ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | /create/phantom |  | CreatePhantomRelationView |
| ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | /delete/phantom |  | DeletePhantomRelationView |
| ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | /get/phantom |  | GetPhantomActorView |
| ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | /get_invite_link_info/ |  | GetInviteLinkInfoView |
| ![#0000ff](https://via.placeholder.com/15/0000ff/000000?text=+) **GET** | /get_qr_code/ | QR code generation | QRCodeView |
| ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | /get_session/ | Get session based on request body | GetSession |
| ![#ff0000](https://via.placeholder.com/15/ff0000/000000?text=+) **DELETE** | /perms/ | Delete permissions from database that was sent from auth based on request body | PermissionView |
| ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | /perms/ | Create permissions in database that was sent from auth based on request body | PermissionView |
| ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | /reg/ | Registration user with auth service based on request body | RegistrationView |
| ![#00FF00](https://via.placeholder.com/15/00FF00/000000?text=+) **POST** | /save_session/ | Save session in cookies with flask session module based on request body | SaveSession |
