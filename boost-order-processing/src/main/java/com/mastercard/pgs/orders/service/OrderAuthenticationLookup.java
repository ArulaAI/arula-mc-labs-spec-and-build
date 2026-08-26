package com.mastercard.pgs.orders.service;

import com.mastercard.pgs.orders.client.PayerAuthenticationClient;
import com.mastercard.pgs.orders.client.model.PayerAuthenticationWithOrderDetails;
import java.util.Map;
import java.util.Optional;
import org.springframework.stereotype.Service;

/**
 * Looks up the payer authentication result for an order that the gateway authenticated
 * internally.
 *
 * <p>FIRST-PASS DRAFT — the tracing headers received by order processing are not yet carried
 * across the hop, and "no stored result" is not yet distinguished from "the call failed".
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

        // TODO(PGSE-88): pass the tracing headers through; treat "no matching record" as empty
        return Optional.ofNullable(payerAuthenticationClient.retrieve(
                merchantWsapiId, orderWsapiId, authenticationTransactionWsapiId, Map.of()));
    }
}
