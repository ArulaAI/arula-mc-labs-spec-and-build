package com.mastercard.pgs.auth.domain;

/** Additional order context carried over from the legacy platform. */
public record LegacyOrderData(
        String browser,
        String ipAddress,
        String referenceOrder) {
}
