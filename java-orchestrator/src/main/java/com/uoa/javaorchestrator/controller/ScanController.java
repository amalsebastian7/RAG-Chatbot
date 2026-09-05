package com.uoa.javaorchestrator.controller;

import com.uoa.javaorchestrator.client.PythonApiClient;
import com.uoa.javaorchestrator.model.DocumentPayload;
import com.uoa.javaorchestrator.scheduler.ScanScheduler;
import com.uoa.javaorchestrator.service.FileScannerService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Enterprise REST API Controller providing remote telemetry and ingestion control
 * for the Java Orchestrator microservice.
 */
@RestController
@RequestMapping("/api/scan")
@CrossOrigin(origins = "*")
public class ScanController {

    private final ScanScheduler scheduler;
    private final FileScannerService scannerService;
    private final PythonApiClient apiClient;

    /**
     * Function:
     *     Initializes the controller with necessary scheduler, scanner, and API client components.
     *
     * Input:
     *     scheduler (ScanScheduler): Scheduler coordinating background and manual scans.
     *     scannerService (FileScannerService): Scanner analyzing local directory files.
     *     apiClient (PythonApiClient): Client checking Python AI Engine connectivity.
     *
     * Output:
     *     None: Instantiates controller instance.
     */
    public ScanController(ScanScheduler scheduler, FileScannerService scannerService, PythonApiClient apiClient) {
        this.scheduler = scheduler;
        this.scannerService = scannerService;
        this.apiClient = apiClient;
    }

    /**
     * Function:
     *     Exposes an HTTP POST endpoint allowing external clients (e.g., Streamlit UI, CI/CD pipelines)
     *     to trigger an on-demand filesystem scan and vector ingestion cycle.
     *
     * Input:
     *     forceAll (boolean): Query parameter indicating whether to re-index all documents (true)
     *                         or only delta modifications (false). Defaults to false.
     *
     * Output:
     *     ResponseEntity<Map<String, Object>>: JSON response detailing files dispatched,
     *                                          timestamp, and execution status message.
     */
    @PostMapping("/trigger")
    public ResponseEntity<Map<String, Object>> triggerScan(
            @RequestParam(defaultValue = "false") boolean forceAll) {
        int dispatched = scheduler.triggerManualScan(forceAll);

        Map<String, Object> response = new HashMap<>();
        response.put("status", "success");
        response.put("filesDispatched", dispatched);
        response.put("forceAll", forceAll);
        response.put("lastScanTime", scheduler.getLastScanTime());
        response.put("message", scheduler.getLastStatus());
        return ResponseEntity.ok(response);
    }

    /**
     * Function:
     *     Exposes an HTTP GET endpoint returning real-time health telemetry, directory paths,
     *     and synchronization metrics for the Java orchestrator.
     *
     * Input:
     *     None.
     *
     * Output:
     *     ResponseEntity<Map<String, Object>>: Telemetry JSON detailing service identity,
     *                                          Python engine reachability, and total files processed.
     */
    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> getStatus() {
        Map<String, Object> status = new HashMap<>();
        status.put("service", "Java Spring Boot Orchestrator");
        status.put("targetDirectory", scannerService.resolveTargetDirectory().toString());
        status.put("pythonEngineUrl", apiClient.getPythonEngineUrl());
        status.put("pythonEngineHealthy", apiClient.isEngineHealthy());
        status.put("isScanRunning", scheduler.isScanRunning());
        status.put("lastScanTime", scheduler.getLastScanTime());
        status.put("totalDispatchedCount", scheduler.getTotalDispatchedCount());
        status.put("lastMessage", scheduler.getLastStatus());
        return ResponseEntity.ok(status);
    }

    /**
     * Function:
     *     Exposes an HTTP GET endpoint returning an inventory of all currently detected
     *     valid PDF documents residing in the monitored directory.
     *
     * Input:
     *     None.
     *
     * Output:
     *     ResponseEntity<List<DocumentPayload>>: Array of document metadata payloads.
     */
    @GetMapping("/files")
    public ResponseEntity<List<DocumentPayload>> listFiles() {
        return ResponseEntity.ok(scannerService.scanAll());
    }
}
