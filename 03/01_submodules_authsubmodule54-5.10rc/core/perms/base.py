class BasePerms:
    """
    Base permissions class
    """
    def __init__(self, user, permaction_uuid, source_class):
        self.user = user
        self.source_class = source_class
        self.permaction_uuid = permaction_uuid
