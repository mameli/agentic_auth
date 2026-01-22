# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Keycloak-delegation is an OAuth2/OpenID Connect token delegation system integrating Keycloak (identity provider) with Trino (SQL query engine). It demonstrates:
- User authentication through Keycloak using OAuth2/OIDC
- Token exchange (RFC 8693) for On-Behalf-Of (OBO) flows
- Group-based access control from Keycloak to Trino
- A FastAPI web application as intermediary for token management

## Build and Run Commands

### Docker Compose (Primary Development Method)
```bash
# Start all services
docker-compose up

# Start with manual profile (includes Trino and WebApp)
docker-compose --profile manual up
```

### Python Projects (uv package manager)
```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests

# Lint/format
uv run ruff check .
uv run ruff format .

# Run FastAPI app manually
fastapi run src/python_auth_app/main.py --host 0.0.0.0 --port 5555
```

### Java Plugin (Maven)
```bash
# Build Keycloak groups plugin
cd keycloak-groups-plugin
mvn clean package
# Output: trino-group-provider-keycloak-1.0.trino-plugin
```

## Architecture

```
User Browser
    ↓
FastAPI Web App (python_auth_app) - port 5555
    ├─ /login → Redirects to Keycloak
    ├─ /callback ← Receives auth code
    ├─ /protected → Token exchange (OBO) + Trino queries

Keycloak - port 8090/8443
    ├─ OAuth2/OIDC endpoints
    ├─ Token exchange (RFC 8693)
    └─ User/group management

Trino - port 8081/8543
    ├─ OAuth2/JWT authentication
    ├─ Keycloak Group Provider plugin
    └─ Group-based access control
```

### Key Data Flows

1. **Authentication**: User → Keycloak OAuth2 → callback with auth code → exchange for tokens
2. **Token Exchange (OBO)**: Webapp exchanges user token for Trino-specific token via `exchange_token_for_audience()`
3. **Group Access**: Custom Trino plugin queries Keycloak API for user groups

## Project Structure

- `python_auth_app/` - FastAPI web application with OAuth2 flows
- `pyscripts/` - Initialization scripts (create clients, users, groups in Keycloak)
- `keycloak-groups-plugin/` - Java Maven project for Trino group provider plugin
- `trino/` - Trino configuration (OAuth2, JWT auth, catalogs)
- `certs/` - SSL/TLS certificates
- `env_files/` - Runtime environment configuration

## Tech Stack

- **Python 3.12** with FastAPI, httpx, trino-python-client, pydantic-settings
- **Java 25** for Trino plugin (Maven)
- **Keycloak 26.5.1** - Identity provider
- **Trino 479** - SQL query engine
- **uv** - Python package manager

## Key Configuration

| File | Purpose |
|------|---------|
| `docker-compose.yaml` | Service orchestration |
| `trino/config.properties` | Trino OAuth2/JWT auth |
| `trino/group-provider.properties` | Keycloak group provider config |
| `python_auth_app/src/python_auth_app/app_settings.py` | FastAPI app settings |
| `pyscripts/src/constants.py` | Initialization constants |

## Test Users

Created by initializer container:
- `antonio.murgia@agilelab.it` / `StrongP@ssword123` (in trino-admins group)
- `andrea.fonti@agilelab.it` / `StrongP@ssword123`
