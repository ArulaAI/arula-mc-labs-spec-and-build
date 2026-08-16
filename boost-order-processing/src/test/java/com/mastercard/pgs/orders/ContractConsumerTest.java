package com.mastercard.pgs.orders;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.mastercard.pgs.orders.client.model.LegacyOrderData;
import com.mastercard.pgs.orders.client.model.Merchant;
import com.mastercard.pgs.orders.client.model.OrderDetails;
import com.mastercard.pgs.orders.client.model.OrderFunding;
import com.mastercard.pgs.orders.client.model.PayerAuthentication;
import com.mastercard.pgs.orders.client.model.PayerAuthenticationWithOrderDetails;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.junit.jupiter.api.Test;
import org.yaml.snakeyaml.Yaml;

/**
 * Cross-repo contract test.
 *
 * <p>The producer ({@code boost-authentication-service}) and this consumer share one contract
 * file, {@code openapi/payer-authentication-v1.yaml}. This test fails if the producer's copy
 * drifts from ours, if the contract drifts from the DTOs we deserialize into, or if a response
 * shaped like the contract no longer binds to those DTOs.
 *
 * <p>No live HTTP: the producer's shape is checked through the shared contract and a canned
 * response, not by starting either service.
 */
class ContractConsumerTest {

    private static final Path CONSUMER_CONTRACT =
            Path.of("src/main/resources/openapi/payer-authentication-v1.yaml");
    private static final Path PRODUCER_CONTRACT = Path.of("..", "boost-authentication-service",
            "src", "main", "resources", "openapi", "payer-authentication-v1.yaml");

    @Test
    void producerAndConsumerHoldTheSameContract() throws Exception {
        assumeTrue(Files.exists(PRODUCER_CONTRACT),
                "producer repo not present in this workspace — cross-repo check skipped");
        assertThat(Files.readString(CONSUMER_CONTRACT))
                .as("the shared contract must be identical in both repos")
                .isEqualTo(Files.readString(PRODUCER_CONTRACT));
    }

    @Test
    void consumerDtosMatchTheContractSchemas() throws Exception {
        Map<String, Object> schemas = schemas();

        assertThat(propertiesOf(schemas, "PayerAuthenticationWithOrderDetails"))
                .isEqualTo(componentsOf(PayerAuthenticationWithOrderDetails.class));
        assertThat(propertiesOf(schemas, "PayerAuthentication"))
                .isEqualTo(componentsOf(PayerAuthentication.class));
        assertThat(propertiesOf(schemas, "LegacyOrderData"))
                .isEqualTo(componentsOf(LegacyOrderData.class));
        assertThat(propertiesOf(schemas, "Merchant"))
                .isEqualTo(componentsOf(Merchant.class));
        assertThat(propertiesOf(schemas, "OrderDetails"))
                .isEqualTo(componentsOf(OrderDetails.class));
        assertThat(propertiesOf(schemas, "OrderFunding"))
                .isEqualTo(componentsOf(OrderFunding.class));
    }

    @Test
    void cannedProducerResponseDeserializesStrictly() throws Exception {
        ObjectMapper mapper = new ObjectMapper()
                .enable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES);

        PayerAuthenticationWithOrderDetails response;
        try (InputStream json = getClass()
                .getResourceAsStream("/canned/payer-authentication-200.json")) {
            response = mapper.readValue(json, PayerAuthenticationWithOrderDetails.class);
        }

        assertThat(response.payerAuthentication().method()).isEqualTo("EMV_3DS");
        assertThat(response.payerAuthentication().protocolVersion()).isEqualTo("2.2.0");
        assertThat(response.merchant().merchantId()).isEqualTo("MERCH-AU-001");
        assertThat(response.legacyOrderData().referenceOrder()).isEqualTo("REF-ORD-1001");
        assertThat(response.order().currency()).isEqualTo("AUD");
        assertThat(response.order().funding().cardBrand()).isEqualTo("MASTERCARD");
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> schemas() throws Exception {
        Map<String, Object> contract = new Yaml().load(Files.readString(CONSUMER_CONTRACT));
        Map<String, Object> components = (Map<String, Object>) contract.get("components");
        return (Map<String, Object>) components.get("schemas");
    }

    @SuppressWarnings("unchecked")
    private static Set<String> propertiesOf(Map<String, Object> schemas, String schemaName) {
        Map<String, Object> schema = (Map<String, Object>) schemas.get(schemaName);
        Map<String, Object> properties = (Map<String, Object>) schema.get("properties");
        return new LinkedHashSet<>(properties.keySet());
    }

    private static Set<String> componentsOf(Class<?> recordClass) {
        return Arrays.stream(recordClass.getRecordComponents())
                .map(java.lang.reflect.RecordComponent::getName)
                .collect(Collectors.toCollection(LinkedHashSet::new));
    }
}
