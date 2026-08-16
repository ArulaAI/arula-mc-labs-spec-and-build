package com.mastercard.pgs.auth.service;

/** The caller is not authorized to retrieve payer authentication results. */
public class UnauthorizedCallerException extends RuntimeException {

    public UnauthorizedCallerException(String message) {
        super(message);
    }
}
