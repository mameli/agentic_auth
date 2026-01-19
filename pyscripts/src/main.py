import create_user
import create_client
from pathlib import Path
import re
import urllib3


def _update_trino_client_secret(trino_config_path: Path, key: str, secret: str):
    trino_config_path = Path(trino_config_path)
    if not trino_config_path.exists():
        print(f"Trino config file {trino_config_path} not found, skipping update.")
        return
    text = trino_config_path.read_text()
    # create a backup
    backup = trino_config_path.with_name(trino_config_path.name + ".bak")
    backup.write_text(text)
    if key in text:
        new_text = re.sub(
            r"^" + re.escape(key) + r".*$", f"{key}{secret}", text, flags=re.M
        )
    else:
        new_text = text + f"\n{key}{secret}\n"
    trino_config_path.write_text(new_text)
    print(f"Updated {trino_config_path} (backup at {backup})")


def main():
    urllib3.disable_warnings()
    create_user.create_users()
    secret = create_client.create_clients()
    if secret:
        root = Path("/")
        trino_config = root / "trino" / "config.properties"
        trino_group_config = root / "trino" / "group-provider.properties"
        _update_trino_client_secret(
            trino_config, "http-server.authentication.oauth2.client-secret=", secret
        )
        _update_trino_client_secret(
            trino_group_config, "keycloak.client-secret=", secret
        )
    else:
        print("No client secret returned; skipping Trino update")


if __name__ == "__main__":
    main()
