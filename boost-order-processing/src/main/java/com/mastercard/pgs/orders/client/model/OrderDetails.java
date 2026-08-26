package com.mastercard.pgs.orders.client.model;

/** Consumer view of the order block of payer-authentication-v1.yaml. */
public record OrderDetails(
        String orderId,
        String currency,
        long amountMinor,
        String customerReference,
        String billingCountry,
        String shippingCountry,
        OrderFunding funding) {
}
