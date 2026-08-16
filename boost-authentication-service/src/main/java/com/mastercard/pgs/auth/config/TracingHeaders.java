package com.mastercard.pgs.auth.config;

import java.util.List;

/**
 * Tracing / correlation headers carried across every PGS service hop.
 *
 * <p>Propagate them. Never log their values.
 */
public final class TracingHeaders {

    public static final String CLIENT_CORRELATION_ID = "X-Client-Correlation-Id";
    public static final String MC_CORRELATION_ID = "X-Mc-Correlation-Id";
    public static final String MC_CORRELATION_REQUEST_ID = "X-Mc-Correlation-Request-ID";
    public static final String MC_TNS_LOGGING_ID = "X-Mc-Tns-Logging-Id";
    public static final String MC_TOGGLE_VERSION = "X-Mc-Toggle-Version";

    public static final List<String> ALL = List.of(
            CLIENT_CORRELATION_ID,
            MC_CORRELATION_ID,
            MC_CORRELATION_REQUEST_ID,
            MC_TNS_LOGGING_ID,
            MC_TOGGLE_VERSION);

    private TracingHeaders() {
    }
}
