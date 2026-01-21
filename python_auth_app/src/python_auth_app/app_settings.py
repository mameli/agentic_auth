from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    client_id: str = "pythonapp"
    realm: str = "master"
    client_secret: str
    oidc_url: str = 'https://keycloak:8443'
    client_scope: str = 'openid profile email'
    app_secret_key: str = "secret"
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
    )