package com.mastercard.pgs.auth.api;

import com.mastercard.pgs.auth.domain.PayerAuthenticationWithOrderDetails;
import com.mastercard.pgs.auth.security.CallerAuthorization;
import com.mastercard.pgs.auth.service.PayerAuthenticationService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

/**
 * Modern Retrieve Payer Authentication Results endpoint.
 *
 * <p>Contract: {@code src/main/resources/openapi/payer-authentication-v1.yaml}.
 *
 * <p>FIRST-PASS DRAFT — the tracing headers are not read or echoed yet.
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
                    String clientId) {

        // TODO(PGSE-88): read and echo the tracing headers (TracingHeaders.ALL)
        return ResponseEntity.ok(payerAuthenticationService.retrieve(
                merchantWsapiId, orderWsapiId, authenticationTransactionWsapiId, clientId));
    }
}
