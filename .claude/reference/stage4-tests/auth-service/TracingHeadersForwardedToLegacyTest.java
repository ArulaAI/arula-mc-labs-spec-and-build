package com.mastercard.pgs.auth;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.mastercard.pgs.auth.client.LegacyAuthenticationRecord;
import com.mastercard.pgs.auth.client.LegacyPassClient;
import com.mastercard.pgs.auth.client.LegacyRetrievalQuery;
import com.mastercard.pgs.auth.config.TracingHeaders;
import com.mastercard.pgs.auth.security.CallerAuthorization;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

/**
 * AC-8: given inbound tracing headers, when the endpoint is called, then those headers are
 * propagated across the hop to the legacy edge (not only echoed back to the caller —
 * {@code specs/NON_NEGOTIABLES.md} §4: "every inbound tracing header is propagated across the
 * hop").
 *
 * <p>{@code RetrievalMappingTest} already proves the headers are echoed back to the caller. This
 * test proves the other half: they reach {@link LegacyPassClient#retrieveAuthenticationResult}.
 */
@SpringBootTest
@AutoConfigureMockMvc
class TracingHeadersForwardedToLegacyTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private LegacyPassClient legacyPassClient;

    @Test
    void allInboundTracingHeadersReachTheLegacyRetrievalCall() throws Exception {
        when(legacyPassClient.retrieveAuthenticationResult(any(LegacyRetrievalQuery.class)))
                .thenReturn(record());

        mockMvc.perform(get("/merchants/{m}/orders/{o}/authentications/{a}",
                        "MERCH-AU-001", "ORD-1001", "AUTH-9001")
                        .header(CallerAuthorization.CLIENT_ID_HEADER, "boost-order-processing")
                        .header(TracingHeaders.CLIENT_CORRELATION_ID, "client-corr-456")
                        .header(TracingHeaders.MC_CORRELATION_ID, "corr-abc-123")
                        .header(TracingHeaders.MC_CORRELATION_REQUEST_ID, "corr-req-789")
                        .header(TracingHeaders.MC_TNS_LOGGING_ID, "tns-log-321")
                        .header(TracingHeaders.MC_TOGGLE_VERSION, "v2"))
                .andExpect(status().isOk());

        ArgumentCaptor<LegacyRetrievalQuery> captor =
                ArgumentCaptor.forClass(LegacyRetrievalQuery.class);
        verify(legacyPassClient).retrieveAuthenticationResult(captor.capture());

        assertThat(captor.getValue().tracingHeaders())
                .containsEntry(TracingHeaders.CLIENT_CORRELATION_ID, "client-corr-456")
                .containsEntry(TracingHeaders.MC_CORRELATION_ID, "corr-abc-123")
                .containsEntry(TracingHeaders.MC_CORRELATION_REQUEST_ID, "corr-req-789")
                .containsEntry(TracingHeaders.MC_TNS_LOGGING_ID, "tns-log-321")
                .containsEntry(TracingHeaders.MC_TOGGLE_VERSION, "v2");
    }

    private static LegacyAuthenticationRecord record() {
        return new LegacyAuthenticationRecord(
                "MERCH-AU-001", "ORD-1001", "AUTH-9001", "INTERNAL",
                new LegacyAuthenticationRecord.LegacyAuthBlock(
                        "EMV_3DS", "AUTHENTICATION_SUCCESSFUL", "MASTERCARD", "2.2.0",
                        "NO_CHALLENGE", "AAABBJg0VhI0VniQEjRWAAAAAAA=", "LOW_VALUE"),
                new LegacyAuthenticationRecord.LegacyOrderBlock(
                        "Mozilla/5.0", "203.0.113.24", "REF-ORD-1001",
                        "Boost Demo Merchant", "5411", "AUD", 12500L,
                        "CUST-77301", "AU", "AU",
                        "CARD", "4111111111111111", "MASTERCARD"),
                "corr-AUTH-9001");
    }
}
