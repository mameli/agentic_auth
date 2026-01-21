
from keycloak import KeycloakAdmin


keycloak_endpoint = "https://keycloak:8443"
trino_url = "https://trinodb:8543"
app_url = "http://webapp:5555"
trinodb_client_id = "trinodb"
webapp_client_id = "pythonapp"
token_exchange_scope = "scope-token-exchange"

def create_keycloak_admin() -> KeycloakAdmin:
    return KeycloakAdmin(
        server_url=keycloak_endpoint,
        username="admin",
        password="admin",
        realm_name="master",
        client_id="admin-cli",
        verify=False,
    )