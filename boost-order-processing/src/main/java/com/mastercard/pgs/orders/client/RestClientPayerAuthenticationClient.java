package com.mastercard.pgs.orders.client;

import com.mastercard.pgs.orders.client.model.PayerAuthenticationWithOrderDetails;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

/**
 * HTTP consumer of boost-authentication-service.
 *
 * <p>FIRST-PASS DRAFT — the tracing headers are accepted but not propagated, and a
 * "no matching record" response from the producer is not distinguished from a failure.
 */
@Component
public class RestClientPayerAuthenticationClient implements PayerAuthenticationClient {

    private static final String CLIENT_ID_HEADER = "X-Mc-Client-Id";

    private final RestClient restClient;
    private final String clientId;

    public RestClientPayerAuthenticationClient(RestClient.Builder builder,
            @Value("${pgs.orders.authentication-service.base-url}") String baseUrl,
            @Value("${pgs.orders.client-id}") String clientId) {
        this.restClient = builder.baseUrl(baseUrl).build();
        this.clientId = clientId;
    }

    @Override
    public PayerAuthenticationWithOrderDetails retrieve(String merchantWsapiId,
            String orderWsapiId, String authenticationTransactionWsapiId,
            Map<String, String> tracingHeaders) {

        // TODO(PGSE-88): propagate tracingHeaders; map a 404 from the producer to "no record"
        return restClient.get()
                .uri("/merchants/{m}/orders/{o}/authentications/{a}",
                        merchantWsapiId, orderWsapiId, authenticationTransactionWsapiId)
                .header(CLIENT_ID_HEADER, clientId)
                .retrieve()
                .body(PayerAuthenticationWithOrderDetails.class);
    }
}
