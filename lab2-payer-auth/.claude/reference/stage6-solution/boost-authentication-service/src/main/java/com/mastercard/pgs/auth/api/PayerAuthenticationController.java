package com.mastercard.pgs.auth.api;

import com.mastercard.pgs.auth.config.TracingHeaders;
import com.mastercard.pgs.auth.domain.PayerAuthenticationWithOrderDetails;
import com.mastercard.pgs.auth.security.CallerAuthorization;
import com.mastercard.pgs.auth.service.PayerAuthenticationService;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

/**
 * Modern Retrieve Payer Authentication Results endpoint.
 *
 * <p>Contract: {@code src/main/resources/openapi/payer-authentication-v1.yaml}. HTTP concerns
 * only — the tracing headers are collected here, propagated by the service across the hop, and
 * echoed back to the caller. Their values are never logged.
 */
@RestController
public class PayerAuthenticationController {

    private final PayerAuthenticationService payerAuthenticationService;

    public PayerAuthenticationController(PayerAuthenticationService payerAuthenticationService) {
        this.payerAuthenticationService = payerAuthenticationService;
    }

    @GetMapping("/merchants/{merchant_wsapi_id}/orders/{order_wsapi_id}"
            + "/authentications/{authentication_transaction_wsapi_id}")
    public ResponseEntity<PayerAuthenticationWithOrderDetails> retrievePayerAuthentication(
            @PathVariable("merchant_wsapi_id") String merchantWsapiId,
            @PathVariable("order_wsapi_id") String orderWsapiId,
            @PathVariable("authentication_transaction_wsapi_id") String authenticationTransactionWsapiId,
            @RequestHeader(value = CallerAuthorization.CLIENT_ID_HEADER, required = false)
                    String clientId,
            @RequestHeader Map<String, String> requestHeaders) {

        Map<String, String> tracing = tracingHeaders(requestHeaders);
        PayerAuthenticationWithOrderDetails result = payerAuthenticationService.retrieve(
                merchantWsapiId, orderWsapiId, authenticationTransactionWsapiId, clientId,
                tracing);

        HttpHeaders responseHeaders = new HttpHeaders();
        tracing.forEach(responseHeaders::add);
        return ResponseEntity.ok().headers(responseHeaders).body(result);
    }

    private static Map<String, String> tracingHeaders(Map<String, String> requestHeaders) {
        Map<String, String> tracing = new LinkedHashMap<>();
        for (String name : TracingHeaders.ALL) {
            requestHeaders.entrySet().stream()
                    .filter(entry -> entry.getKey().equalsIgnoreCase(name))
                    .findFirst()
                    .ifPresent(entry -> tracing.put(name, entry.getValue()));
        }
        return tracing;
    }
}
