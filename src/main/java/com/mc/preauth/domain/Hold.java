package com.mc.preauth.domain;

import java.math.BigDecimal;
import java.time.Instant;

/**
 * An authorization hold. Immutable snapshot — state transitions (capture, reverse, expiry)
 * produce a new Hold rather than mutating this one. See {@link com.mc.preauth.repo.HoldStore}
 * for how snapshots are swapped atomically.
 *
 * @param holdId          server-generated identifier for this hold
 * @param transactionId   the AuthMessage.transactionId this hold was created from
 * @param amountAuthorized the full amount originally held
 * @param amountCaptured  cumulative amount captured against this hold so far
 * @param currency        ISO 4217 currency code
 * @param status          current lifecycle status
 * @param createdAt       when the hold was created
 * @param expiresAt       when the hold expires if not captured or reversed first
 */
public record Hold(
        String holdId,
        String transactionId,
        BigDecimal amountAuthorized,
        BigDecimal amountCaptured,
        String currency,
        HoldStatus status,
        Instant createdAt,
        Instant expiresAt
) {
    public BigDecimal remainingAuthorized() {
        return amountAuthorized.subtract(amountCaptured);
    }

    public boolean isExpired(Instant now) {
        return now.isAfter(expiresAt);
    }
}
