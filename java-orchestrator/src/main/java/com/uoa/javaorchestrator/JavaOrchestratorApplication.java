package com.uoa.javaorchestrator;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

/**
 * Main application entry point for the Java Spring Boot Orchestrator.
 * Configures scheduling capabilities and registers enterprise HTTP communication beans.
 */
@SpringBootApplication
@EnableScheduling
public class JavaOrchestratorApplication {

    /**
     * Function:
     *     Standard JVM entry point initiating Spring Boot bootstrap, component scanning,
     *     and embedded web server initialization.
     *
     * Input:
     *     args (String[]): Command line arguments passed at process execution.
     *
     * Output:
     *     None: Launches Spring application context.
     */
    public static void main(String[] args) {
        SpringApplication.run(JavaOrchestratorApplication.class, args);
    }

    /**
     * Function:
     *     Constructs and registers a production-grade RestTemplate bean configured with explicit
     *     connection and read timeouts using SimpleClientHttpRequestFactory. Prevents thread exhaustion
     *     if downstream AI services experience latency.
     *
     * Input:
     *     None.
     *
     * Output:
     *     RestTemplate: Configured HTTP client bean with 5-second connect and 60-second read timeouts.
     */
    @Bean
    public RestTemplate restTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(5));
        factory.setReadTimeout(Duration.ofSeconds(60));
        return new RestTemplate(factory);
    }
}
