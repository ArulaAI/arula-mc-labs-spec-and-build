package com.mastercard.pgs.orders.client.model;

/** Consumer view of the legacy order data block of payer-authentication-v1.yaml. */
public record LegacyOrderData(
        String browser,
        String ipAddress,
        String referenceOrder) {
}
