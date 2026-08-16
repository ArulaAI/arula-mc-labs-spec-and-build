package com.mastercard.pgs.auth;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.mastercard.pgs.auth.security.CallerAuthorization;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

/**
 * AC-NOT-FOUND / AC-FORBIDDEN / AC-BAD-REQUEST / AC-OUT-OF-SCOPE.
 *
 * <p>404, 403 and 400 mean distinct things, and an externally authenticated transaction is not
 * served as if it were internally authenticated.
 */
@SpringBootTest
@AutoConfigureMockMvc
class ErrorSemanticsAndScopeTest {

    private static final String AUTHORIZED_CLIENT = "boost-order-processing";

    @Autowired
    private MockMvc mockMvc;

    @Test
    void missingRecordReturns404NotAnEmpty200() throws Exception {
        mockMvc.perform(get("/merchants/{m}/orders/{o}/authentications/{a}",
                        "MERCH-AU-001", "ORD-9999", "AUTH-9999")
                        .header(CallerAuthorization.CLIENT_ID_HEADER, AUTHORIZED_CLIENT))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.reasonCode").value("NOT_FOUND"));
    }

    @Test
    void unauthorizedCallerReturns403AndNoData() throws Exception {
        mockMvc.perform(get("/merchants/{m}/orders/{o}/authentications/{a}",
                        "MERCH-AU-001", "ORD-1001", "AUTH-9001")
                        .header(CallerAuthorization.CLIENT_ID_HEADER, "some-other-service"))
                .andExpect(status().isForbidden())
                .andExpect(jsonPath("$.payerAuthentication").doesNotExist());
    }

    @Test
    void callerWithNoClientIdReturns403() throws Exception {
        mockMvc.perform(get("/merchants/{m}/orders/{o}/authentications/{a}",
                        "MERCH-AU-001", "ORD-1001", "AUTH-9001"))
                .andExpect(status().isForbidden());
    }

    @Test
    void malformedIdentifierReturns400() throws Exception {
        mockMvc.perform(get("/merchants/{m}/orders/{o}/authentications/{a}",
                        "MERCH-AU-001", "ORD-1001", "AUTH 9001!")
                        .header(CallerAuthorization.CLIENT_ID_HEADER, AUTHORIZED_CLIENT))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.reasonCode").value("INVALID_REQUEST"));
    }

    @Test
    void externallyAuthenticatedTransactionIsNotServed() throws Exception {
        mockMvc.perform(get("/merchants/{m}/orders/{o}/authentications/{a}",
                        "MERCH-AU-001", "ORD-1003", "AUTH-9003")
                        .header(CallerAuthorization.CLIENT_ID_HEADER, AUTHORIZED_CLIENT))
                .andExpect(status().isNotFound());
    }
}
