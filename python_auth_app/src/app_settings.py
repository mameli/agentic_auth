from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    oidc_name: str = "keycloak"
    client_id: str = "pythonapp"
    client_secret: str
    server_metadata_url: str = 'https://keycloak:8443/realms/master/.well-known/openid-configuration'
    client_scope: str = 'openid profile email'
    app_secret_key: str = "secret"
    port: int = 5555
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
    )