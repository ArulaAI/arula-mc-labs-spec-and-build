package com.mastercard.pgs.auth.domain;

/**
 * Payer authentication result as returned by the modern API.
 *
 * <p>{@code authenticationValue} is the CAVV. It is sensitive cardholder data and it is
 * {@code null} for stored legacy records that never carried one — that is a legitimate
 * stored state, not an error condition.
 */
public record PayerAuthentication(
        AuthenticationType method,
        String status,
        String scheme,
        String protocolVersion,
        String challengeIndicator,
        String authenticationValue,
        String psd2ScaExemption) {
}
