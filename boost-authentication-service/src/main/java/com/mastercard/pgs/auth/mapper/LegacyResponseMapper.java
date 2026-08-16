package com.mastercard.pgs.auth.mapper;

import com.mastercard.pgs.auth.client.LegacyAuthenticationRecord;
import com.mastercard.pgs.auth.domain.AuthenticationType;
import com.mastercard.pgs.auth.domain.PayerAuthentication;
import com.mastercard.pgs.auth.domain.PayerAuthenticationWithOrderDetails;
import org.springframework.stereotype.Component;

/**
 * Maps a stored legacy Target/PASS record onto the modern response aggregate.
 *
 * <p>Field-by-field mapping is in {@code .claude/context/target-pass-proxy.context.md}.
 *
 * <p>FIRST-PASS DRAFT — only the {@code payerAuthentication} block is mapped so far. The
 * {@code legacyOrderData}, {@code merchant} and {@code order} blocks of
 * {@code PayerAuthenticationWithOrderDetails} are still unmapped.
 */
@Component
public class LegacyResponseMapper {

    public PayerAuthenticationWithOrderDetails toModern(LegacyAuthenticationRecord legacyRecord) {
        return new PayerAuthenticationWithOrderDetails(
                toPayerAuthentication(legacyRecord.authentication()),
                // TODO(PGSE-88): map legacyOrderData, merchant and order from legacyRecord.order()
                null,
                null,
                null);
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
