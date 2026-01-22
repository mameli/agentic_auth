# SSL/TLS Certificates

Certificates for HTTPS communication between services.

## Prerequisites

Install mkcert if not already installed:

```bash
# macOS
brew install mkcert

# Install the local CA (one-time setup)
mkcert -install
```

## Regenerate Certificates

```bash
cd certs

# 1. Generate PEM certificate and key for Keycloak
mkcert -cert-file servers.pem -key-file servers-key.pem keycloak trinodb localhost 127.0.0.1

# 2. Convert to PKCS12 keystore for Trino
openssl pkcs12 -export \
  -in servers.pem \
  -inkey servers-key.pem \
  -out trino-keystore.p12 \
  -name trino \
  -passout pass:changeit
```

## Files

| File                 | Format          | Used By  | Password   |
| -------------------- | --------------- | -------- | ---------- |
| `servers.pem`        | PEM certificate | Keycloak | n/a        |
| `servers-key.pem`    | PEM private key | Keycloak | n/a        |
| `trino-keystore.p12` | PKCS12 keystore | Trino    | `changeit` |

## Subject Alternative Names

The certificate includes SANs for:

- `keycloak` - Docker service hostname
- `trinodb` - Docker service hostname
- `localhost` - Local development
- `127.0.0.1` - Loopback IP
