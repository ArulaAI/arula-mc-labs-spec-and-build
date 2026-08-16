package com.mastercard.pgs.auth;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.mastercard.pgs.auth.config.TracingHeaders;
import com.mastercard.pgs.auth.security.CallerAuthorization;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

/**
 * AC-1 (200 with the full aggregate) and AC-TRACING (the correlation headers are propagated).
 *
 * <p>The mapping is 1:1 with the legacy field map in the compressed context — every block of
 * PayerAuthenticationWithOrderDetails is populated from the stored record.
 */
@SpringBootTest
@AutoConfigureMockMvc
class RetrievalMappingTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    void completeStoredRecordMapsOntoTheFullAggregate() throws Exception {
        mockMvc.perform(get("/merchants/{m}/orders/{o}/authentications/{a}",
                        "MERCH-AU-001", "ORD-1001", "AUTH-9001")
                        .header(CallerAuthorization.CLIENT_ID_HEADER, "boost-order-processing"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.payerAuthentication.method").value("EMV_3DS"))
                .andExpect(jsonPath("$.payerAuthentication.scheme").value("MASTERCARD"))
                .andExpect(jsonPath("$.payerAuthentication.psd2ScaExemption").value("LOW_VALUE"))
                .andExpect(jsonPath("$.legacyOrderData.browser").value("Mozilla/5.0"))
                .andExpect(jsonPath("$.legacyOrderData.referenceOrder").value("REF-ORD-1001"))
                .andExpect(jsonPath("$.merchant.merchantId").value("MERCH-AU-001"))
                .andExpect(jsonPath("$.merchant.categoryCode").value("5411"))
                .andExpect(jsonPath("$.order.orderId").value("ORD-1001"))
                .andExpect(jsonPath("$.order.currency").value("AUD"))
                .andExpect(jsonPath("$.order.amountMinor").value(12500))
                .andExpect(jsonPath("$.order.funding.method").value("CARD"))
                .andExpect(jsonPath("$.order.funding.cardBrand").value("MASTERCARD"));
    }

    @Test
    void tracingHeadersArePropagatedBackToTheCaller() throws Exception {
        mockMvc.perform(get("/merchants/{m}/orders/{o}/authentications/{a}",
                        "MERCH-AU-001", "ORD-1001", "AUTH-9001")
                        .header(CallerAuthorization.CLIENT_ID_HEADER, "boost-order-processing")
                        .header(TracingHeaders.MC_CORRELATION_ID, "corr-abc-123")
                        .header(TracingHeaders.CLIENT_CORRELATION_ID, "client-corr-456"))
                .andExpect(status().isOk())
                .andExpect(header().string(TracingHeaders.MC_CORRELATION_ID, "corr-abc-123"))
                .andExpect(header().string(TracingHeaders.CLIENT_CORRELATION_ID,
                        "client-corr-456"));
    }
}
