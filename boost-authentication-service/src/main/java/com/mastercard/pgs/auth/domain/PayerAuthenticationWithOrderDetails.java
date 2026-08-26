package com.mastercard.pgs.auth.domain;

/** Response aggregate for GET .../authentications/{authentication_transaction_wsapi_id}. */
public record PayerAuthenticationWithOrderDetails(
        PayerAuthentication payerAuthentication,
        LegacyOrderData legacyOrderData,
        Merchant merchant,
        OrderDetails order) {
}
