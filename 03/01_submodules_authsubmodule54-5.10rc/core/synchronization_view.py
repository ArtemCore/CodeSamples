import zipfile

from flask import current_app as app
from flask import jsonify, make_response, request
from flask.views import MethodView
from flask_cors import cross_origin

from .decorators import auth_service_only, data_parsing
from .ecdsa_lib import verify_signature
from .utils import check_if_auth_service, json_dumps


class GetSynchronizationHash(MethodView):
    """
    @POST Request on getting a actor, group, permaction hash@
    """

    @auth_service_only
    @cross_origin()
    @data_parsing
    def post(self, data, **kwargs):
        """
                Request on getting a actor, group, permaction hash
                @subm_flow Request on getting a actor, group, permaction hash
                """
        if data and (
            verify_signature(
                app.config.get("AUTH_PUB_KEY", ""),
                data.pop("signature"),
                json_dumps(data, sort_keys=True),
            )
            or check_if_auth_service()
        ):

            response = dict(
                actor_hash=self.get_actor_hash(),
                group_hash=self.get_actor_group_hash(),
                permactions_hash_data=self.get_permactions_hash_data(),
            )
            status_code = 200
        else:
            response = dict(message="Receiving synchronization hashes failed.")

            status_code = 400
        return make_response(jsonify(response), status_code)

    def get_actor_hash(self):
        return (
            app.db.fetchone(
                """
                SELECT md5(array_agg(md5((t.*)::varchar))::varchar) AS actor_hash
                FROM (
                        SELECT uuid, root_perms_signature, initial_key, secondary_keys, uinfo, actor_type
                        FROM actor
                        WHERE actor_type IN ('classic_user', 'user', 'group', 'service')
                        ORDER BY uuid
                    ) AS t;
                """
            ).get("actor_hash")
            or "0"
        )

    def get_actor_group_hash(self):
        return (
            app.db.fetchone(
                """
                SELECT md5(array_agg(md5((t.*)::varchar))::varchar) AS group_hash
                FROM (
                        SELECT uuid, uinfo
                        FROM actor
                        WHERE actor_type = 'group'
                        ORDER BY uuid
                    ) AS t;
                """
            ).get("group_hash")
            or "0"
        )

    def get_permactions_hash_data(self):
        if check_if_auth_service():
            result = dict()
            services = app.db.fetchall(
                f"""SELECT uuid from actor where actor_type='service' and uuid != '{app.config.get("SERVICE_UUID")}' """
            )
            base_query = """SELECT md5(array_agg(md5((t.*)::varchar))::varchar) AS hash
                 FROM (
                     SELECT permaction_uuid, params, actor_uuid, service_uuid, value
                     FROM {}_permaction
                     WHERE service_uuid = '{}'
                     ORDER BY permaction_uuid
                 ) AS t;
                 """
            for service in services:
                result[service["uuid"]] = {
                    "actor_permactions_hash": app.db.fetchone(
                        base_query.format("actor", service["uuid"])
                    ).get("hash")
                    or "0",
                    "group_permactions_hash": app.db.fetchone(
                        base_query.format("group", service["uuid"])
                    ).get("hash")
                    or "0",
                }
            return result
        else:
            base_query = """
                SELECT md5(array_agg(md5((t.*)::varchar))::varchar) AS hash
                FROM (
                    SELECT permaction_uuid, params, actor_uuid, service_uuid, value
                    FROM {}_permaction
                    ORDER BY permaction_uuid
                ) AS t;
                """
            actor_permactions_hash = (
                app.db.fetchone(base_query.format("actor")).get("hash") or "0"
            )
            group_permactions_hash = (
                app.db.fetchone(base_query.format("group")).get("hash") or "0"
            )
            return dict(
                actor_permactions_hash=actor_permactions_hash,
                group_permactions_hash=group_permactions_hash,
            )


class ProcessForcedSynchroniationDataView(MethodView):
    """
    @POST Force synchroniation@
    """

    @auth_service_only
    @cross_origin()
    @data_parsing
    def post(self, data, **kwargs):
        if check_if_auth_service():
            response = dict(
                message="Forced synchronization process is not available for Auth service."
            )
            status_code = 400

        elif data and verify_signature(
            app.config["AUTH_PUB_KEY"],
            data.pop("signature"),
            json_dumps(data, sort_keys=True),
        ):

            if "actors" in request.files:
                file = request.files.get("actors")
                data = self.get_data_from_zip(file)

                query = (
                    "INSERT INTO actor SELECT * FROM jsonb_populate_recordset(null::actor, jsonb %s) ON CONFLICT(uuid) "
                    "DO UPDATE SET root_perms_signature=EXCLUDED.root_perms_signature, initial_key=EXCLUDED.initial_key, secondary_keys = EXCLUDED.secondary_keys, uinfo=EXCLUDED.uinfo;"
                )
                app.db.execute(query, [data.decode("utf-8")])

                response = dict(message="Success.")
                status_code = 200

            elif "actors_uuids" in request.files:
                data = self.get_data_from_zip(request.files.get("actors_uuids"))

                delete_query = """DELETE FROM actor WHERE actor_type IN ('classic_user', 'user', 'group', 'service') AND NOT (uuid = ANY(
                        SELECT uuid FROM jsonb_populate_recordset(null::actor, jsonb %s)))"""
                app.db.execute(delete_query, [data.decode("utf-8")])

                response = dict(message="Success.")
                status_code = 200

            elif (
                "actor_permactions" in request.files
                and "group_permactions" in request.files
            ):

                def perms_sync(relation, data):
                    query = f"INSERT INTO {relation}_permaction SELECT * FROM jsonb_populate_recordset(null::{relation}_permaction, jsonb %s)"

                    delete_query = f"DELETE FROM {relation}_permaction"
                    app.db.execute(delete_query)
                    app.db.execute(query, [data.decode("utf-8")])

                apa_data = self.get_data_from_zip(
                    request.files.get("actor_permactions")
                )
                perms_sync("actor", apa_data)

                gpa_data = self.get_data_from_zip(
                    request.files.get("group_permactions")
                )
                perms_sync("group", gpa_data)

                response = dict(message="Success.")
                status_code = 200
            else:
                response = dict(message="Invalid files data.")
                status_code = 400

        else:
            response = dict(message="Verify signature process failed.")
            status_code = 400
        return make_response(jsonify(response), status_code)

    def get_data_from_zip(self, zip_file):
        with zipfile.ZipFile(zip_file) as zip:
            with zip.open("auth_data.json") as jfile:
                return jfile.read()
