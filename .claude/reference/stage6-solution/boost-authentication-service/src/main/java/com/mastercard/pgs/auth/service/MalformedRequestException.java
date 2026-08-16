package com.mastercard.pgs.auth.service;

/** The request could not be accepted: an identifier is missing or malformed. */
public class MalformedRequestException extends RuntimeException {

    public MalformedRequestException(String message) {
        super(message);
    }
}
