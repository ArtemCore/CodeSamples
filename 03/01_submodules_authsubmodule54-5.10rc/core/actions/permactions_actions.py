import json

from typing import List
from typing import Optional
from typing import Dict
from typing import Tuple
from typing import Union

from flask import current_app as app

from ..actor import Actor
from ..utils import create_response_message


class GetGroupPermsAction:

    def __init__(self, actor_uuid) -> None:
        self.actor_uuid = actor_uuid

    def execute(self) -> List:
        permissions = app.db.fetchall("""
            SELECT
                DPA.description as description,
                DPA.service_uuid as service_uuid,
                DPA.permaction_uuid as permaction_uuid,
                DPA.title as title,
                DPA.unions as unions,
                DPA.params as default_params,
                DPA.perm_type as perm_type,
                GPA.value as value,
                GPA.params as params,
                GPA.actor_uuid as actor_uuid,
                GPA.created as created,
                GPA.weight as weight
            FROM
                default_permaction AS DPA
                LEFT JOIN group_permaction AS GPA
                ON DPA.permaction_uuid = GPA.permaction_uuid
            WHERE
                GPA.actor_uuid = ANY(%s::uuid[])
            ORDER BY 
                GPA.weight desc 
            """,
            [self.actor_uuid]
          )
        return permissions


class GetActorPermsAction:

    def __init__(self, actor_uuid) -> None:
        self.actor_uuid = actor_uuid

    def execute(self) -> Dict:
        actor_permissions = app.db.fetchall("""
            SELECT
                DPA.description as description,
                DPA.service_uuid as service_uuid,
                DPA.permaction_uuid as permaction_uuid,
                DPA.title as title,
                DPA.unions as unions,
                DPA.params as default_params,
                DPA.perm_type as perm_type,
                APA.value as value,
                APA.params as params,
                APA.actor_uuid as actor_uuid,
                APA.created as created
            FROM
                default_permaction AS DPA
                LEFT JOIN actor_permaction AS APA
                ON DPA.permaction_uuid = APA.permaction_uuid
            WHERE
                APA.actor_uuid = ANY(%s::uuid[]);
            """,
            [self.actor_uuid]
        )
        return actor_permissions


class GetDefaultPermsAction:

    def execute(self) -> Union[Dict, List]:
        default_permactions = app.db.fetchall(
            """SELECT * FROM default_permaction""",
        )
        return default_permactions


class GetAllPermsAction:

    def __init__(self, actor_uuid) -> None:
        self.actor_perms: Optional[List] = None
        self.groups_perms: Optional[List] = None
        self.default_perms: Optional[List] = None
        self.perms = dict()
        self.actor_uuid = actor_uuid
        self.actor = Actor.objects.get(uuid=self.actor_uuid)
        self.groups = [group.uuid for group in self.actor.get_groups()]

    def execute(self) -> Dict:
        self.get_actor_perms()
        self.get_groups_perms()
        self.get_default_perms()
        return self.perms

    def get_actor_perms(self) -> None:
        self.actor_perms = GetActorPermsAction([self.actor_uuid]).execute()
        self.perms['actor'] = self.actor_perms

    def get_groups_perms(self) -> None:
        if self.actor.actor_type == 'group':
            self.groups_perms = GetGroupPermsAction([self.actor_uuid]).execute()
            self.perms['actor'] = self.groups_perms
        else:
            self.groups_perms = GetGroupPermsAction(self.groups).execute()
            self.perms['groups'] = self.groups_perms

    def get_default_perms(self) -> None:
        self.default_perms = GetDefaultPermsAction().execute()
        self.perms['default'] = self.default_perms


class BasePermactionAction:

    def __init__(self, data: Dict) -> None:
        self.actor_uuid: str = data.get('actor_uuid')
        self.perm_uuid: str = data.get('perm_uuid')
        self.value: Optional[str] = data.get('value')
        self.params: Optional[str] = data.get('params')
        self.weight: Optional[int] = data.get('weight')
        self.query: Optional[str] = None
        self.sql_params: Optional[List] = None
        self.actor = Actor.objects.get(uuid=self.actor_uuid)
        self.table_name: Optional[str] = None
        self.error: bool = False
        self.response: dict = create_response_message("Success")
        self.status_code: int = 200

    def execute_sql(self):
        try:
            app.db.execute(self.query, self.sql_params)
        except Exception as e:
            print(f'Exception on {self.__class__.__name__}! {e}')
            self.error = True

    def check_error(self) -> None:
        if self.error:
            self.response = create_response_message("Something went wrong", error=True)
            self.status_code = 400


class SetPermactionAction(BasePermactionAction):

    def __init__(self, data: Dict) -> None:
        super().__init__(data)

    def execute(self) -> Tuple[Dict, int]:
        self.select_sql()
        self.execute_sql()
        self.check_error()
        return self.response, self.status_code

    def select_sql(self):
        if self.actor.actor_type in ['classic_user', 'user', 'service']:
            self.query = """INSERT INTO actor_permaction(permaction_uuid, actor_uuid, service_uuid, value, params)
                                       VALUES(%s, %s, %s, %s, %s)"""
            self.sql_params = [self.perm_uuid, self.actor_uuid, app.config.get('SERVICE_UUID'),
                               self.value, json.dumps(self.params)]
        elif self.actor.actor_type == 'group':
            self.query = """INSERT INTO group_permaction(permaction_uuid, actor_uuid, service_uuid, value,
                             params, weight) VALUES(%s, %s, %s, %s, %s, %s)"""
            self.sql_params = [self.perm_uuid, self.actor_uuid, app.config.get('SERVICE_UUID'),
                               self.value, json.dumps(self.params), self.actor.uinfo['weight']]


class UpdatePermactionAction(BasePermactionAction):

    def __init__(self, data: Dict) -> None:
        super().__init__(data)

    def execute(self) -> Tuple[Dict, int]:
        self.select_sql()
        self.execute_sql()
        self.check_error()
        return self.response, self.status_code

    def select_sql(self):
        if self.actor.actor_type in ['classic_user', 'user', 'service']:
            self.query = """UPDATE actor_permaction SET value = %s, params = %s
                                    WHERE actor_uuid = %s and permaction_uuid = %s"""
            self.sql_params = [self.value, json.dumps(self.params), self.actor_uuid, self.perm_uuid]
        elif self.actor.actor_type == 'group':
            self.query = """UPDATE group_permaction SET value = %s, params = %s, weight = %s
                        WHERE actor_uuid = %s and permaction_uuid = %s"""
            self.sql_params = [self.value, json.dumps(self.params), self.actor.uinfo['weight'],
                               self.actor_uuid, self.perm_uuid]


class DeletePermactionAction(BasePermactionAction):

    def __init__(self, data: Dict) -> None:
        super().__init__(data)

    def execute(self) -> Tuple[Dict, int]:
        self.select_sql()
        self.execute_sql()
        self.check_error()
        return self.response, self.status_code

    def select_sql(self):
        if self.actor.actor_type in ['classic_user', 'user', 'service']:
            self.query = """DELETE FROM actor_permaction WHERE actor_uuid = %s and permaction_uuid = %s"""
        elif self.actor.actor_type == 'group':
            self.query = """DELETE FROM group_permaction WHERE actor_uuid = %s and permaction_uuid = %s"""
        self.sql_params = [self.actor_uuid, self.perm_uuid]
