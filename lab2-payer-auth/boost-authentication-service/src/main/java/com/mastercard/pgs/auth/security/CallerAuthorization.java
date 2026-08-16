package com.mastercard.pgs.auth.security;

import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Deny-by-default authorization for callers of the retrieval API.
 *
 * <p>Every interface is a trust boundary, including calls from other internal services:
 * an unknown or absent client id is refused.
 */
@Component
public class CallerAuthorization {

    public static final String CLIENT_ID_HEADER = "X-Mc-Client-Id";

    private final List<String> authorizedClients;

    public CallerAuthorization(
            @Value("${pgs.auth.authorized-clients:}") List<String> authorizedClients) {
        this.authorizedClients = authorizedClients == null ? List.of() : authorizedClients;
    }

    /** Deny by default: only an explicitly allow-listed client id is authorized. */
    public boolean isAuthorized(String clientId) {
        return clientId != null && !clientId.isBlank() && authorizedClients.contains(clientId);
    }
}
