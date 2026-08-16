package com.mastercard.pgs.auth.client;

/** Input to the legacy Authenticate Payer operation. Authenticate Payer is BILLABLE. */
public record AuthenticatePayerCommand(
        String merchantWsapiId,
        String orderWsapiId,
        String authenticationTransactionWsapiId,
        String correlationId) {
}
