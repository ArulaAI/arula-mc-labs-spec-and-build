package com.mastercard.pgs.auth.api;

import com.mastercard.pgs.auth.domain.ErrorResponse;
import com.mastercard.pgs.auth.service.UnauthorizedCallerException;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/** Global, consistent error responses for the retrieval API. */
@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(UnauthorizedCallerException.class)
    public ResponseEntity<ErrorResponse> handleUnauthorizedCaller(UnauthorizedCallerException ex) {
        // Do not confirm to an unknown caller that the record exists.
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(new ErrorResponse(
                "PAYER_AUTHENTICATION",
                "NOT_FOUND",
                "No matching authentication record",
                "NOT_RECOVERABLE",
                List.of()));
    }
}
