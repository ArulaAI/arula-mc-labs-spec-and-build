package com.mc.preauth.domain;

/**
 * Result of a capture attempt. Sealed so callers must handle both outcomes explicitly —
 * a capture is never allowed to "fail silently."
 */
public sealed interface CaptureOutcome {

    record Captured(Hold updatedHold) implements CaptureOutcome {
    }

    record Rejected(String reason) implements CaptureOutcome {
    }
}
