import time
import constants


def create_clients():
    while True:
        try:
            print("Starting")
            # Configure Keycloak connection
            keycloak_admin = constants.create_keycloak_admin()
            # Define client configuration
            client_representation = {
                "clientId": "trinodb",
                "enabled": True,
                "redirectUris": [f"{constants.trino_url}/oauth2/callback"],
                "publicClient": False,
                "serviceAccountsEnabled": True,
                "protocol": "openid-connect",
                "attributes": {
                    "post.logout.redirect.uris": f"{constants.trino_url}/ui/logout/logout.html"
                },
                "defaultClientScopes": [
                    "service_account",
                    "web-origins",
                    "acr",
                    "profile",
                    "roles",
                    "basic",
                    "email",
                ],
            }

            # Create the client
            client_id = keycloak_admin.create_client(
                payload=client_representation, skip_exists=True
            )
            # need to perform the update otherwise the attributes are not set....
            # keycloak_admin.update_client(client_id, client_representation)
            print(f"Created client with ID: {client_id}")
            # Create client secret
            mapper = {
                "name": "groups",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-group-membership-mapper",  # this is kind of useless
                "consentRequired": False,
                "config": {
                    "full.path": "false",
                    "id.token.claim": "false",
                    "access.token.claim": "true",
                    "claim.name": "groups",
                    "userinfo.token.claim": "false",
                },
            }
            scope = {
                "name": "groups",
                "description": "Mapping groups",
                "protocol": "openid-connect",
                "attributes": {"type": "default"},
                "protocolMappers": [mapper],
            }
            keycloak_admin.create_client_scope(scope, skip_exists=True)
            print("Added mapper to client")

            client_secret = keycloak_admin.generate_client_secrets(client_id)
            print(f"Generated client secret: {client_secret}")
            # Normalize returned secret structure (dict vs string)
            if isinstance(client_secret, dict):
                client_secret_value = (
                    client_secret.get("value")
                    or client_secret.get("secret")
                    or str(client_secret)
                )
            else:
                client_secret_value = str(client_secret)

            print(f"Using client secret: {client_secret_value}")
            # associate service account role to make group plugin work
            client_user_rep = keycloak_admin.get_client_service_account_user(client_id)
            print(f"Found user associated to client: {client_user_rep}")
            # here i don't get very much how it works....
            # but works
            master_realm_client_id = keycloak_admin.get_client_id(
                f"{keycloak_admin.connection.realm_name}-realm"
            )
            if master_realm_client_id is None:
                raise Exception("Cannot find master realm client id")
            print(keycloak_admin.get_client_roles(master_realm_client_id))
            view_users_role = next(
                r
                for r in keycloak_admin.get_client_roles(master_realm_client_id)
                if r["name"] == "view-users"
            )
            keycloak_admin.assign_client_role(
                user_id=client_user_rep["id"],
                client_id=master_realm_client_id or "",
                # we should send a patch upstream
                roles={
                    "id": view_users_role["id"],
                    "name": view_users_role["name"],
                },
            )
            return client_secret_value
        except Exception as e:
            print(f"Error: {e}. Retrying in 5 seconds...")
            import traceback

            traceback.print_exc()
            time.sleep(5)