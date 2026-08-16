package com.mastercard.pgs.orders.client.model;

/** Consumer view of the payer authentication block of payer-authentication-v1.yaml. */
public record PayerAuthentication(
        String method,
        String status,
        String scheme,
        String protocolVersion,
        String challengeIndicator,
        String authenticationValue,
        String psd2ScaExemption) {
}
