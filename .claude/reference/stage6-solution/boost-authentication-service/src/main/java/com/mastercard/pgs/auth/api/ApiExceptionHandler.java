package com.mastercard.pgs.auth.api;

import com.mastercard.pgs.auth.domain.ErrorResponse;
import com.mastercard.pgs.auth.service.AuthenticationRecordNotFoundException;
import com.mastercard.pgs.auth.service.MalformedRequestException;
import com.mastercard.pgs.auth.service.UnauthorizedCallerException;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * Global, consistent error responses.
 *
 * <p>400, 403 and 404 are distinct and mean distinct things. No payload content, stack trace or
 * internal detail is echoed back to the caller.
 */
@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(MalformedRequestException.class)
    public ResponseEntity<ErrorResponse> handleMalformedRequest(MalformedRequestException ex) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(new ErrorResponse(
                "PAYER_AUTHENTICATION",
                "INVALID_REQUEST",
                "Malformed or invalid request",
                "NOT_RECOVERABLE",
                List.of()));
    }

    @ExceptionHandler(UnauthorizedCallerException.class)
    public ResponseEntity<ErrorResponse> handleUnauthorizedCaller(UnauthorizedCallerException ex) {
        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(new ErrorResponse(
                "PAYER_AUTHENTICATION",
                "UNAUTHORIZED",
                "Caller is not authorized to retrieve payer authentication results",
                "NOT_RECOVERABLE",
                List.of()));
    }

    @ExceptionHandler(AuthenticationRecordNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(AuthenticationRecordNotFoundException ex) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(new ErrorResponse(
                "PAYER_AUTHENTICATION",
                "NOT_FOUND",
                "No matching authentication record",
                "NOT_RECOVERABLE",
                List.of()));
    }
}
