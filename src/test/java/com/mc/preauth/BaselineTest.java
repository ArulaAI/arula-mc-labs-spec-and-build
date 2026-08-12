package com.mc.preauth;

import com.mc.preauth.domain.AuthMessage;
import com.mc.preauth.domain.CaptureRequest;
import com.mc.preauth.domain.Hold;
import com.mc.preauth.domain.HoldStatus;
import com.mc.preauth.repo.HoldStore;
import com.mc.preauth.service.HoldService;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

/**
 * Baseline: the app compiles, a hold can be created, and capture()/reverse() are confirmed
 * genuinely unbuilt. This test must stay green on a fresh clone — it is not the lab exercise,
 * it is the starting point for it.
 */
class BaselineTest {

    private final Clock fixedClock = Clock.fixed(Instant.parse("2026-01-01T00:00:00Z"), ZoneOffset.UTC);
    private final HoldService holdService = new HoldService(new HoldStore(), fixedClock);

    @Test
    void createHoldProducesAnActiveHoldForTheFullRequestedAmount() {
        AuthMessage message = new AuthMessage(
                "TXN-001",
                "ACQUIRERBIC",
                "ISSUERBIC1",
                "tok_4111********1111",
                new BigDecimal("100.00"),
                "USD",
                "MERCH-01",
                "REQ-001",
                Duration.ofDays(7)
        );

        Hold hold = holdService.createHold(message);

        assertThat(hold.status()).isEqualTo(HoldStatus.ACTIVE);
        assertThat(hold.amountAuthorized()).isEqualByComparingTo("100.00");
        assertThat(hold.amountCaptured()).isEqualByComparingTo("0.00");
        assertThat(hold.remainingAuthorized()).isEqualByComparingTo("100.00");
    }

    @Test
    void captureIsNotYetImplemented() {
        CaptureRequest request = new CaptureRequest("HOLD-1", "REQ-CAP-1", new BigDecimal("50.00"), "USD");

        assertThatThrownBy(() -> holdService.capture(request))
                .isInstanceOf(UnsupportedOperationException.class);
    }

    @Test
    void reverseIsNotYetImplemented() {
        assertThatThrownBy(() -> holdService.reverse("HOLD-1"))
                .isInstanceOf(UnsupportedOperationException.class);
    }
}
