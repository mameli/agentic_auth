FROM maven:3.9-eclipse-temurin-25 AS builder
RUN mkdir /builder
WORKDIR /builder/
COPY pom.xml .
COPY src src
RUN mvn clean package

FROM trinodb/trino:479

COPY --from=builder /builder/target/trino-group-provider-keycloak-1.0 /usr/lib/trino/plugin/trino-group-provider-keycloak-1.0

RUN mkdir -p /tmp/trino-metastore
