from keycloak import KeycloakAdmin


keycloak_endpoint = "https://keycloak:8443"
trino_url = "https://trinodb:8543"
app_url = "http://webapp:5555"

def create_keycloak_admin() -> KeycloakAdmin:
    return KeycloakAdmin(
        server_url=keycloak_endpoint,
        username="admin",
        password="admin",
        realm_name="master",
        client_id="admin-cli",
        verify=False,
    )
