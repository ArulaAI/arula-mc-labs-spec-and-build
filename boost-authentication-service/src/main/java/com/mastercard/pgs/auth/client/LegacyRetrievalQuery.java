package com.mastercard.pgs.auth.client;

import java.util.Map;

/**
 * Read-only lookup key for a stored authentication record on the legacy edge.
 *
 * <p>{@code merchantWsapiId}, {@code orderWsapiId} and {@code authenticationTransactionWsapiId}
 * are the key. {@code tracingHeaders} carries every inbound tracing header
 * ({@link com.mastercard.pgs.auth.config.TracingHeaders#ALL}) across the hop — see
 * {@code specs/NON_NEGOTIABLES.md} §4 — and does not affect what comes back.
 */
public record LegacyRetrievalQuery(
        String merchantWsapiId,
        String orderWsapiId,
        String authenticationTransactionWsapiId,
        Map<String, String> tracingHeaders) {
}
