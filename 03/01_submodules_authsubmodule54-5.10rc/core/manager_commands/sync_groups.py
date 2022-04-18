from flask_script import Command
from ..service_view import GetAndUpdateGroups


class SyncGroups(Command):
    """
    Synchronization service groups with auth groups
    """
    def run(self, *args, **kwargs):

        try:
            groups = GetAndUpdateGroups().update_groups()
        except Exception:
            print('\033[91mError with getting default groups. Check that your service is registered on auth and'
                  ' have the necessary permissions for getting groups\033[0m')
            return

        if groups is None:
            print('\033[91mError with getting default groups. Check that your service is registered on auth and'
                  ' have the necessary permissions for getting groups\033[0m')
            return

        print(f'\033[92mGroups successfully synchronized with auth\033[0m')

        return
