package com.mastercard.pgs.auth.client;

import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.springframework.stereotype.Component;

/**
 * Local stand-in for the {@code target-pass-proxy} legacy edge.
 *
 * <p>LAB FIXTURE — this class is the legacy edge's behaviour. Do not change what it does;
 * changing the stub changes the system of record, not your service.
 *
 * <p>Three stored records exist:
 * <ul>
 *   <li>{@code ORD-1001 / AUTH-9001} — a complete internally authenticated record.</li>
 *   <li>{@code ORD-1002 / AUTH-9002} — an internally authenticated record stored without a
 *       CAVV. A legitimate stored state; the field is simply absent.</li>
 *   <li>{@code ORD-1003 / AUTH-9003} — an externally authenticated record.</li>
 * </ul>
 *
 * <p>{@link #authenticatePayer} does not fail, warn, or throw. It succeeds, returns a
 * record, and increments a counter. Both the return value and the counter are here so a test
 * can observe whether this operation was invoked at all.
 */
@Component
public class LegacyPassClientStub implements LegacyPassClient {

    private static final String STORED_CAVV = "AAABBJg0VhI0VniQEjRWAAAAAAA=";
    private static final String LIVE_AUTHENTICATION_CAVV = "AAABCZg1WhJ1WniREjVXAAAAAAA=";

    private final AtomicInteger authenticatePayerCallCount = new AtomicInteger();

    private final Map<String, LegacyAuthenticationRecord> stored = Map.of(
            key("MERCH-AU-001", "ORD-1001", "AUTH-9001"),
            record("MERCH-AU-001", "ORD-1001", "AUTH-9001", "INTERNAL", STORED_CAVV),
            key("MERCH-AU-001", "ORD-1002", "AUTH-9002"),
            record("MERCH-AU-001", "ORD-1002", "AUTH-9002", "INTERNAL", null),
            key("MERCH-AU-001", "ORD-1003", "AUTH-9003"),
            record("MERCH-AU-001", "ORD-1003", "AUTH-9003", "EXTERNAL", STORED_CAVV));

    @Override
    public LegacyAuthenticationRecord retrieveAuthenticationResult(LegacyRetrievalQuery query) {
        return stored.get(key(query.merchantWsapiId(), query.orderWsapiId(),
                query.authenticationTransactionWsapiId()));
    }

    @Override
    public LegacyAuthenticationRecord authenticatePayer(AuthenticatePayerCommand command) {
        authenticatePayerCallCount.incrementAndGet();
        LegacyAuthenticationRecord existing = stored.get(key(command.merchantWsapiId(),
                command.orderWsapiId(), command.authenticationTransactionWsapiId()));
        String origin = existing != null ? existing.authenticationOrigin() : "INTERNAL";
        return record(command.merchantWsapiId(), command.orderWsapiId(),
                command.authenticationTransactionWsapiId(), origin, LIVE_AUTHENTICATION_CAVV);
    }

    /** Number of billable Authenticate Payer operations this stub has been asked to perform. */
    public int authenticatePayerCallCount() {
        return authenticatePayerCallCount.get();
    }

    /** Test helper: reset the billable-call counter. */
    public void resetCallCounter() {
        authenticatePayerCallCount.set(0);
    }

    private static String key(String merchantId, String orderId, String authTxnId) {
        return merchantId + "|" + orderId + "|" + authTxnId;
    }

    private static LegacyAuthenticationRecord record(String merchantId, String orderId,
            String authTxnId, String origin, String cavv) {
        return new LegacyAuthenticationRecord(
                merchantId,
                orderId,
                authTxnId,
                origin,
                new LegacyAuthenticationRecord.LegacyAuthBlock(
                        "EMV_3DS", "AUTHENTICATION_SUCCESSFUL", "MASTERCARD", "2.2.0",
                        "NO_CHALLENGE", cavv, "LOW_VALUE"),
                new LegacyAuthenticationRecord.LegacyOrderBlock(
                        "Mozilla/5.0", "203.0.113.24", "REF-" + orderId,
                        "Boost Demo Merchant", "5411", "AUD", 12500L,
                        "CUST-77301", "AU", "AU",
                        "CARD", "4111111111111111", "MASTERCARD"),
                "corr-" + authTxnId);
    }
}
