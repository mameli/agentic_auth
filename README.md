# Keycloak + TrinoDB

I started this small PoC in the context of chat with your data project.
My aim is to prove that it is possible to create a setup as follows:

1. Users, Roles and Groups are managed by an IdP (Keycloak in the example)
1. A virtualizer/query server is used to query data in diverse sources (Trino DB in the example)
1. A user can connect to a custom web UI (accessed authenticating through IdP at 1) and can execute queries to the virtualizer (2) accessing data that is visible to the same user on the virtualizer (2)

All of this using open standards and open source products.

In order to do so I tried to setup:

1. Keycloak as the IdP because it supports both OIDC, OAuth2 and potentially federation
2. TrinoDB as the virtualizer/query server
3. A custom web app that actually is just a form that allows to send a query and shows the result

A bonus is that the request to the query server should easily show that there is a delegation/impersonation in the "middle" (i.e. it's not directly the user but it's an application acting as the user).

## Real life complexities

- TrinoDB access control is complex. Depending on how you configure it you can get Trino to decide ACL or the queried system to decide. OPA plugin probably gives you the best flexibility (I think I will try it someday), for now we will stick to the [file access control](https://trino.io/docs/current/security/file-system-access-control.html) refreshed every second.

- [Groups are not mapped/forwarded](https://trino.io/docs/current/security/group-mapping.html) when using OAuth2, only used in conjunction with LDAP. I'm thinking about building a group mapper plugin, but I should look into it a bit deeper, because the feature was there and was removed at some point (config was: `http-server.authentication.oauth2.groups-field`) the conf is marked as [deprecated](https://github.com/trinodb/trino/blob/2054443358cddda256c8706083ce08530c173f5e/core/trino-main/src/main/java/io/trino/server/security/oauth2/OAuth2Config.java#L158) see [commit](https://github.com/trinodb/trino/commit/65a8f113f92ad8a435e71adb6365db35b3975920) and [PR](https://github.com/trinodb/trino/pull/15669), so i built a [groups plugin for Trino](./keycloak-groups-plugin/)

---

1. `docker compose up -d` will start keycloak and initialize it through [initializer script](./pyscripts/src/main.py).
   1. This script will create 2 users (antonio.murgia@agilelab.it and andrea.fonti@agilelab.it, both will have password "StrongP@ssword123") and will register trinodb client.
   2. After registering trinodb client, will add a client scope and mapper so that groups are added in OIDC tokens
   3. Will modify [trino/config.properties](trino/config.properties) to set the just created client secret
2. Then you need to start trinodb `docker compose up -d trinodb`


Go to https://keycloak:8443 and login via admin/admin (do it in private browsing, otherwise the cookie will prevent you to access trino later) to access keycloak console

Go to https://trinodb:8543 and login via one of the two users to access trinodb coordinator.


