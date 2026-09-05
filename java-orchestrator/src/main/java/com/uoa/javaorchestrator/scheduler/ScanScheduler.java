package com.uoa.javaorchestrator.scheduler;

import com.uoa.javaorchestrator.client.PythonApiClient;
import com.uoa.javaorchestrator.model.DocumentPayload;
import com.uoa.javaorchestrator.service.FileScannerService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Enterprise Ingestion Scheduler coordinating automated background directory scanning.
 * Implements re-entrancy prevention locks and pre-flight health validation to guarantee
 * non-blocking, reliable pipeline operation.
 */
@Component
public class ScanScheduler {

    private static final Logger logger = LoggerFactory.getLogger(ScanScheduler.class);

    private final FileScannerService scannerService;
    private final PythonApiClient apiClient;

    private final AtomicBoolean isScanRunning = new AtomicBoolean(false);
    private final AtomicInteger totalDispatchedCount = new AtomicInteger(0);

    private volatile LocalDateTime lastScanTime;
    private volatile String lastStatus = "System Initialized. Awaiting first scheduled scan.";

    /**
     * Function:
     *     Initializes the background scheduler with core scanner and API client dependencies.
     *
     * Input:
     *     scannerService (FileScannerService): Component managing local directory polling.
     *     apiClient (PythonApiClient): Component managing HTTP communications with Python.
     *
     * Output:
     *     None: Instantiates scheduler component.
     */
    public ScanScheduler(FileScannerService scannerService, PythonApiClient apiClient) {
        this.scannerService = scannerService;
        this.apiClient = apiClient;
    }

    /**
     * Function:
     *     Executes a scheduled background polling cycle on a fixed delay timer.
     *     Guarantees single-threaded re-entrancy safety via AtomicBoolean compareAndSet.
     *     Performs a pre-flight health probe before initiating network payload transfers.
     *
     * Input:
     *     None: Automatically triggered by Spring TaskScheduler via @Scheduled annotation.
     *
     * Output:
     *     None: Updates internal status strings and metrics asynchronously.
     */
    @Scheduled(fixedDelayString = "${sops.scan.interval.ms:60000}", initialDelay = 10000)
    public void executeScheduledScan() {
        if (!isScanRunning.compareAndSet(false, true)) {
            logger.warn("Previous directory scan cycle is still executing. Skipping concurrent trigger.");
            return;
        }

        try {
            lastScanTime = LocalDateTime.now();
            logger.info("Starting automated SOP directory scan at {}", lastScanTime);

            // Verify Python engine availability before dispatching
            if (!apiClient.isEngineHealthy()) {
                lastStatus = "Scan deferred: Python AI engine is currently unreachable.";
                logger.warn(lastStatus);
                return;
            }

            List<DocumentPayload> changedDocuments = scannerService.scanForChanges();
            if (changedDocuments.isEmpty()) {
                lastStatus = "Scan completed: Knowledge base is up to date (no new/modified PDFs).";
                logger.info(lastStatus);
                return;
            }

            logger.info("Detected {} modified/new SOP document(s). Dispatched for vectorization...",
                    changedDocuments.size());

            int successfulTransfers = 0;
            for (DocumentPayload doc : changedDocuments) {
                if (apiClient.sendForProcessing(doc)) {
                    successfulTransfers++;
                    totalDispatchedCount.incrementAndGet();
                }
            }

            lastStatus = String.format("Scan completed successfully: %d/%d documents synchronized.",
                    successfulTransfers, changedDocuments.size());
            logger.info(lastStatus);

        } catch (Exception e) {
            lastStatus = "Error during scheduled scan: " + e.getMessage();
            logger.error("Unexpected failure during scheduled scan cycle", e);
        } finally {
            isScanRunning.set(false);
        }
    }

    /**
     * Function:
     *     Enables on-demand, synchronous scan execution (typically requested via the REST API or UI).
     *     Allows forcing full re-indexing of all existing documents.
     *
     * Input:
     *     forceAll (boolean): If true, bypasses delta-check and re-ingests all PDF documents.
     *
     * Output:
     *     int: The total count of document payloads successfully transmitted to Python.
     */
    public int triggerManualScan(boolean forceAll) {
        lastScanTime = LocalDateTime.now();
        logger.info("Manual ingestion scan triggered (forceAll={})", forceAll);

        if (!apiClient.isEngineHealthy()) {
            lastStatus = "Manual scan aborted: Python AI engine is offline.";
            logger.error(lastStatus);
            return 0;
        }

        List<DocumentPayload> targets = forceAll ? scannerService.scanAll() : scannerService.scanForChanges();
        int successCount = 0;

        for (DocumentPayload doc : targets) {
            if (apiClient.sendForProcessing(doc)) {
                successCount++;
                totalDispatchedCount.incrementAndGet();
            }
        }

        lastStatus = String.format("Manual scan completed: %d/%d documents dispatched.",
                successCount, targets.size());
        return successCount;
    }

    /**
     * Function:
     *     Returns the timestamp of the most recent directory scan execution.
     *
     * Input:
     *     None.
     *
     * Output:
     *     LocalDateTime: Date and time of last scan, or null if no scan has completed.
     */
    public LocalDateTime getLastScanTime() {
        return lastScanTime;
    }

    /**
     * Function:
     *     Returns the cumulative count of document payloads transmitted to the AI engine.
     *
     * Input:
     *     None.
     *
     * Output:
     *     int: Total successful transfers since application startup.
     */
    public int getTotalDispatchedCount() {
        return totalDispatchedCount.get();
    }

    /**
     * Function:
     *     Returns the latest diagnostic status message summarizing the previous scan operation.
     *
     * Input:
     *     None.
     *
     * Output:
     *     String: Operational status description.
     */
    public String getLastStatus() {
        return lastStatus;
    }

    /**
     * Function:
     *     Indicates whether an active directory scan is currently executing in the background.
     *
     * Input:
     *     None.
     *
     * Output:
     *     boolean: True if an active scan thread is running.
     */
    public boolean isScanRunning() {
        return isScanRunning.get();
    }
}
