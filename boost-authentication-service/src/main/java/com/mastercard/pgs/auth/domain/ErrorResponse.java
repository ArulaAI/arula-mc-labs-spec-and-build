package com.mastercard.pgs.auth.domain;

import java.util.List;

/**
 * Structured error object (source, reason code, description, recoverability, details).
 *
 * <p>Never echo request or response payloads into {@code description} or {@code details} —
 * the retrieval payload carries CAVV, PAN and PII.
 */
public record ErrorResponse(
        String source,
        String reasonCode,
        String description,
        String recoverability,
        List<String> details) {
}
