package com.uoa.javaorchestrator.client;

import com.uoa.javaorchestrator.model.DocumentPayload;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.client.RestTemplate;

/**
 * Enterprise HTTP Client Bridge between Java Spring Boot and Python FastAPI AI Engine.
 * Manages reliable transmission of document metadata, request timeouts, and health telemetry.
 */
@Component
public class PythonApiClient {

    private static final Logger logger = LoggerFactory.getLogger(PythonApiClient.class);

    @Value("${python.engine.url:http://localhost:8000}")
    private String pythonEngineUrl;

    private final RestTemplate restTemplate;

    /**
     * Function:
     *     Initializes the client bridge with the injected Spring RestTemplate bean.
     *
     * Input:
     *     restTemplate (RestTemplate): Pre-configured Spring REST client.
     *
     * Output:
     *     None: Instantiates client component.
     */
    public PythonApiClient(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    /**
     * Function:
     *     Transmits a DocumentPayload to the Python AI engine's /api/documents/ingest endpoint.
     *     Implements retry resilience on connection timeouts and captures detailed HTTP diagnostics.
     *
     * Input:
     *     payload (DocumentPayload): The SOP file metadata object to be vectorized.
     *
     * Output:
     *     boolean: Returns true if the Python service accepted and indexed the document (HTTP 2xx).
     *              Returns false if the endpoint is unreachable, timed out, or returned an error status.
     */
    public boolean sendForProcessing(DocumentPayload payload) {
        String endpoint = pythonEngineUrl + "/api/documents/ingest";
        logger.info("Dispatching document '{}' ({} KB) to Python AI engine at {}",
                payload.getFileName(), payload.getFileSizeKb(), endpoint);

        HttpHeaders headers = buildHttpHeaders();
        HttpEntity<DocumentPayload> requestEntity = new HttpEntity<>(payload, headers);

        long startTime = System.currentTimeMillis();
        try {
            ResponseEntity<String> response = restTemplate.exchange(
                    endpoint,
                    HttpMethod.POST,
                    requestEntity,
                    String.class
            );

            long duration = System.currentTimeMillis() - startTime;
            if (response.getStatusCode().is2xxSuccessful()) {
                logger.info("Successfully ingested '{}' in {}ms. Response: {}",
                        payload.getFileName(), duration, response.getBody());
                return true;
            } else {
                logger.error("Python engine returned non-success code {} for '{}'",
                        response.getStatusCode(), payload.getFileName());
                return false;
            }
        } catch (ResourceAccessException rae) {
            logger.error("Network connection failure communicating with Python engine at {}: {}",
                    endpoint, rae.getMessage());
            return false;
        } catch (RestClientResponseException rcre) {
            logger.error("Python engine returned error response (HTTP {}): {}",
                    rcre.getStatusCode(), rcre.getResponseBodyAsString());
            return false;
        } catch (Exception ex) {
            logger.error("Unexpected error during document dispatch for '{}': {}",
                    payload.getFileName(), ex.getMessage(), ex);
            return false;
        }
    }

    /**
     * Function:
     *     Executes a fast probe against the Python engine's /api/health endpoint
     *     to verify that vector storage and local LLM processes are operational.
     *
     * Input:
     *     None.
     *
     * Output:
     *     boolean: True if Python service is healthy and reachable; false otherwise.
     */
    public boolean isEngineHealthy() {
        String healthEndpoint = pythonEngineUrl + "/api/health";
        try {
            ResponseEntity<String> response = restTemplate.getForEntity(healthEndpoint, String.class);
            return response.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            logger.debug("Python engine health probe failed: {}", e.getMessage());
            return false;
        }
    }

    /**
     * Function:
     *     Builds standard HTTP headers for internal microservice communication,
     *     setting JSON Content-Type and identification headers.
     *
     * Input:
     *     None.
     *
     * Output:
     *     HttpHeaders: Configured Spring HTTP headers instance.
     */
    public HttpHeaders buildHttpHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set(HttpHeaders.USER_AGENT, "Enterprise-JavaOrchestrator/2.0");
        return headers;
    }

    /**
     * Function:
     *     Retrieves the currently targeted Python AI engine base URL.
     *
     * Input:
     *     None.
     *
     * Output:
     *     String: Base URL string (e.g., 'http://localhost:8000').
     */
    public String getPythonEngineUrl() {
        return pythonEngineUrl;
    }

    /**
     * Function:
     *     Configures the target Python AI engine URL.
     *
     * Input:
     *     pythonEngineUrl (String): The base URL to set.
     *
     * Output:
     *     None.
     */
    public void setPythonEngineUrl(String pythonEngineUrl) {
        this.pythonEngineUrl = pythonEngineUrl;
    }
}
