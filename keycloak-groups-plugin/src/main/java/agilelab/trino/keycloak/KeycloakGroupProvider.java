package agilelab.trino.keycloak;

import io.airlift.log.Logger;
import io.trino.plugin.base.ssl.SslUtils;
import io.trino.spi.security.GroupProvider;

import java.io.File;
import java.io.IOException;
import java.security.GeneralSecurityException;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;

import org.keycloak.OAuth2Constants;
import org.keycloak.admin.client.Keycloak;
import org.keycloak.admin.client.KeycloakBuilder;
import org.keycloak.admin.client.spi.ResteasyClientClassicProvider;
import org.keycloak.representations.idm.AbstractUserRepresentation;
import org.keycloak.representations.idm.GroupRepresentation;
import org.keycloak.representations.idm.UserRepresentation;

import javax.net.ssl.SSLContext;


public class KeycloakGroupProvider implements GroupProvider {
    private static final Logger log = Logger.get(KeycloakGroupProvider.class);
    //    private final KeycloakAdminClient client; // Your wrapper for the Admin API
    private final String url;
    private final String clientId;
    private final String clientSecret;
    private final String realm;
    private final String keystorePath;
    private final String keystorePassword;
    private final String truststorePath;
    private final String truststorePassword;
    private final Optional<SSLContext> sslContext;
    private final Keycloak client;

    KeycloakGroupProvider(Map<String, String> config) {
        this.url = config.get("keycloak.url");
        this.clientId = config.get("keycloak.client-id");
        this.clientSecret = config.get("keycloak.client-secret");
        this.realm = config.get("keycloak.realm");
        this.keystorePath = config.getOrDefault("keycloak.keystore.path", null);
        this.keystorePassword = config.getOrDefault("keycloak.keystore.key", null);
        this.truststorePath = config.getOrDefault("keycloak.trust-store-path", null);
        this.truststorePassword = config.getOrDefault("keycloak.trust-store-password", null);
        File keystoreFile;
        if (keystorePath != null) {
            keystoreFile = new File(keystorePath);
        } else {
            keystoreFile = null;
        }
        File truststoreFile;
        if (truststorePath != null) {
            truststoreFile = new File(truststorePath);
        } else {
            truststoreFile = null;
        }

        this.sslContext = createSslContext(
                Optional.ofNullable(keystoreFile),
                Optional.ofNullable(keystorePassword),
                Optional.ofNullable(truststoreFile),
                Optional.ofNullable(truststorePassword)
        );
        ClassLoader oldClassLoader = Thread.currentThread().getContextClassLoader();
        try {
            this.client = KeycloakBuilder.builder()
                    .serverUrl(this.url)
                    .realm(this.realm)
                    .clientId(this.clientId)
                    .clientSecret(this.clientSecret)
                    .grantType(OAuth2Constants.CLIENT_CREDENTIALS)
                    .resteasyClient(
                            new ResteasyClientClassicProvider()
                                    .newRestEasyClient(null, sslContext.orElse(null), false)
                    )
                    .build();
        } finally {
            Thread.currentThread().setContextClassLoader(oldClassLoader);
        }
        log.info("Initialized %s as %s", this.getClass(), this.toString());
    }

    @Override
    public String toString() {
        return "KeycloakGroupProvider{" +
                "url='" + url + '\'' +
                ", clientId='" + clientId + '\'' +
                ", clientSecret='" + clientSecret + '\'' +
                ", realm='" + realm + '\'' +
                ", keystorePath='" + keystorePath + '\'' +
                ", keystorePassword='" + keystorePassword + '\'' +
                ", truststorePath='" + truststorePath + '\'' +
                ", truststorePassword='" + truststorePassword + '\'' +
                ", sslContext=" + sslContext +
                ", client=" + client +
                '}';
    }

    @Override
    public Set<String> getGroups(String user) {
        ClassLoader oldClassLoader = Thread.currentThread().getContextClassLoader();
        Thread.currentThread().setContextClassLoader(getClass().getClassLoader());
        try {
            log.info("Getting groups for user: %s", user);
            List<UserRepresentation> users = client.realm(this.realm).users().searchByEmail(user, true);
            log.info("Found the following users: %s", String.join("\n", users.stream().map(AbstractUserRepresentation::getUsername).toList()));
            UserRepresentation keycloakUser = users.getFirst();
            List<GroupRepresentation> groups = client.realm(this.realm)
                    .users()
                    .get(keycloakUser.getId()) // Targets /users/{id}
                    .groups();
            Set<String> groupNames = groups.stream().map(GroupRepresentation::getName).collect(Collectors.toSet());
            log.info("User %s is part of the following groups\n\t%s", keycloakUser.getUsername(), String.join("\n\t", groupNames));
            return groupNames;
        } finally {
            Thread.currentThread().setContextClassLoader(oldClassLoader);
        }
        // 1. Get User UUID by username

    }

    private static Optional<SSLContext> createSslContext(Optional<File> keyStorePath, Optional<String> keyStorePassword, Optional<File> trustStorePath, Optional<String> trustStorePassword) {
        if (keyStorePath.isEmpty() && trustStorePath.isEmpty()) {
            return Optional.empty();
        } else {
            try {
                return Optional.of(SslUtils.createSSLContext(keyStorePath, keyStorePassword, trustStorePath, trustStorePassword));
            } catch (IOException | GeneralSecurityException var5) {
                throw new RuntimeException(var5);
            }
        }
    }
}