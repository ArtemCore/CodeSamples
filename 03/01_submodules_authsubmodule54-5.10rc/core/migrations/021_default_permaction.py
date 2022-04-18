from . import base


class Migration(base.BaseMigration):
    """
    Create permactions table.
    """

    table_name = "default_permaction"
    forwards_query = f"""

        CREATE TABLE {table_name} (
            permaction_uuid uuid,
            service_uuid uuid references actor(uuid) ON DELETE CASCADE,
            value smallint CHECK (value >= 0 AND value <= 1),
            perm_type character varying(64) CHECK (perm_type='simple' OR perm_type='check'),
            description character varying(1024),
            title character varying(512),
            created timestamp DEFAULT (now() at time zone 'utc'),
            unions text[],
            params jsonb,
            PRIMARY KEY(permaction_uuid, service_uuid)
        );
        """

    backwards_query = f"""
        DROP TABLE {table_name}
    """
