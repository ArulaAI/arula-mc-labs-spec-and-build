package com.mastercard.pgs.auth.domain;

/** Merchant identity block of the retrieval response. */
public record Merchant(
        String merchantId,
        String name,
        String categoryCode) {
}
