import create_user
import create_client
from pathlib import Path
import urllib3
import constants


def create_env_file(file: Path, values: dict[str, str]):
    print(f"Creating env file {file}")
    content = "\n".join([f"{k}={v}" for k, v in values.items()])
    file.write_text(content)
    print(f"Written {file} with content:\n{content}")


def main():
    urllib3.disable_warnings()
    keycloak_admin = constants.create_keycloak_admin()
    create_user.create_users(keycloak_admin)
    secret = create_client.create_trino_client(keycloak_admin)
    if secret:
        trino_env_file = Path("/") / "env_files" / "trino.env"
        create_env_file(trino_env_file, {"OAUTH2_CLIENT_SECRET": secret})
    else:
        print("No client secret returned; skipping Trino update")
    secret = create_client.create_app_client(keycloak_admin)
    if secret:
        webapp_env_file = Path("/") / "env_files" / "webapp.env"
        create_env_file(webapp_env_file, {"client_secret": secret})


if __name__ == "__main__":
    main()
