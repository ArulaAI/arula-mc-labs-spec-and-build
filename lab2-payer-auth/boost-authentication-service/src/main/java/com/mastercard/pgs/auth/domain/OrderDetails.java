package com.mastercard.pgs.auth.domain;

/** Order block of the retrieval response — billing, shipping, customer and funding context. */
public record OrderDetails(
        String orderId,
        String currency,
        long amountMinor,
        String customerReference,
        String billingCountry,
        String shippingCountry,
        OrderFunding funding) {
}
