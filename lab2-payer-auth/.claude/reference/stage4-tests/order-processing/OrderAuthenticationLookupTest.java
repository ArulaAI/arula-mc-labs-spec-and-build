package com.mastercard.pgs.orders;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import com.mastercard.pgs.orders.client.PayerAuthenticationClient;
import com.mastercard.pgs.orders.client.model.PayerAuthentication;
import com.mastercard.pgs.orders.client.model.PayerAuthenticationWithOrderDetails;
import java.util.Map;
import java.util.Optional;
import org.junit.jupiter.api.Test;

/**
 * Consumer wiring: the tracing headers order processing received are carried across the hop,
 * and "no stored result" is an empty Optional rather than an error.
 */
class OrderAuthenticationLookupTest {

    private static final Map<String, String> TRACING = Map.of(
            "X-Mc-Correlation-Id", "corr-abc-123",
            "X-Client-Correlation-Id", "client-corr-456");

    private final PayerAuthenticationClient client = mock(PayerAuthenticationClient.class);
    private final com.mastercard.pgs.orders.service.OrderAuthenticationLookup lookup =
            new com.mastercard.pgs.orders.service.OrderAuthenticationLookup(client);

    @Test
    void tracingHeadersArePropagatedToTheAuthenticationService() {
        when(client.retrieve(eq("MERCH-AU-001"), eq("ORD-1001"), eq("AUTH-9001"), eq(TRACING)))
                .thenReturn(result());

        Optional<PayerAuthenticationWithOrderDetails> found =
                lookup.lookup("MERCH-AU-001", "ORD-1001", "AUTH-9001", TRACING);

        assertThat(found).isPresent();
    }

    @Test
    void noStoredResultIsAnEmptyOptional() {
        when(client.retrieve(eq("MERCH-AU-001"), eq("ORD-9999"), eq("AUTH-9999"), eq(TRACING)))
                .thenReturn(null);

        assertThat(lookup.lookup("MERCH-AU-001", "ORD-9999", "AUTH-9999", TRACING)).isEmpty();
    }

    private static PayerAuthenticationWithOrderDetails result() {
        return new PayerAuthenticationWithOrderDetails(
                new PayerAuthentication("EMV_3DS", "AUTHENTICATION_SUCCESSFUL", "MASTERCARD",
                        "2.2.0", "NO_CHALLENGE", null, "LOW_VALUE"),
                null, null, null);
    }
}
