from abc import ABC, abstractmethod, abstractclassmethod
from typing import List, Dict

"""
Base class for actions. This class contains general function for some permissions.
Like comparing dates or checking some time range and other.
All actions should be inherited from BaseAction class.
"""


class BasePermAction(ABC):

    @classmethod
    def collect_all_perms(cls) -> Dict:
        """
        Method handles biom permission of current action with default values and permission type
        """

        result = {
            'perm_type': cls.permaction_type(),
            'value': cls.default_value(),
            'permaction_uuid': cls.permaction_uuid(),
            'description': cls.description(),
            'title': cls.title(),
            'unions': cls.unions(),
            'params': cls.params()
        }
        return result

    @abstractmethod
    def execute(self):
        """Main executable method of action."""

    @abstractmethod
    def biom_perm(self, params: Dict) -> bool:
        """Permission function. 
            There is implementation of access
            validation logic of action.
        """

    @abstractclassmethod
    def description(cls) -> str:
        """There is description of permission."""

    @abstractclassmethod
    def title(cls) -> str:
        """There is title of permission."""

    @abstractclassmethod
    def permaction_uuid(cls) -> str:
        """There is uuid of permaction."""

    @abstractclassmethod
    def permaction_type(cls) -> str:
        """There is type of permission:
                1. simple - permission return True or False
                2. check - code inside permission will be executed
                    and return True or False."""

    @abstractclassmethod
    def default_value(cls) -> int:
        """There is default value of permission:
                1. 0 - user can't execute action by default
                2. 1 - user can execute action by default
            For check permissions:
                1. 0 - permission just return False
                2. 1 - code inside of permission will be executed
                    and permission return True or False.
        """

    @abstractclassmethod
    def unions(cls) -> List[str]:
        """This is unions of permaction.
            Each permactions should be
            included at least in one union.
        """

    @classmethod
    def params(cls) -> List[str]:
        """This is default params
            for check permaction.
            There can be example of
            a body of check permission.
        """
        return {}
