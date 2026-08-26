package com.mastercard.pgs.orders;

import static org.assertj.core.api.Assertions.assertThat;

import com.mastercard.pgs.orders.service.OrderAuthenticationLookup;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

/** Baseline: the consumer context loads and the lookup collaborator is wired. */
@SpringBootTest
class BaselineTest {

    @Autowired
    private OrderAuthenticationLookup orderAuthenticationLookup;

    @Test
    void contextLoads() {
        assertThat(orderAuthenticationLookup).isNotNull();
    }
}
