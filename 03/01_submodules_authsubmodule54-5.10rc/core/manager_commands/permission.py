import inspect
import json
import requests

from flask import current_app as app
from importlib import import_module
from urllib.parse import urljoin
from typing import Callable, List, Dict, Tuple

from .base import BaseCommand
from ..ecdsa_lib import sign_data
from ..utils import check_if_auth_service
from ..utils import delete_old_permactions
from ..utils import json_dumps
from ..utils import get_auth_domain
from ..utils import get_language_header
from ..utils import insert_or_update_default_permaction


class CollectPerms(BaseCommand):

    def run(self):
        result: Dict = dict()
        if not app.config.get('SERVICE_UUID'):
            result.update(message='Error. There is no SERVICE_UUID')
        else:
            permaction_message = self.execute_command()
            result.update(
                permaction_message=permaction_message,
            )
        self.print_result(**result)

    def execute_command(self):
        actions_files = self.get_actions_files()

        permaction_result = self.collect_perms(actions_files)

        permaction_message =\
            self.save_permissions(permaction_result)

        return permaction_message

    def get_actions_files(self) -> Tuple:
        actions_path_files = self._get_path('actions')
        return (
            path.replace('/', '.') + "." + action[:-3]
            for path in actions_path_files
            for action in self._clean_and_sort(self._listdir_no_hidden(path))
        )

    def collect_perms(self, actions_files: Tuple[str]) -> Tuple[List[Dict], List[Dict]]:
        permaction_result = list()
        for module_path in actions_files:
            module = import_module(module_path)
            clsmembers = inspect.getmembers(module, inspect.isclass)

            [permaction_result.append(self.handle_base_permaction(cls))
                for cls in dict(clsmembers).values()
                if "BasePermAction" in [
                    base.__name__ for base in cls.__bases__
                ]
            ]
        return permaction_result


    def handle_base_permaction(self, class_obj: type) -> Dict:
        permission = class_obj.collect_all_perms()
        return {
                'permaction_uuid': permission.get("permaction_uuid"),
                'value': permission.get("value"),
                'description': permission.get("description"),
                'title': permission.get("title"),
                'perm_type': permission.get('perm_type'),
                "service_uuid": app.config['SERVICE_UUID'],
                "unions": permission.get("unions"),
                "params": permission.get("params"),
            }

    def save_permissions(
        self,
        permissions: List[Dict]
    ) -> str:
        result_message: str = None
        delete_old_permactions(permissions)
        if permissions == []:
            result_message = 'There is no permissions'
        elif check_if_auth_service():
            insert_or_update_default_permaction(permissions)
            result_message = 'Response status - 200 \nResponse content - Successfully created'
        else:
            signature = sign_data(app.config['SERVICE_PRIVATE_KEY'], json_dumps(permissions, sort_keys=True))

            request_data = {
                "permissions": permissions,
                "signature": signature,
                "service_uuid": app.config['SERVICE_UUID']
            }

            response = requests.post(
                urljoin(
                    get_auth_domain(),
                    '/service/permactions/default'
                ),
                json=request_data,
                headers=get_language_header()
            )

            try:
                content = response.json()
                if content.get('error'):
                        result_message = 'Response status - %s \nResponse content - %s' % (
                        response.status_code, "\n".join(
                            [f"{field}: {message}" for field, message
                            in content.get('error_content', {}).items()])
                    )
                else:
                    insert_or_update_default_permaction(permissions)
                    result_message = 'Response status - %s \nResponse content - %s' % (
                        response.status_code, content.get('message')
                    )
            except json.JSONDecodeError:
                result_message = 'Error with updating permissions on auth service'
        return result_message

    def print_result(self, **kwargs):
        for item, value in kwargs.items():
            print("-"*120)
            print(item.replace("_", " ").capitalize() + ":")
            print(value)
