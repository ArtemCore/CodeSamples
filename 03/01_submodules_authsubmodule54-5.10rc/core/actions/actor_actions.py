from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Dict, List
from uuid import UUID
from uuid import uuid4
from psycopg2 import sql
from psycopg2 import errors
from flask_babel import gettext as _
from flask import current_app as app
from werkzeug.exceptions import Forbidden

from ..actor import ActorNotFound
from ..utils import hash_md5
from ..utils import json_dumps
from ..utils import is_valid_uuid
from ..utils import validate_email
from ..utils import get_current_actor
from ..utils import create_response_message
from ..actor import Actor
from ..auth_view import RegistrationView
from ..exceptions import Auth54ValidationError


class ActorAction(ABC):

	def __init__(self, data):
		self.response: str
		self.status_code: int = 200
		self.message: str = str()
		self.query: str = str
		self.appends_list: List = list()
		self.values: Dict = dict()
		self.handlers: List[Callable] = list()
		self.initialize(data)

	@abstractmethod
	def initialize(self, data):
		...

	def execute(self):
		"""
		Actor Actions
		@subm_flow
		"""
		self.handle_input()
		self.apply_handlers()
		self.handle_value()
		self.create_response()
		return self.response, self.status_code

	def handle_input(self):
		if not app.config.get('AUTH_STANDALONE'):
			self.handle_with_auth()
		elif self.actor_type == 'classic_user':
			self.handle_classic_user()
		elif self.actor_type == 'group':
			self.handle_group()
		else:
			self.status_code = 400
			self.message = f"Invalid actor type {self.actor_type}."

	def apply_handlers(self):
		for handler in self.handlers:
			handler()
			if self.status_code != 200:
				break

	def handle_value(self):
		if self.status_code == 200:
			self.execute_query()

	def create_response(self):
		if self.status_code == 200:
			self.response = dict(
				message=_(self.message)
			)
		else:
			self.response = \
				create_response_message(message=_(self.message), error=True)

	def execute_query(self):
		try:
			query = sql.SQL(self.query).format(*self.appends_list)
			app.db.execute(query, self.values)
		except errors.UniqueViolation:
			self.status_code = 400
			self.message = "Such actor already exists locally"

	@abstractmethod
	def handle_with_auth(self):
		...

	@abstractmethod
	def handle_classic_user(self):
		...

	@abstractmethod
	def handle_group(self):
		...


class CreateActorAction(ActorAction):
	"""
	CreateActorAction
	@subm_flow CreateActorAction
	"""

	def initialize(self, data):
		self.message = "Actor was successfully created."
		self.actor = data
		self.actor_type = self.actor.get('actor_type')
		self.uinfo = self.actor.get('uinfo')
		self.actor['uuid'] = self.actor.get("uuid") \
			if self.actor.get("uuid") else uuid4()

	def handle_with_auth(self):
		self.handlers += [
			self.create_query,
		]

	def handle_classic_user(self):
		self.handlers += [
			self.handle_classic_user_data,
			self.handle_email,
			self.handle_unique_email,
			self.handle_users_groups,
			self.handle_password,
			self.create_query,
		]

	def handle_group(self):
		self.handlers += [
			self.handle_gruop_data,
			self.handle_primary_group_info,
			self.handle_unique_group_name,
			self.handle_group_users,
			self.create_query,
		]

	def create_query(self):
		self.query = """INSERT INTO actor
			(SELECT * FROM jsonb_populate_record(null::actor, jsonb {}))
			RETURNING uuid"""
		self.appends_list = [sql.Placeholder("actor")]
		self.values.update({
			"actor":json_dumps(self.actor)
		})

	def handle_classic_user_data(self):
		if not self.uinfo.get('email') or not self.uinfo.get('password'):
			self.message = "Invalid request data."
			self.status_code = 400

	def handle_email(self):
		try:
			validate_email(self.uinfo.get('email'))
		except Auth54ValidationError as e:
			self.message="Email you have inputted is invalid. Please check it."
			self.status_code = 400

	def handle_unique_email(self):
		if app.db.fetchone("""SELECT EXISTS(
				SELECT 1 FROM actor
				WHERE uinfo ->> 'email' = %s)""",
				[self.uinfo.get('email')]).get('exists'):
			self.message = "Actor with such email already exists."
			self.status_code = 400

	def handle_users_groups(self):
		if not self.uinfo.get('groups'):
			self.uinfo = RegistrationView.add_default_group(self.actor)
		else:
			try:
				[UUID(group) for group in self.uinfo.get('groups')]
			except ValueError:
				self.message=f"Invalid group uuid."
				self.status_code = 400

	def handle_password(self):
		self.uinfo['password'] = \
			hash_md5(self.uinfo.get('password'))

	def handle_gruop_data(self):
		if not self.uinfo.get('group_name') or not self.uinfo.get('weight'):
			self.message = "Invalid request data."
			self.status_code = 400

	def handle_primary_group_info(self):
		self.uinfo['group_name'] = self.uinfo.get('group_name').upper()
		self.uinfo['weight'] = int(self.uinfo.get('weight'))

	def handle_unique_group_name(self):
		if app.db.fetchone("""SELECT EXISTS(SELECT 1
				FROM actor WHERE uinfo ->> 'group_name' = %s)""",
				[self.uinfo.get('group_name')]).get('exists'):
			self.message = "Group with such name already exists."
			self.status_code = 400

	def handle_group_users(self):
		if self.uinfo.get('users'):
			query = """UPDATE actor SET
				uinfo = jsonb_set(uinfo, '{groups}', uinfo->'groups' || %s)
				WHERE actor_type IN ('user', 'classic_user')
				AND NOT uinfo->'groups' @> %s
				AND uuid IN %s;"""
			app.db.execute(
				query,
				[
					json_dumps([self.actor.get('uuid')]),
					json_dumps([self.actor.get('uuid')]),
					tuple(self.uinfo.pop('users'))
				]
			)


class UpdateActorAction(ActorAction):
	"""
	UpdateActorAction
	@subm_flow UpdateActorAction
	"""
	def initialize(self, data):
		self.message = "Actor was successfully updated."
		self.actors: list = data.get("actors")
		self.uuid: str = data.get("uuid", None)
		self.uinfo: dict = data.get('uinfo', None)
		self.actor_type: str = data.get('actor_type', None)
		self.users = data.get('users', [])
		self.query: str = str()
		self.appends_list: list = list()
		self.values: dict = dict()
		if not self.actors:
			self.prepare_values()

	def prepare_values(self):
		if not isinstance(self.users, list):
			self.users = [self.users]

		if not Actor.objects.exists(uuid=self.uuid):
			raise Forbidden

		if not self.actor_type:
			self.actor_type = app.db.fetchone(
				"SELECT actor_type FROM actor WHERE uuid = %s",
				(self.uuid,)
			).get('actor_type')

	def handle_with_auth(self):
		self.handlers += [
			self.create_query_with_auth,
			self.create_appends_list_with_auth,
			self.create_values_with_auth
		]

	def handle_classic_user(self):
		self.handlers += [
			self.handle_unique_user_email,
			self.handle_user_password,
			self.create_classic_user_query,
			self.create_classic_user_appends_list,
			self.create_classic_user_values
		]

	def handle_group(self):
		self.handlers += [
			self.handle_group_weight_type,
			self.handle_gruop_weight_value,
			self.handle_unique_weight,
			self.handle_unique_group_name,
			self.create_group_query,
			self.create_group_appends_list,
			self.create_group_values
		]

	def handle_group_weight_type(self):
		try:
			self.uinfo['weight'] = int(self.uinfo.get('weight'))
		except ValueError:
			self.message="Group weight must be an integer value"
			self.status_code = 400

	def handle_gruop_weight_value(self):
		if self.uinfo.get('weight') < 0:
			self.message="Group weight must be a positive value"
			self.status_code = 400

	def handle_unique_weight(self):
		actor_count = app.db.fetchone(
			"""SELECT COUNT(*) FROM actor WHERE actor_type = 'group'
				AND uinfo->>'weight' = %s AND uuid != %s""",
			(self.uinfo.get('weight'), self.uuid)
			).get('count')

		if actor_count != 0:
			self.message="Group with such weight already exists"
			self.status_code = 400

	def handle_unique_group_name(self):
		if self.uinfo.get('group_name'):
			actor_count = app.db.fetchone(
				"""SELECT COUNT(*) FROM actor WHERE actor_type = 'group' "
					"AND uinfo->>'group_name' = %s AND uuid != %s""",
				(self.uinfo.get('group_name'), self.uuid)
			).get('count')

			if actor_count != 0:
				self.message="Group with such name already exists"
				self.status_code = 400

	def handle_unique_user_email(self):
		if self.uinfo.get('email'):
			actor_count = app.db.fetchone(
				"""SELECT COUNT(*) FROM actor
					WHERE actor_type = ANY(ARRAY['classic_user', 'user'])
					AND uinfo->>'email' = %s AND uuid != %s""",
				(self.uinfo.get('email'), self.uuid)
			).get('count')

			if actor_count != 0:
				self.message="User with such email already exists"
				self.status_code = 400

	def handle_user_password(self):
		actor = Actor.objects.get(uuid=self.uuid)
		if actor.uinfo.get('password') != self.uinfo.get('password'):
			self.uinfo['password'] = hash_md5(self.uinfo.get('password'))

	def create_group_query(self):
		self.uqery += """WITH users AS (SELECT A.uuid,
			CASE WHEN A.uinfo->>'groups' IS NULL THEN A.uinfo || to_jsonb({}::jsonb)
				WHEN A.uinfo->'groups' ? {} THEN
					jsonb_set(A.uinfo, {}, ((A.uinfo->'groups')::jsonb - {}::text)) ELSE
					jsonb_set(A.uinfo, {}, ((A.uinfo->'groups')::jsonb || to_jsonb({}::text))) END AS uinfo
				FROM unnest({}::uuid[]) AS RA, actor AS A WHERE RA.uuid=A.uuid)
			UPDATE actor AS A SET uinfo = U.uinfo FROM users AS U WHERE A.uuid=U.uuid;"""

	def create_group_appends_list(self):
		self.appends_list += [
			sql.Placeholder('null_groups'), sql.Placeholder('group_uuid'),
			sql.Placeholder('group_jsonb_key'), sql.Placeholder('group_uuid'),
			sql.Placeholder('group_jsonb_key'), sql.Placeholder('group_uuid'),
			sql.Placeholder('user_uuids')
		]

	def create_group_values(self):
		self.values.update({
			"null_groups": json_dumps({"groups": [self.uuid]}),
			"group_uuid": str(self.uuid),
			"group_jsonb_key": '{groups}',
			"user_uuids": self.users
		})

	def update_permactions_weight(self):
		app.db.execute(
			"""UPDATE group_permaction
				SET weight=%s
				WHERE actor_uuid = %s;
			""", (self.uinfo.get("weight"), self.uuid)
		)

	def create_query_with_auth(self):
		self.query += "SELECT update_or_insert_actor_if_group_exists({})"

	def create_appends_list_with_auth(self):
		self.appends_list += [sql.Placeholder("actors")]

	def create_values_with_auth(self):
		self.values.update({
			"actors": json_dumps(self.actors),
		})

	def create_classic_user_query(self):
		self.query += "UPDATE actor SET uinfo = {}::jsonb WHERE uuid = {};"

	def create_classic_user_appends_list(self):
		self.appends_list += [
			sql.Placeholder('uinfo'),
			sql.Placeholder('uuid')
		]

	def create_classic_user_values(self):
		self.values.update({
			"uinfo": json_dumps(self.uinfo),
			"uuid": self.uuid,
		})


class DeleteActorAction(ActorAction):

	def initialize(self, data):
		self.message = "Actor was successfully deleted."
		self.query: str = str()
		self.appends_list: list = list()
		self.values: dict = dict()
		self.actor: dict = data.get("actor") if data.get("actor") else data
		self.current_actor: Actor
		self.uuid_list: list = self.actor.get("uuid_list", None)
		self.uuid: str = self.actor.get('uuid', None)
		self.uinfo: dict = self.actor.get('uinfo', None)
		self.actor_type: str = self.actor.get('actor_type', "classic_user")

	def handle_with_auth(self):
		self.handlers += [
			self.get_auth_users,
			self.handle_users_uinfo,
			self.create_query,
			self.create_appends_list,
			self.create_values
		]

	def handle_classic_user(self):
		if self.uuid_list:
			self.handlers += [
				self.get_users_list,
				self.handle_root,
				self.handle_admin,
				self.handle_group,
				self.create_plural_query,
				self.create_plural_appends_list,
				self.create_plural_values,
			]
		else:
			self.handlers += [
				self.get_users,
				self.handle_root,
				self.handle_admin,
				self.create_query,
				self.create_appends_list,
				self.create_values
			]

	def handle_group(self):
		if self.uuid_list:
			self.handlers += [
				self.handle_valid_uuids,
			]
		else:
			self.handlers += [
				self.get_users,
				self.handle_users_uinfo,
				self.create_query,
				self.create_appends_list,
				self.create_values
			]

	def handle_valid_uuids(self):
		for uuid in self.uuid_list:
			if not is_valid_uuid(uuid):
				self.message=f"Invalid uuid values - {uuid}"
				self.status_code = 400

	def handle_users_uinfo(self):
		for actor in self.actors:
			if actor.actor_type == "group":
				app.db.execute(
					"""UPDATE actor SET
						uinfo = jsonb_set(uinfo, '{groups}',
						((uinfo->'groups')::jsonb - %s))
						WHERE uinfo->'groups' ? %s""",
					[actor.uuid, actor.uuid]
				)

	def create_query(self):
		self.query = """DELETE FROM actor WHERE uuid={}"""

	def create_appends_list(self):
		self.appends_list += [
			sql.Placeholder("uuid")
		]

	def create_values(self):
		self.values.update({
			"uuid": self.uuid
		})

	def get_auth_users(self):
		try:
			self.actors = [Actor.objects.get(uuid=self.uuid)]
		except ActorNotFound:
			self.actors = list()

	def get_users(self):
		self.actors = [Actor.objects.get(uuid=self.uuid)]
		self.current_actor = get_current_actor()

	def handle_root(self):
		for actor in self.actors:
			if actor.is_root and not self.current_actor.is_root:
				self.message=f"You can't delete root.\n UUID - {self.actor.uuid}," \
					f"Username- {self.actor.username}, Email - {self.actor.email}"
				self.status_code = 400

	def handle_admin(self):
		for actor in self.actors:
			if actor.is_admin and (not self.current_actor.is_root
										or not self.current_actor.is_admin):
				self.message=f"You can't delete admin.\n UUID - {self.actor.uuid}," \
					"Username- {self.actor.username}, Email - {self.acotr.email}"
				self.status_code = 400

	def get_users_list(self):
		self.actors = Actor.objects.filter(uuid__in=self.uuid_list)
		self.current_actor = get_current_actor()

	def create_plural_query(self):
		self.query = "DELETE FROM actor WHERE uuid = ANY({}::uuid[])"

	def create_plural_appends_list(self):
			self.appends_list += [
			sql.Placeholder("uuid_list")
		]

	def create_plural_values(self):
		self.values.update({
			"uuid_list": self.uuid_list
		})
