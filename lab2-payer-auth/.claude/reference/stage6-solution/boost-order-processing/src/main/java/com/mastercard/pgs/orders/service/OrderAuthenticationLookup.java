package com.mastercard.pgs.orders.service;

import com.mastercard.pgs.orders.client.PayerAuthenticationClient;
import com.mastercard.pgs.orders.client.model.PayerAuthenticationWithOrderDetails;
import java.util.Map;
import java.util.Optional;
import org.springframework.stereotype.Service;

/**
 * Looks up the payer authentication result for an order the gateway authenticated internally.
 *
 * <p>The tracing headers order processing received are carried across the hop. "No stored
 * result" is an empty Optional, not an error.
 */
@Service
public class OrderAuthenticationLookup {

    private final PayerAuthenticationClient payerAuthenticationClient;

    public OrderAuthenticationLookup(PayerAuthenticationClient payerAuthenticationClient) {
        this.payerAuthenticationClient = payerAuthenticationClient;
    }

    public Optional<PayerAuthenticationWithOrderDetails> lookup(String merchantWsapiId,
            String orderWsapiId, String authenticationTransactionWsapiId,
            Map<String, String> tracingHeaders) {

        return Optional.ofNullable(payerAuthenticationClient.retrieve(
                merchantWsapiId, orderWsapiId, authenticationTransactionWsapiId,
                tracingHeaders == null ? Map.of() : tracingHeaders));
    }
}
