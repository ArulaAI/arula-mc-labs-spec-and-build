package com.mastercard.pgs.auth.domain;

/**
 * Funding details of the authenticated order.
 *
 * <p>{@code cardNumber} is a PAN. The legacy platform is the system of record and returns it;
 * it must never reach a log line, an error message, or any other sink.
 */
public record OrderFunding(
        String method,
        String cardNumber,
        String cardBrand) {
}
