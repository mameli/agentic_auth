import time
from typing import Any

from keycloak import KeycloakAdmin
import constants


def normalize_secret(client_secret: dict | str) -> str:
    if isinstance(client_secret, dict):
        return (
            client_secret.get("value")
            or client_secret.get("secret")
            or str(client_secret)
        )
    else:
        return str(client_secret)


def create_groups_scope(keycloak_admin: KeycloakAdmin):
    """
    This adds a default scope so that all tokens
    will contain the list of groups
    """
    scope = {
        "name": "groups",
        "description": "Mapping groups",
        "protocol": "openid-connect",
        "attributes": {"type": "default"},
        "protocolMappers": [
            {
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
        ],
    }
    keycloak_admin.create_client_scope(scope, skip_exists=True)


def add_view_role_to_client(keycloak_admin: KeycloakAdmin, client_id: str):
    # associate service account role to make group plugin work
    client_user_rep = keycloak_admin.get_client_service_account_user(client_id)

    # here i don't get very much how it works....
    # but works
    master_realm_client_id = keycloak_admin.get_client_id(
        f"{keycloak_admin.connection.realm_name}-realm"
    )
    if master_realm_client_id is None:
        raise Exception("Cannot find master realm client id")
    view_users_role = next(
        r
        for r in keycloak_admin.get_client_roles(master_realm_client_id)
        if r["name"] == "view-users"
    )
    keycloak_admin.assign_client_role(
        user_id=client_user_rep["id"],
        client_id=master_realm_client_id or "",
        # we should send a patch upstream to fix this function typing
        roles=[
            {
                "id": view_users_role["id"],
                "name": view_users_role["name"],
            }
        ],
    )


def create_app_client(keycloak_admin: KeycloakAdmin):
    while True:
        try:
            # Define client configuration
            client_representation = {
                "clientId": constants.webapp_client_id,
                "enabled": True,
                "redirectUris": [f"{constants.app_url}/callback"],
                "publicClient": False,
                "protocol": "openid-connect",
                "attributes": {
                    "post.logout.redirect.uris": f"{constants.app_url}",
                    # this is needed otherwise it won't be able to perform OBO flow
                    "standard.token.exchange.enabled": "true",
                },
            }

            # Create the client
            client_id = keycloak_admin.create_client(
                payload=client_representation, skip_exists=True
            )

            print(f"Created client with ID: {client_id}")

            # this creates a scope that must be requested in order to enable
            # the token exchange for the desired audience
            scope = {
                "name": constants.token_exchange_scope,
                "description": "Allowing token exchange",
                "protocol": "openid-connect",
                "attributes": {
                    "type": "default",
                    "include.in.token.scope": "true",
                    "display.on.consent.screen": "false",
                },
                "protocolMappers": [
                    {
                        "name": f"{constants.trinodb_client_id}-audience-mapper",
                        "protocol": "openid-connect",
                        "protocolMapper": "oidc-audience-mapper",
                        "consentRequired": False,
                        "config": {
                            "included.client.audience": constants.trinodb_client_id,
                            "id.token.claim": "false",
                            "access.token.claim": "true",
                        },
                    }
                ],
            }
            client_scope_id = keycloak_admin.create_client_scope(
                scope, skip_exists=True
            )
            keycloak_admin.add_client_optional_client_scope(
                client_id=client_id,
                client_scope_id=client_scope_id,
                payload={
                    "realm": keycloak_admin.connection.realm_name,
                    "client": client_id,
                    "clientScopeId": client_scope_id,
                },
            )

            # Create client secret
            client_secret = keycloak_admin.generate_client_secrets(client_id)
            # Normalize returned secret structure (dict vs string)
            return normalize_secret(client_secret)
        except Exception as e:
            print(f"Error: {e}. Retrying in 5 seconds...")
            import traceback

            traceback.print_exc()
            time.sleep(5)


def create_trino_client(keycloak_admin: KeycloakAdmin):
    while True:
        try:
            # Define client configuration
            client_representation = {
                "clientId": constants.trinodb_client_id,
                "enabled": True,
                "redirectUris": [f"{constants.trino_url}/oauth2/callback"],
                "publicClient": False,
                "serviceAccountsEnabled": True,
                "protocol": "openid-connect",
                "attributes": {
                    "post.logout.redirect.uris": f"{constants.trino_url}/ui/logout/logout.html",
                },
                "defaultClientScopes": [
                    # the service_account is mandatory so that it's possible to
                    # perform keycloak API calls like the one to retrieve groups
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
            # create_groups_scope(keycloak_admin)
            add_view_role_to_client(keycloak_admin, client_id)
            client_secret = keycloak_admin.generate_client_secrets(client_id)
            return normalize_secret(client_secret)
        except Exception as e:
            print(f"Error: {e}. Retrying in 5 seconds...")
            import traceback

            traceback.print_exc()
            time.sleep(5)
