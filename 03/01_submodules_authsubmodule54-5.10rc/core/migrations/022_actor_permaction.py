from . import base


class Migration(base.BaseMigration):
    """
    Create permactions table.
    """

    table_name = "actor_permaction"
    forwards_query = f"""

        CREATE TABLE {table_name} (
            permaction_uuid uuid,
            actor_uuid uuid references actor(uuid) ON DELETE CASCADE,
            service_uuid uuid references actor(uuid) ON DELETE CASCADE,
            created timestamp DEFAULT (now() at time zone 'utc'),
            value smallint CHECK (value >= 0 AND value <= 1),
            params jsonb,
            PRIMARY KEY(permaction_uuid, actor_uuid, service_uuid)
        );
        """

    backwards_query = f"""
        DROP TABLE {table_name}
    """
