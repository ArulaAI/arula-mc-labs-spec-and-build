package com.mc.preauth.domain;

import java.math.BigDecimal;

/**
 * A request to capture (settle) some or all of an existing hold.
 *
 * @param holdId    the hold being captured against
 * @param requestId client-supplied idempotency key — a retried request with the same
 *                  requestId against the same holdId must never create a second capture
 * @param amount    the amount to capture in this call; must never exceed the hold's
 *                  remaining authorized (held) amount, not the original requested amount
 * @param currency  ISO 4217 currency code; must match the hold's currency
 */
public record CaptureRequest(
        String holdId,
        String requestId,
        BigDecimal amount,
        String currency
) {
}
