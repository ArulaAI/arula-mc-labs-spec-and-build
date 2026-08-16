package com.mastercard.pgs.auth;

import static org.hamcrest.Matchers.nullValue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.mastercard.pgs.auth.client.AuthenticatePayerCommand;
import com.mastercard.pgs.auth.client.LegacyAuthenticationRecord;
import com.mastercard.pgs.auth.client.LegacyPassClient;
import com.mastercard.pgs.auth.client.LegacyRetrievalQuery;
import com.mastercard.pgs.auth.security.CallerAuthorization;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

/**
 * AC-INCOMPLETE: given a stored authentication result missing an optional field, when retrieval
 * is called, then the service returns the stored result as-is (mapping the gap through) and the
 * legacy Authenticate Payer operation is never invoked.
 *
 * <p>Authenticate Payer is billable. The mock below makes it *succeed*, exactly like the real
 * legacy edge — so if the implementation calls it, nothing fails, nothing looks wrong, and the
 * only trace is this assertion.
 */
@SpringBootTest
@AutoConfigureMockMvc
class NoSecondAuthenticatePayerCallTest {

    private static final String STORED_CAVV = "AAABBJg0VhI0VniQEjRWAAAAAAA=";
    private static final String REFRESHED_CAVV = "AAABCZg1WhJ1WniREjVXAAAAAAA=";

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private LegacyPassClient legacyPassClient;

    @Test
    void incompleteStoredRecordIsReturnedAsIsAndAuthenticatePayerIsNeverInvoked()
            throws Exception {

        when(legacyPassClient.retrieveAuthenticationResult(any(LegacyRetrievalQuery.class)))
                .thenReturn(record(null));
        when(legacyPassClient.authenticatePayer(any(AuthenticatePayerCommand.class)))
                .thenReturn(record(REFRESHED_CAVV));

        mockMvc.perform(get("/merchants/{m}/orders/{o}/authentications/{a}",
                        "MERCH-AU-001", "ORD-1002", "AUTH-9002")
                        .header(CallerAuthorization.CLIENT_ID_HEADER, "boost-order-processing"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.payerAuthentication.status")
                        .value("AUTHENTICATION_SUCCESSFUL"))
                .andExpect(jsonPath("$.payerAuthentication.authenticationValue")
                        .value(nullValue()));

        verify(legacyPassClient, never()).authenticatePayer(any());
    }

    @Test
    void completeStoredRecordAlsoNeverTriggersAuthenticatePayer() throws Exception {
        when(legacyPassClient.retrieveAuthenticationResult(any(LegacyRetrievalQuery.class)))
                .thenReturn(record(STORED_CAVV));

        mockMvc.perform(get("/merchants/{m}/orders/{o}/authentications/{a}",
                        "MERCH-AU-001", "ORD-1001", "AUTH-9001")
                        .header(CallerAuthorization.CLIENT_ID_HEADER, "boost-order-processing"))
                .andExpect(status().isOk());

        verify(legacyPassClient, never()).authenticatePayer(any());
    }

    private static LegacyAuthenticationRecord record(String cavv) {
        return new LegacyAuthenticationRecord(
                "MERCH-AU-001", "ORD-1002", "AUTH-9002", "INTERNAL",
                new LegacyAuthenticationRecord.LegacyAuthBlock(
                        "EMV_3DS", "AUTHENTICATION_SUCCESSFUL", "MASTERCARD", "2.2.0",
                        "NO_CHALLENGE", cavv, "LOW_VALUE"),
                new LegacyAuthenticationRecord.LegacyOrderBlock(
                        "Mozilla/5.0", "203.0.113.24", "REF-ORD-1002",
                        "Boost Demo Merchant", "5411", "AUD", 12500L,
                        "CUST-77301", "AU", "AU",
                        "CARD", "4111111111111111", "MASTERCARD"),
                "corr-AUTH-9002");
    }
}
