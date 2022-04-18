from typing import Callable, Dict, List
from flask import current_app as app
from werkzeug.exceptions import Unauthorized

from .base import BasePerms


class BiomLevelPermactionChain(BasePerms):

    def __init__(self, service_uuid, user, permaction_uuid, source_class):
        super().__init__(
            user=user,
            permaction_uuid=permaction_uuid,
            source_class=source_class
        )
        self.service_uuid = service_uuid
        self.type_switch = {
            "check": self.handle_check_permactions,
            "simple": self.handle_simple_permactions,
        }

    def check(self):
        return self.status_check() if self.status_check()\
            else self.check_permissions()

    def status_check(self):
        result = False

        if self.user.is_root:
            result = True
        elif self.user.is_banned:
            raise Unauthorized
        elif self.user.is_admin:
            result =  True

        return result

    def check_permissions(self) -> bool:
        """
        Check permactions
        @subm_flow Check permactions
        """
        permission = self.get_permactions()
        handler = self.type_switch.get(permission.get("perm_type"))
        result = handler(permission)
        return result

    def get_permactions(self) -> Dict:
        # Get actor special permissions

        result = app.db.fetchone("""
            SELECT APA.params as params,
                APA.value as value, perm_type as perm_type
            FROM actor_permaction AS APA
                LEFT JOIN default_permaction AS ADA
                ON APA.permaction_uuid = ADA.permaction_uuid
            WHERE actor_uuid=%s
                AND APA.service_uuid=%s
                AND APA.permaction_uuid=%s;
        """, (self.user.uuid, self.service_uuid, self.permaction_uuid))

        if not result:
            # Get group permission by weight
            result = app.db.fetchone("""
                SELECT GPA.params as params, GPA.value as value,
                    perm_type as perm_type
                FROM group_permaction AS GPA
                    LEFT JOIN default_permaction AS ADA
                    ON GPA.permaction_uuid = ADA.permaction_uuid
                WHERE GPA.service_uuid=%s
                    AND GPA.permaction_uuid=%s
                    AND GPA.actor_uuid = ANY(%s::uuid[])
                ORDER BY weight DESC
                LIMIT 1;
            """, (
                self.service_uuid,
                self.permaction_uuid,
                self.user.uinfo.get("groups")
                )
            )

        if not result:
            # Get default permission with default value and params
            result = app.db.fetchone("""
                SELECT params as params, value as value,
                    perm_type as perm_type
                FROM default_permaction
                WHERE service_uuid=%s
                    AND permaction_uuid=%s
            """, (self.service_uuid, self.permaction_uuid))

        return result

    def handle_check_permactions(self, permission) -> bool:
        result = False
        if (not permission.get("params")
            or permission.get("params", {}).get("status", 1) == 0
        ):
            result = True if permission.get("value") else False
        else:
            result = self.source_class.biom_perm(permission.get("params"))
        return result

    def handle_simple_permactions(self, permission) -> bool:
        return True if permission.get("value") else False
