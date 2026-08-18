package com.mastercard.pgs.auth.service;

import com.mastercard.pgs.auth.client.LegacyAuthenticationRecord;
import com.mastercard.pgs.auth.client.LegacyPassClient;
import com.mastercard.pgs.auth.client.LegacyRetrievalQuery;
import com.mastercard.pgs.auth.domain.PayerAuthenticationWithOrderDetails;
import com.mastercard.pgs.auth.mapper.LegacyResponseMapper;
import com.mastercard.pgs.auth.security.CallerAuthorization;
import java.util.Map;
import java.util.regex.Pattern;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

/**
 * Retrieve Payer Authentication Results (PGSE-88).
 *
 * <p>Read-only retrieval of a stored legacy record. This path never invokes the legacy
 * Authenticate Payer operation — it is billable and must never be called a second time
 * (spec AC-INCOMPLETE, {@code specs/NON_NEGOTIABLES.md} §3).
 */
@Service
public class PayerAuthenticationService {

    private static final Logger log = LoggerFactory.getLogger(PayerAuthenticationService.class);

    private static final String INTERNAL_ORIGIN = "INTERNAL";
    private static final Pattern IDENTIFIER = Pattern.compile("[A-Za-z0-9_-]{1,64}");

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
            String orderWsapiId, String authenticationTransactionWsapiId, String clientId,
            Map<String, String> tracingHeaders) {

        if (!callerAuthorization.isAuthorized(clientId)) {
            throw new UnauthorizedCallerException("caller is not authorized for this merchant");
        }
        requireIdentifier(merchantWsapiId, "merchant_wsapi_id");
        requireIdentifier(orderWsapiId, "order_wsapi_id");
        requireIdentifier(authenticationTransactionWsapiId,
                "authentication_transaction_wsapi_id");

        LegacyRetrievalQuery query = new LegacyRetrievalQuery(
                merchantWsapiId, orderWsapiId, authenticationTransactionWsapiId,
                tracingHeaders);

        LegacyAuthenticationRecord stored = legacyPassClient.retrieveAuthenticationResult(query);
        if (stored == null || !INTERNAL_ORIGIN.equals(stored.authenticationOrigin())) {
            // Absent, or authenticated outside the gateway. Externally authenticated
            // transactions are out of scope and are not served as if internal.
            throw new AuthenticationRecordNotFoundException("no matching authentication record");
        }

        // The stored record is the answer, exactly as stored. A missing authentication value is
        // a legitimate stored state and is mapped through as null; refreshing it from the
        // provider would trigger a second, billable Authenticate Payer.
        PayerAuthenticationWithOrderDetails result = mapper.toModern(stored);

        log.info("PGSE-88 retrieval completed for authentication transaction {}",
                authenticationTransactionWsapiId);
        return result;
    }

    private static void requireIdentifier(String value, String name) {
        if (value == null || !IDENTIFIER.matcher(value).matches()) {
            throw new MalformedRequestException(name + " is malformed");
        }
    }
}
