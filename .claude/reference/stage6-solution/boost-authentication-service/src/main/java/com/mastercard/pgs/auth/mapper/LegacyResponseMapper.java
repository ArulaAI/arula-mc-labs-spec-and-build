package com.mastercard.pgs.auth.mapper;

import com.mastercard.pgs.auth.client.LegacyAuthenticationRecord;
import com.mastercard.pgs.auth.domain.AuthenticationType;
import com.mastercard.pgs.auth.domain.LegacyOrderData;
import com.mastercard.pgs.auth.domain.Merchant;
import com.mastercard.pgs.auth.domain.OrderDetails;
import com.mastercard.pgs.auth.domain.OrderFunding;
import com.mastercard.pgs.auth.domain.PayerAuthentication;
import com.mastercard.pgs.auth.domain.PayerAuthenticationWithOrderDetails;
import org.springframework.stereotype.Component;

/**
 * Maps a stored legacy Target/PASS record onto the modern response aggregate.
 *
 * <p>The mapping is 1:1 with the legacy field map in
 * {@code .claude/context/target-pass-proxy.context.md}. Nothing is computed, defaulted or
 * enriched here — a null {@code cavv} maps through as a null authentication value.
 */
@Component
public class LegacyResponseMapper {

    public PayerAuthenticationWithOrderDetails toModern(LegacyAuthenticationRecord legacyRecord) {
        LegacyAuthenticationRecord.LegacyOrderBlock order = legacyRecord.order();
        return new PayerAuthenticationWithOrderDetails(
                toPayerAuthentication(legacyRecord.authentication()),
                new LegacyOrderData(order.browserData(), order.ipAddress(),
                        order.referenceOrder()),
                new Merchant(legacyRecord.merchantWsapiId(), order.merchantName(),
                        order.merchantCategoryCode()),
                new OrderDetails(
                        legacyRecord.orderWsapiId(),
                        order.currency(),
                        order.amountMinor(),
                        order.customerReference(),
                        order.billingCountry(),
                        order.shippingCountry(),
                        new OrderFunding(order.fundingMethod(), order.cardNumber(),
                                order.cardBrand())));
    }

    private PayerAuthentication toPayerAuthentication(
            LegacyAuthenticationRecord.LegacyAuthBlock auth) {
        return new PayerAuthentication(
                AuthenticationType.valueOf(auth.authMethod()),
                auth.authStatus(),
                auth.schemeName(),
                auth.protocolVersion(),
                auth.challengeIndicator(),
                auth.cavv(),
                auth.psd2ScaExemptionCode());
    }
}
