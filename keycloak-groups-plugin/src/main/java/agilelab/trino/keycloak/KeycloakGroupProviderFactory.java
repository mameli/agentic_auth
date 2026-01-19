package agilelab.trino.keycloak;

import io.trino.spi.security.GroupProvider;
import io.trino.spi.security.GroupProviderFactory;

import java.util.Map;

public class KeycloakGroupProviderFactory implements GroupProviderFactory {

    @Override
    public String getName() {
        return "keycloak";
    }

    @Override
    public GroupProvider create(Map<String, String> config) {
        if (config.isEmpty()) {
            throw new IllegalArgumentException("this group provider requires configuration properties");
        }
        return new KeycloakGroupProvider(config);
    }
}