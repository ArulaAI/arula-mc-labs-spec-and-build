package com.mastercard.pgs.orders.client.model;

/** Consumer view of the merchant block of payer-authentication-v1.yaml. */
public record Merchant(
        String merchantId,
        String name,
        String categoryCode) {
}
