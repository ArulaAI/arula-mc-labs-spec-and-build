package com.mastercard.pgs.auth.service;

/** No in-scope stored authentication record matches the requested identifiers. */
public class AuthenticationRecordNotFoundException extends RuntimeException {

    public AuthenticationRecordNotFoundException(String message) {
        super(message);
    }
}
