package com.mastercard.pgs.auth.client;

/**
 * A stored authentication record as the legacy Target/PASS edge returns it.
 *
 * <p>Shape and field names come from {@code .claude/context/target-pass-proxy.context.md}
 * (the Tier-1 compressed context for the legacy edge). {@code authenticationOrigin} is
 * {@code INTERNAL} for gateway-authenticated transactions and {@code EXTERNAL} for
 * externally authenticated ones.
 */
public record LegacyAuthenticationRecord(
        String merchantWsapiId,
        String orderWsapiId,
        String authenticationTransactionWsapiId,
        String authenticationOrigin,
        LegacyAuthBlock authentication,
        LegacyOrderBlock order,
        String correlationId) {

    /** Authentication block of the stored legacy record. {@code cavv} may be null. */
    public record LegacyAuthBlock(
            String authMethod,
            String authStatus,
            String schemeName,
            String protocolVersion,
            String challengeIndicator,
            String cavv,
            String psd2ScaExemptionCode) {
    }

    /** Order block of the stored legacy record. {@code cardNumber} is a PAN. */
    public record LegacyOrderBlock(
            String browserData,
            String ipAddress,
            String referenceOrder,
            String merchantName,
            String merchantCategoryCode,
            String currency,
            long amountMinor,
            String customerReference,
            String billingCountry,
            String shippingCountry,
            String fundingMethod,
            String cardNumber,
            String cardBrand) {
    }
}
