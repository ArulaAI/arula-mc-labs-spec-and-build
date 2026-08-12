package com.mc.preauth.domain;

import java.math.BigDecimal;
import java.time.Instant;

/**
 * Incoming authorization request, shaped by ISO 20022 CardPaymentAuthorisation-style fields.
 *
 * @param transactionId       ISO 20022 TxId — the network-assigned transaction identifier
 * @param instructingAgent    BIC of the acquirer/issuer originating the request
 * @param instructedAgent     BIC of the party the request is addressed to
 * @param cardToken           tokenized PAN (never a raw PAN)
 * @param requestedAmount     amount requested to be held
 * @param currency            ISO 4217 currency code
 * @param merchantId          merchant identifier
 * @param requestId           client-supplied idempotency key for this authorization request
 * @param holdDuration        how long the hold remains valid before expiry
 */
public record AuthMessage(
        String transactionId,
        String instructingAgent,
        String instructedAgent,
        String cardToken,
        BigDecimal requestedAmount,
        String currency,
        String merchantId,
        String requestId,
        java.time.Duration holdDuration
) {
    public Instant expiresAt(Instant from) {
        return from.plus(holdDuration);
    }
}
