from typing import Dict, Optional, Tuple

from flask import current_app as app

from ..actor import Actor
from ..utils import (create_response_message, get_current_actor, hash_md5,
                     json_dumps)


class UpdateProfileAction:
    def __init__(self, data: Dict) -> None:
        self.data = data
        self.actor = get_current_actor()
        self.error = False
        self.response = create_response_message(message="Profile successfully updated")
        self.status_code = 200

    def execute(self) -> Tuple[Dict, int]:
        self.hash_password()
        self.execute_query()
        self.check_error()
        return self.response, self.status_code

    def hash_password(self) -> None:
        if self.data.get("password").strip():
            self.data["password"] = hash_md5(self.data.get("password"))
        else:
            self.data.pop("password")

    def execute_query(self):
        try:
            query = """UPDATE actor SET uinfo=uinfo || %s WHERE uuid=%s"""
            values = [json_dumps(self.data), self.actor.uuid]
            app.db.execute(query, values)
        except Exception as e:
            print(f"Exception on updating profile! {e}")
            self.error = True

    def check_error(self):
        if self.error:
            self.response = create_response_message(
                message="Some error occurred while profile updating.", error=True
            )
            self.status_code = 400


class UpdateActorAction:
    def __init__(self, data: Dict, uuid: str) -> None:
        self.data = data
        self.error = False
        self.actor = Actor.objects.get(uuid=uuid)
        self.query: Optional[str] = None
        self.values: Optional[list] = None
        self.response = create_response_message(message="Actor successfully updated")
        self.status_code = 200

    def execute(self) -> Tuple[Dict, int]:
        self.select_query()
        self.execute_query()
        self.check_error()
        return self.response, self.status_code
        pass

    def select_query(self) -> None:
        if self.actor.actor_type in ["classic_user", "user"]:
            self.hash_password()
            self.query = """UPDATE actor SET uinfo=uinfo || %s WHERE uuid=%s"""
            self.values = [json_dumps(self.data), self.actor.uuid]

        elif self.actor.actor_type == "group":
            users = self.data.get("users")
            if len(users) == 0:
                self.query = """UPDATE actor SET uinfo = jsonb_set(uinfo, '{groups}', (uinfo->'groups') - %s)
                               WHERE actor_type IN ('user', 'classic_user'); UPDATE actor SET uinfo = uinfo || %s 
                               WHERE uuid = %s"""
                self.values = [
                    self.actor.uuid,
                    json_dumps(
                        {
                            "group_name": self.data.get("group_name"),
                            "weight": self.data.get("weight"),
                        }
                    ),
                    self.actor.uuid,
                ]
            else:
                self.query = """UPDATE actor SET uinfo = jsonb_set(uinfo, '{groups}', uinfo->'groups' || %s) WHERE
                               actor_type IN ('user', 'classic_user') AND NOT uinfo->'groups' @> %s AND uuid IN %s;
                               UPDATE actor SET uinfo = jsonb_set(uinfo, '{groups}', (uinfo->'groups') - %s) WHERE 
                               actor_type IN ('user', 'classic_user') AND uuid NOT IN %s; UPDATE actor 
                               SET uinfo = uinfo || %s WHERE uuid = %s"""
                self.values = [
                    json_dumps(self.actor.uuid),
                    json_dumps(self.actor.uuid),
                    tuple(users),
                    self.actor.uuid,
                    tuple(users),
                    json_dumps(
                        {
                            "group_name": self.data.get("group_name"),
                            "weight": self.data.get("weight"),
                        }
                    ),
                    self.actor.uuid,
                ]

    def hash_password(self) -> None:
        if self.data.get("password").strip():
            self.data["password"] = hash_md5(self.data.get("password"))
        else:
            self.data.pop("password")

    def execute_query(self) -> None:
        try:
            app.db.execute(self.query, self.values)
        except Exception as e:
            print(f"Exception on updating actor! {e}")
            self.error = True

    def check_error(self) -> None:
        if self.error:
            self.response = create_response_message(
                message="Some error occurred while actor updating.", error=True
            )
            self.status_code = 400
