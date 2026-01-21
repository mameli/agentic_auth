# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This repository is a Proof of Concept (PoC) demonstrating integration between Keycloak (Identity Provider), TrinoDB (query engine), and a custom web application. The setup shows how users can authenticate via Keycloak and access TrinoDB with proper delegation/impersonation using OAuth2 Token Exchange (RFC 8693) and JWT tokens.

**Key Design Choice:** All components use **email as the principal identifier** (not username). This is enforced across TrinoDB authentication config, JWT validation, Keycloak group mapping, and access control rules.

## Architecture

The system consists of four main components:

1. **Keycloak** - Identity Provider managing users, roles, and groups
   - Version: 26.5.1
   - Manages authentication and authorization
   - Provides OIDC/OAuth2 endpoints
   - Hosted at https://keycloak:8443

2. **TrinoDB** - Distributed SQL query engine
   - Version: 479
   - Configured with OAuth2/JWT authentication against Keycloak
   - Uses a custom Keycloak Groups Plugin for group mapping
   - Hosted at https://trinodb:8543
   - Access control via file-based permissions (refreshes every second)

3. **Python Initializer** - Bootstrap script
   - Creates users in Keycloak
   - Registers OAuth2 clients for TrinoDB and the web app
   - Configures client secrets in TrinoDB and web app configs
   - Runs on container startup

4. **Python Web Application** - Custom UI
   - FastAPI-based web application
   - Implements OAuth2 authentication flow
   - Uses Token Exchange (RFC 8693) to delegate access to TrinoDB
   - Hosted at http://webapp:5555

## Key Features & Architecture Patterns

### OAuth2 Token Exchange (RFC 8693)
The web application implements the "on-behalf-of" token exchange flow:
1. User authenticates with Keycloak via web app (OAuth2 authorization code flow)
2. Web app receives user's access token
3. Web app exchanges user token for a **new token with `audience=trinodb`**
4. Web app uses the exchanged token to authenticate to TrinoDB as the user
5. TrinoDB validates JWT and enforces access control based on user groups

**Critical scope requirement:** The web app must request `scope-token-exchange` during initial login. This scope includes a protocol mapper that adds `trinodb` as the token audience.

### Custom Keycloak Groups Plugin
**Why it exists:** TrinoDB doesn't forward OAuth2 groups automatically (this feature was deprecated). The custom plugin:
1. Implements TrinoDB's `GroupProvider` SPI interface
2. Uses Keycloak Admin API to fetch user groups by email
3. Requires a service account with `view-users` role (auto-configured by initializer)
4. Returns groups to TrinoDB for file-based access control evaluation

**Plugin location:** `keycloak-groups-plugin/` (Java Maven project, packaged into TrinoDB Docker image)

### Configuration Management Strategy
Configuration flows through three layers:

1. **Static files (git-committed):** `trino/config.properties` with placeholders like `${ENV:OAUTH2_CLIENT_SECRET}`
2. **Generated env files:** Initializer writes `env_files/trino.env` and `env_files/webapp.env` with secrets
3. **Runtime substitution:** Services read environment variables at startup

**Secret synchronization:** The initializer generates OAuth2 client secrets in Keycloak and writes them to env files. If secrets get out of sync, OAuth2 will fail with 401 errors.

### End-to-End TLS
- Keycloak uses custom certificates: `certs/servers.pem` and `certs/servers-key.pem`
- TrinoDB uses Java keystore: `certs/trino-keystore.p12` (password: `changeit`)
- **Development mode:** All Python clients use `verify=False` to skip certificate validation

### File-based Access Control
- TrinoDB permissions defined in `trino/access-control.properties`
- **Refresh period:** 1 second (aggressive, for development)
- Group names in rules must match Keycloak group names exactly
- Example: `trino-admins` group created by initializer

## Common Development Commands

### Starting the System

**IMPORTANT:** TrinoDB and webapp use Docker Compose profiles (`manual`), so they won't start with `docker compose up -d` alone.

```bash
# Full startup sequence:
docker compose up -d              # Starts Keycloak and initializer
# Wait for initializer to complete (check logs: docker compose logs initializer)
docker compose up -d trinodb      # Start TrinoDB with generated secrets
docker compose up -d webapp       # Start web application

# Or start everything at once:
docker compose --profile manual up -d
```

**Why this design?** The initializer must run first to generate OAuth2 client secrets and write them to `env_files/trino.env` and `env_files/webapp.env`. TrinoDB cannot start without a valid `OAUTH2_CLIENT_SECRET`.

### Building Components

**Keycloak Groups Plugin (Java):**
```bash
cd keycloak-groups-plugin
mvn clean package  # Creates target/trino-group-provider-keycloak-1.0.jar
# Or rebuild Docker image:
docker compose build trinodb
```

**Python Initializer:**
```bash
cd pyscripts
uv sync              # Install dependencies from uv.lock
python src/main.py   # Run manually (requires Keycloak running)
# Or rebuild:
docker compose build initializer
docker compose up initializer  # Run one-shot
```

**Web Application:**
```bash
cd python_auth_app
uv sync              # Install dependencies from uv.lock
uv run fastapi run src/python_auth_app/main.py --port 5555
# Or rebuild:
docker compose build webapp
docker compose up -d webapp
```

### Development Iteration

```bash
# Rebuild single service after code changes:
docker compose build <service-name>
docker compose up -d <service-name>

# Full teardown and rebuild:
docker compose down
docker compose build
docker compose --profile manual up -d

# View logs:
docker compose logs -f <service-name>
```

### Development Workflow

**Standard startup sequence:**
1. Start Keycloak: `docker compose up -d keycloak` (or just `docker compose up -d` since it has no profile)
2. Wait for Keycloak to be ready: `docker compose logs -f keycloak` (look for "Listening on:")
3. Run initializer: `docker compose up initializer` (one-shot, creates users/clients/secrets)
4. Start TrinoDB: `docker compose up -d trinodb` (requires secrets from step 3)
5. Start web app: `docker compose up -d webapp` (requires Keycloak and secrets from step 3)

**Development iteration (changing Python/Java code):**
```bash
# After modifying initializer:
docker compose build initializer
docker compose up initializer

# After modifying TrinoDB plugin:
cd keycloak-groups-plugin && mvn clean package && cd ..
docker compose build trinodb
docker compose restart trinodb

# After modifying web app:
docker compose build webapp
docker compose restart webapp
```

### Accessing Services

- **Keycloak Admin Console**: https://localhost:8443 (admin/admin)
- **TrinoDB UI**: https://localhost:8543
- **Web App**: http://localhost:5555

## Configuration Files

### Keycloak Configuration
- Created automatically by initializer script
- Users: antonio.murgia@agilelab.it and andrea.fonti@agilelab.it (password: StrongP@ssword123)
- Client: trinodb (public client for TrinoDB authentication)

### TrinoDB Configuration
- **config.properties**: Main TrinoDB configuration
  - OAuth2 issuer: https://keycloak:8443/realms/master
  - Client ID: trinodb
  - TLS keystore: /certs/trino-keystore.p12
  - JWT authentication with email as principal field

- **group-provider.properties**: Keycloak groups plugin configuration
  - Connects to Keycloak for group mapping
  - Requires client secret (set by initializer)

- **access-control.properties**: File-based access control rules
- **catalog/**: Catalog definitions for various data sources

### Web Application Configuration
- **.env file**: Contains OAuth2 client credentials
  - client_id, client_secret, oidc_url, realm
  - Generated by initializer script

## Important Implementation Details

### Service Dependencies & Startup Order
```
Keycloak (no dependencies)
   ↓
Initializer (waits for Keycloak, creates users/clients/secrets)
   ↓
   ├→ TrinoDB (requires env_files/trino.env with OAUTH2_CLIENT_SECRET)
   └→ Webapp (requires env_files/webapp.env with client_secret)
```

**Timing considerations:**
- Initializer has built-in retry loops (5-second intervals) for Keycloak API calls
- TrinoDB will fail to start if `OAUTH2_CLIENT_SECRET` is missing or invalid
- Webapp will fail authentication if `client_secret` doesn't match Keycloak

### Email as Principal Identifier
All components are configured to use email addresses (not usernames) as the principal:
- **TrinoDB config:** `http-server.authentication.oauth2.principal-field=email`
- **JWT validation:** `http-server.authentication.jwt.principal-field=email`
- **Keycloak plugin:** Searches users by email via `searchByEmail()`
- **Access control rules:** Principals are email addresses

Test users: `antonio.murgia@agilelab.it` and `andrea.fonti@agilelab.it` (both password: `StrongP@ssword123`)

### Docker Compose Build Context Quirk
The TrinoDB service has an unusual build configuration:
```yaml
build:
  context: ./keycloak-groups-plugin
  dockerfile: ../trino/container-image/Dockerfile
```
This means the Dockerfile is in `trino/container-image/` but the build context is `keycloak-groups-plugin/`. This allows the Dockerfile to copy the compiled JAR from the Maven target directory.

### Certificate Management
- Certificates stored in ./certs directory
- servers.pem: TLS certificate for Keycloak
- servers-key.pem: TLS private key for Keycloak
- trino-keystore.p12: Keystore for TrinoDB
- Mounted into all containers

### Secret Management & Troubleshooting

**How secrets are managed:**
1. Initializer calls `keycloak_admin.generate_client_secrets(client_id)` for both `trinodb` and `pythonapp` clients
2. Secrets are written to `env_files/trino.env` and `env_files/webapp.env`
3. Services load secrets via Docker Compose `env_file` directive
4. TrinoDB substitutes `${ENV:OAUTH2_CLIENT_SECRET}` at startup

**Common issue: Secret mismatch**
If OAuth2 fails with 401 errors, check if secrets are synchronized:
```bash
# View generated secrets:
cat env_files/trino.env
cat env_files/webapp.env

# Compare with Keycloak (requires jq):
docker compose exec keycloak /opt/keycloak/bin/kcadm.sh config credentials \
  --server https://localhost:8443 --realm master --user admin --password admin
docker compose exec keycloak /opt/keycloak/bin/kcadm.sh get clients/<client-uuid>/client-secret

# Fix: Re-run initializer to regenerate and sync secrets:
docker compose up initializer
docker compose restart trinodb webapp
```

## Development Notes & Gotchas

- **Initializer retries:** All Keycloak API calls have 5-second retry loops with exception logging
- **Internal networking:** Services communicate via Docker service names (`keycloak:8443`, `trinodb:8543`, `webapp:5555`)
- **TLS verification disabled:** All Python clients use `verify=False` (development only!)
- **Access control refresh:** TrinoDB reloads rules every 1 second (configured for fast iteration)
- **Catalog management:** Can be environment-driven via `CATALOG_MANAGEMENT` property
- **Session management:** Web app uses Starlette SessionMiddleware with hardcoded secret key
- **Token storage:** User access tokens stored in server-side sessions, not cookies
- **uv package manager:** Both Python projects use `uv.lock` for reproducible builds
- **Java version:** Plugin targets Java 25 (ensure Docker base image matches)
- **Port conflicts:** Keycloak maps 8090→8080 (HTTP) and 8443→8443 (HTTPS), TrinoDB maps 8081→8080 and 8543→8543

## File Structure

```
/
├── certs/                          # TLS certificates (must be pre-generated)
│   ├── servers.pem                 # Keycloak TLS certificate
│   ├── servers-key.pem             # Keycloak TLS private key
│   └── trino-keystore.p12          # TrinoDB Java keystore (password: changeit)
├── keycloak-groups-plugin/         # Java plugin for TrinoDB group mapping
│   ├── pom.xml                     # Maven build configuration
│   ├── src/main/java/              # Java source code (implements GroupProvider SPI)
│   └── src/main/resources/         # Plugin configuration templates
├── pyscripts/                      # Python initializer (one-shot bootstrap)
│   ├── src/
│   │   ├── main.py                 # Entry point (orchestrates user/client creation)
│   │   ├── create_user.py          # Creates test users and trino-admins group
│   │   ├── create_client.py        # Creates trinodb and pythonapp OAuth2 clients
│   │   └── constants.py            # Shared configuration (URLs, client IDs, realm)
│   ├── pyproject.toml              # uv dependencies
│   ├── uv.lock                     # Locked dependency versions
│   └── Dockerfile                  # Two-stage build (uv + slim runtime)
├── python_auth_app/                # FastAPI web application
│   ├── src/python_auth_app/
│   │   ├── main.py                 # OAuth2 routes + token exchange logic
│   │   └── app_settings.py         # Pydantic settings (loads from .env)
│   ├── templates/                  # Jinja2 HTML templates
│   ├── pyproject.toml              # uv dependencies
│   ├── uv.lock                     # Locked dependency versions
│   └── Dockerfile                  # Two-stage build (uv + slim runtime)
├── trino/                          # TrinoDB configuration
│   ├── config.properties           # Main config (OAuth2 issuer, JWT validation)
│   ├── group-provider.properties   # Keycloak Groups Plugin config
│   ├── access-control.properties   # File-based access control rules
│   ├── catalog/                    # Catalog definitions (data sources)
│   └── container-image/Dockerfile  # Custom TrinoDB image with plugin
├── env_files/                      # Generated by initializer (not in git)
│   ├── trino.env                   # OAUTH2_CLIENT_SECRET
│   └── webapp.env                  # client_id, client_secret, oidc_url, realm
├── docker-compose.yaml             # Multi-service orchestration
├── README.md                       # Original project overview
└── CLAUDE.md                       # This file (Claude Code guidance)
```

**Generated files (not committed):**
- `env_files/trino.env` - Generated by initializer with TrinoDB client secret
- `env_files/webapp.env` - Generated by initializer with web app credentials
- `keycloak-groups-plugin/target/` - Maven build artifacts
