package com.mastercard.pgs.auth.client;

/**
 * Client for the legacy Target/PASS edge ({@code target-pass-proxy}) — the system of record
 * for payer authentication.
 *
 * <p>The legacy edge exposes two operations with very different costs. See
 * {@code .claude/context/target-pass-proxy.context.md}.
 */
public interface LegacyPassClient {

    /**
     * Read-only retrieval of a stored authentication result. Safe, free, repeatable.
     *
     * @return the stored record, or {@code null} when no record matches
     */
    LegacyAuthenticationRecord retrieveAuthenticationResult(LegacyRetrievalQuery query);

    /**
     * Live provider authentication.
     *
     * <p><b>BILLABLE.</b> Every invocation is charged and it affects the live transaction
     * outcome. It is not part of the retrieval path.
     */
    LegacyAuthenticationRecord authenticatePayer(AuthenticatePayerCommand command);
}
