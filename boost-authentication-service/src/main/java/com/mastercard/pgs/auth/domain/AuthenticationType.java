package com.mastercard.pgs.auth.domain;

/** Authentication methods supported by the gateway (PGSE-88 in-scope list). */
public enum AuthenticationType {
    EMV_3DS,
    PASSKEY,
    RUPAY
}
