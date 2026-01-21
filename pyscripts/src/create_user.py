from keycloak import KeycloakAdmin
import time


def create_group(keycloak_admin):
    """Create the trino-admins group if it doesn't exist and return its ID."""
    try:
        group_data = {
            "name": "trino-admins",
        }
        group_id = keycloak_admin.create_group(payload=group_data, skip_exists=True)
        print(f"Group 'trino-admins' exists or created with ID: {group_id}")

        # If skip_exists=True and group already exists, we need to fetch it
        if not group_id:
            groups = keycloak_admin.get_groups()
            for group in groups:
                if group["name"] == "trino-admins":
                    group_id = group["id"]
                    break

        return group_id
    except Exception as e:
        print(f"Error creating group: {e}")
        raise


def create_user_obj(name: str, surname: str):
    return {
        "email": f"{name}.{surname}@agilelab.it",
        "username": f"{name}.{surname}",
        "enabled": True,
        "firstName": name.capitalize(),
        "lastName": surname.capitalize(),
    }


def create_users(keycloak_admin: KeycloakAdmin):
    while True:
        try:
            # Create the group
            group_id = create_group(keycloak_admin)

            # Create user
            print("Creating user antonio")
            new_user = create_user_obj("antonio", "murgia")
            user_id = keycloak_admin.create_user(new_user, exist_ok=True)
            keycloak_admin.set_user_password(
                user_id, "StrongP@ssword123", temporary=False
            )
            print(f"User created with ID: {user_id}")

            # Add antonio to trino-admins group
            keycloak_admin.group_user_add(user_id, group_id)
            print(f"Added user {user_id} to trino-admins group")

            print("Creating user andrea")
            new_user = create_user_obj("andrea", "fonti")
            user_id = keycloak_admin.create_user(new_user, exist_ok=True)
            keycloak_admin.set_user_password(
                user_id, "StrongP@ssword123", temporary=False
            )
            print(f"User created with ID: {user_id}")
            return

        except Exception as e:
            print(f"Error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
