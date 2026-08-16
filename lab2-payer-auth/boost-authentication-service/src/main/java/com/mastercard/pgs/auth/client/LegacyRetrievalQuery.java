package com.mastercard.pgs.auth.client;

/** Read-only lookup key for a stored authentication record on the legacy edge. */
public record LegacyRetrievalQuery(
        String merchantWsapiId,
        String orderWsapiId,
        String authenticationTransactionWsapiId,
        String correlationId) {
}
