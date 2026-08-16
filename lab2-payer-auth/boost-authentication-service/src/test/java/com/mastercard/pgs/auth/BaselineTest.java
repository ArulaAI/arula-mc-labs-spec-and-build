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
 * Baseline: the application context loads and the drafted happy path — retrieval of a
 * complete stored record — returns 200 with the mapped authentication block.
 */
@SpringBootTest
@AutoConfigureMockMvc
class BaselineTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void contextLoadsAndCompleteRecordRetrievalReturns200() throws Exception {
        mockMvc.perform(get("/merchants/{m}/orders/{o}/authentications/{a}",
                        "MERCH-AU-001", "ORD-1001", "AUTH-9001")
                        .header(CallerAuthorization.CLIENT_ID_HEADER, "boost-order-processing"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.payerAuthentication.method").value("EMV_3DS"))
                .andExpect(jsonPath("$.payerAuthentication.status")
                        .value("AUTHENTICATION_SUCCESSFUL"))
                .andExpect(jsonPath("$.payerAuthentication.protocolVersion").value("2.2.0"));
    }
}
