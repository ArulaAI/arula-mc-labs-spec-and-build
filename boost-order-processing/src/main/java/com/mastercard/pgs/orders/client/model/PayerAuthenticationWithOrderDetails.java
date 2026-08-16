package com.mastercard.pgs.orders.client.model;

/** Consumer view of the response aggregate published by boost-authentication-service. */
public record PayerAuthenticationWithOrderDetails(
        PayerAuthentication payerAuthentication,
        LegacyOrderData legacyOrderData,
        Merchant merchant,
        OrderDetails order) {
}
