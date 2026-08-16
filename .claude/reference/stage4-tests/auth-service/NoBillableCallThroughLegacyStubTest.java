package com.mastercard.pgs.auth;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.mastercard.pgs.auth.client.LegacyPassClientStub;
import com.mastercard.pgs.auth.security.CallerAuthorization;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

/**
 * The same constraint as {@code NoSecondAuthenticatePayerCallTest}, proved through the real
 * legacy stand-in rather than a mock: the stub's billable-call counter is the invoice.
 *
 * <p>This is the behaviour the lab's acceptance matrix describes — complete record: counter 0;
 * incomplete record: counter 0 once corrected, 1 on the inherited draft.
 */
@SpringBootTest
@AutoConfigureMockMvc
class NoBillableCallThroughLegacyStubTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private LegacyPassClientStub legacyPassClientStub;

    @BeforeEach
    void resetCounter() {
        legacyPassClientStub.resetCallCounter();
    }

    @Test
    void completeRecordRetrievalCostsNothing() throws Exception {
        retrieve("ORD-1001", "AUTH-9001");
        assertThat(legacyPassClientStub.authenticatePayerCallCount()).isZero();
    }

    @Test
    void incompleteRecordRetrievalAlsoCostsNothing() throws Exception {
        retrieve("ORD-1002", "AUTH-9002");
        assertThat(legacyPassClientStub.authenticatePayerCallCount())
                .as("a retrieval must never trigger a billable Authenticate Payer")
                .isZero();
    }

    private void retrieve(String orderId, String authTxnId) throws Exception {
        mockMvc.perform(get("/merchants/{m}/orders/{o}/authentications/{a}",
                        "MERCH-AU-001", orderId, authTxnId)
                        .header(CallerAuthorization.CLIENT_ID_HEADER, "boost-order-processing"))
                .andExpect(status().isOk());
    }
}
