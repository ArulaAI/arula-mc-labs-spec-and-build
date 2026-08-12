package com.mc.preauth.service;

import com.mc.preauth.domain.AuthMessage;
import com.mc.preauth.domain.CaptureOutcome;
import com.mc.preauth.domain.CaptureRequest;
import com.mc.preauth.domain.Hold;
import com.mc.preauth.domain.HoldStatus;
import com.mc.preauth.repo.HoldStore;
import org.springframework.stereotype.Service;

import java.time.Clock;
import java.time.Instant;
import java.util.UUID;

/**
 * Incremental authorization core. createHold is the built, minimal baseline.
 *
 * capture() and reverse() are intentionally unbuilt — this is the feature the lab exists to
 * build. See specs/incremental-auth.spec.md and specs/NON_NEGOTIABLES.md before implementing
 * either: a retried capture must never apply twice, a partial capture must never exceed the
 * remaining held amount (not the original requested amount), and no capture may occur after
 * a hold has been reversed or has expired.
 */
@Service
public class HoldService {

    private final HoldStore holdStore;
    private final Clock clock;

    public HoldService(HoldStore holdStore, Clock clock) {
        this.holdStore = holdStore;
        this.clock = clock;
    }

    public Hold createHold(AuthMessage message) {
        Instant now = clock.instant();
        Hold hold = new Hold(
                UUID.randomUUID().toString(),
                message.transactionId(),
                message.requestedAmount(),
                java.math.BigDecimal.ZERO,
                message.currency(),
                HoldStatus.ACTIVE,
                now,
                message.expiresAt(now)
        );
        holdStore.save(hold);
        return hold;
    }

    public CaptureOutcome capture(CaptureRequest request) {
        throw new UnsupportedOperationException(
                "capture() is not yet implemented — see specs/incremental-auth.spec.md");
    }

    public Hold reverse(String holdId) {
        throw new UnsupportedOperationException(
                "reverse() is not yet implemented — see specs/incremental-auth.spec.md");
    }
}
