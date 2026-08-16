package com.mastercard.pgs.orders.client.model;

/** Consumer view of the funding block. {@code cardNumber} is a PAN — never log it. */
public record OrderFunding(
        String method,
        String cardNumber,
        String cardBrand) {
}
