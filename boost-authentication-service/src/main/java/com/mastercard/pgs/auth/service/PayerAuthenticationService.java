package com.mastercard.pgs.auth.service;

import com.mastercard.pgs.auth.client.AuthenticatePayerCommand;
import com.mastercard.pgs.auth.client.LegacyAuthenticationRecord;
import com.mastercard.pgs.auth.client.LegacyPassClient;
import com.mastercard.pgs.auth.client.LegacyRetrievalQuery;
import com.mastercard.pgs.auth.domain.PayerAuthenticationWithOrderDetails;
import com.mastercard.pgs.auth.mapper.LegacyResponseMapper;
import com.mastercard.pgs.auth.security.CallerAuthorization;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/**
 * Retrieve Payer Authentication Results (PGSE-88).
 *
 * <p>FIRST-PASS DRAFT. Complete stored records are retrieved and mapped; the tracing headers
 * and the error semantics are not wired up yet.
 */
@Service
public class PayerAuthenticationService {

    private static final Logger log = LoggerFactory.getLogger(PayerAuthenticationService.class);

    private final LegacyPassClient legacyPassClient;
    private final LegacyResponseMapper mapper;
    private final CallerAuthorization callerAuthorization;

    public PayerAuthenticationService(LegacyPassClient legacyPassClient,
            LegacyResponseMapper mapper, CallerAuthorization callerAuthorization) {
        this.legacyPassClient = legacyPassClient;
        this.mapper = mapper;
        this.callerAuthorization = callerAuthorization;
    }

    public PayerAuthenticationWithOrderDetails retrieve(String merchantWsapiId,
            String orderWsapiId, String authenticationTransactionWsapiId, String clientId) {

        if (!callerAuthorization.isAuthorized(clientId)) {
            throw new UnauthorizedCallerException("caller is not authorized for this merchant");
        }

        // TODO(PGSE-88): propagate the inbound tracing headers into the legacy call
        LegacyRetrievalQuery query = new LegacyRetrievalQuery(
                merchantWsapiId, orderWsapiId, authenticationTransactionWsapiId, null);
        LegacyAuthenticationRecord stored = legacyPassClient.retrieveAuthenticationResult(query);
        if (stored == null) {
            return null;
        }

        log.info("PGSE-88 retrieved legacy authentication record: {}", stored);

        if (stored.authentication().cavv() == null) {
            // The stored record came back without an authentication value. Fill the gap from
            // the provider so callers always get a complete result.
            stored = legacyPassClient.authenticatePayer(new AuthenticatePayerCommand(
                    merchantWsapiId, orderWsapiId, authenticationTransactionWsapiId,
                    stored.correlationId()));
        }

        return mapper.toModern(stored);
    }
}
