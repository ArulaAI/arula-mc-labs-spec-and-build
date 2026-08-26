package com.mastercard.pgs.orders.client;

import com.mastercard.pgs.orders.client.model.PayerAuthenticationWithOrderDetails;
import java.util.Map;

/**
 * Consumer of the Retrieve Payer Authentication Results contract
 * ({@code src/main/resources/openapi/payer-authentication-v1.yaml}).
 */
public interface PayerAuthenticationClient {

    /**
     * Retrieve the stored payer authentication result for an order.
     *
     * @param tracingHeaders inbound tracing headers to propagate across the hop
     * @return the retrieved result, or {@code null} when the producer reports no matching record
     */
    PayerAuthenticationWithOrderDetails retrieve(String merchantWsapiId, String orderWsapiId,
            String authenticationTransactionWsapiId, Map<String, String> tracingHeaders);
}
