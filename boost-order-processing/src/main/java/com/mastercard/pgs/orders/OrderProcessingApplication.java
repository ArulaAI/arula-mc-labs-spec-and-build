package com.mastercard.pgs.orders;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/** Order processing — consumer of the Retrieve Payer Authentication Results API. */
@SpringBootApplication
public class OrderProcessingApplication {

    public static void main(String[] args) {
        SpringApplication.run(OrderProcessingApplication.class, args);
    }
}
