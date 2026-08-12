package com.mc.preauth;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Clock;

@Configuration
public class PreauthConfig {

    @Bean
    public Clock clock() {
        return Clock.systemUTC();
    }
}
