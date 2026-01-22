# Keycloak delegation demo

## Requirements

- docker compose
- mkcert
- uv

## 1. Certificates

First of all you need certificates and keys to start keycloak and trinodb with https.

To do so head to [certs/README.md](certs/README.md) and follow instructions.

## 2. Keycloak

Then you will start Keycloak and configure it. Docker compose takes care of it. Just run:

```
docker compose up --build
```

This will start at https://keycloak:8443 with administrator credentials `admin/admin`.

It will also run `pyscripts/src/main.py` to setup clients, scopes and users.

Our human users will be:

- `antonio.murgia@agilelab.it` / `StrongP@ssword123` (in trino-admins group)
- `andrea.fonti@agilelab.it` / `StrongP@ssword123`

The generated client secrets for webapp and trino will be written to env files inside `.env_files` folder.
Such files will be sourced by docker-compose in appropriate containers.

## 3. TrinoDB and webapp

Next step is to start our webapp and trinodb, we need to start them after initializing keycloak
so that they can be configured with the needed client secrets to connect to keycloak.

```
docker compose up --build webapp trinodb
```

## 4. Create views

In order to test that RBAC works correctly, we need to create a view that can be accessed by any
`andrea.fonti@agilelab.it` and one that can be accessed only by trino-admins.

Access control rules are controlled by `trino/rules.json` and `trino/catalog/hive-rules.json`

> N.B. For access control based on groups to work we need to add a custom plugin (not production ready)
> that is in [keycloak-groups-plugin](./keycloak-groups-plugin) and it is packaged with the custom trino
> image that we are using see [trino/container-image/Dockerfile](trino/container-image/Dockerfile)

```
cd pyscripts
uv run src/create_view.py
```

This will open a browser where you will need to login as antonio.murgia@agilelab.it (because it's a trino-admin),
andrea fonti will not work, it will return a permission denied error.

## 5. Performing On Behalf Of

Now the cool part:

- we're going to head to http://webapp:5555
- Click on Login with Keycloak
- log in with either antonio or andrea credentials
- Then click on "Protected Route"

If we logged as antonio the 6th element of the bullet point will show a list of nations

If we logged as andrea the 6th element of the bullet point will show a permission denied error (`Query failed`)

### TODO

- [ ] Remove all verify=False