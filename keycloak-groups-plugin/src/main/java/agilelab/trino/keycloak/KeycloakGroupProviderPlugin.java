package agilelab.trino.keycloak;

import io.trino.spi.Plugin;
import io.trino.spi.security.GroupProviderFactory;

import java.util.Collections;

public final class KeycloakGroupProviderPlugin implements Plugin {

    @Override
    public Iterable<GroupProviderFactory> getGroupProviderFactories() {
        return Collections.singletonList(new KeycloakGroupProviderFactory());
    }
}