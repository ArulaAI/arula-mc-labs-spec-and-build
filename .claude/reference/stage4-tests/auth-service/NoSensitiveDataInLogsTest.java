package com.mastercard.pgs.auth;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.mastercard.pgs.auth.security.CallerAuthorization;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

/**
 * AC-2: given a successful retrieval, when the response is processed, then no authentication
 * value, PAN or PII is written to any log.
 *
 * <p>The log sink is {@code logs/auth-service.log} (see {@code log4j2.xml}).
 */
@SpringBootTest
@AutoConfigureMockMvc
class NoSensitiveDataInLogsTest {

    private static final Path LOG_SINK = Path.of("logs", "auth-service.log");
    private static final Pattern PAN = Pattern.compile(
            "\\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}"
                    + "|6(?:011|5[0-9]{2})[0-9]{12})\\b");
    private static final String STORED_CAVV = "AAABBJg0VhI0VniQEjRWAAAAAAA=";
    private static final String CUSTOMER_REFERENCE = "CUST-77301";

    @Autowired
    private MockMvc mockMvc;

    @Test
    void retrievalWritesNoAuthenticationValuePanOrPiiToTheLog() throws Exception {
        mockMvc.perform(get("/merchants/{m}/orders/{o}/authentications/{a}",
                        "MERCH-AU-001", "ORD-1001", "AUTH-9001")
                        .header(CallerAuthorization.CLIENT_ID_HEADER, "boost-order-processing"))
                .andExpect(status().isOk());

        assertThat(Files.exists(LOG_SINK))
                .as("the service log sink should exist after a retrieval")
                .isTrue();
        String log = Files.readString(LOG_SINK);

        assertThat(PAN.matcher(log).find()).as("PAN found in %s", LOG_SINK).isFalse();
        assertThat(log).as("authentication value (CAVV) found in %s", LOG_SINK)
                .doesNotContain(STORED_CAVV);
        assertThat(log).as("customer PII found in %s", LOG_SINK)
                .doesNotContain(CUSTOMER_REFERENCE);
    }
}
