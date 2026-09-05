package com.uoa.javaorchestrator.service;

import com.uoa.javaorchestrator.model.DocumentPayload;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;
import java.nio.file.DirectoryStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * High-performance, non-blocking File Scanner Service.
 * Leverages Java NIO DirectoryStream to efficiently monitor the target SOP directory
 * without excessive heap allocation, automatically identifying newly added or modified PDF files.
 */
@Service
public class FileScannerService {

    private static final Logger logger = LoggerFactory.getLogger(FileScannerService.class);

    @Value("${sops.directory.path:../data/sops}")
    private String targetDirectory;

    private static final String SUPPORTED_EXTENSION = ".pdf";

    // Concurrent thread-safe cache tracking canonical paths to last-modified epoch milliseconds
    private final Map<String, Long> processedFileTimestamps = new ConcurrentHashMap<>();

    /**
     * Function:
     *     Default constructor utilized by the Spring IoC container for dependency injection.
     *
     * Input:
     *     None.
     *
     * Output:
     *     None: Instantiates service with properties bound via Spring environment.
     */
    public FileScannerService() {
    }

    /**
     * Function:
     *     Parameterized constructor facilitating isolated unit testing without requiring
     *     a full Spring application context boot.
     *
     * Input:
     *     targetDirectory (String): Relative or absolute filesystem path to the target PDF folder.
     *
     * Output:
     *     None: Instantiates service targeting the specified path.
     */
    public FileScannerService(String targetDirectory) {
        this.targetDirectory = targetDirectory;
    }

    /**
     * Function:
     *     Resolves relative paths dynamically against multiple runtime execution environments
     *     (such as executing from the project root, from the sub-module directory, or within
     *     a containerized Podman mount).
     *
     * Input:
     *     None: Operates on targetDirectory instance variable and system working directory.
     *
     * Output:
     *     Path: Normalized, absolute Path object pointing to the verified directory.
     */
    public Path resolveTargetDirectory() {
        Path path = Paths.get(targetDirectory);
        if (path.isAbsolute() && Files.exists(path)) {
            return path.normalize();
        }

        Path userDir = Paths.get(System.getProperty("user.dir"));
        Path directResolution = userDir.resolve(targetDirectory).normalize();
        if (Files.exists(directResolution)) {
            return directResolution;
        }

        // Check sibling directory if running directly inside java-orchestrator submodule
        Path parent = userDir.getParent();
        if (parent != null) {
            Path siblingResolution = parent.resolve("data/sops").normalize();
            if (Files.exists(siblingResolution)) {
                return siblingResolution;
            }
        }

        return directResolution;
    }

    /**
     * Function:
     *     Scans the resolved SOP directory and returns payloads for all valid PDF documents,
     *     regardless of whether they have been previously ingested.
     *
     * Input:
     *     None: Discovers directory via resolveTargetDirectory().
     *
     * Output:
     *     List<DocumentPayload>: Complete collection of document transfer objects found.
     *                            Returns empty list if directory is unreadable or empty.
     */
    public List<DocumentPayload> scanAll() {
        Path dirPath = resolveTargetDirectory();
        return scanDirectoryInternal(dirPath, false);
    }

    /**
     * Function:
     *     Executes a high-efficiency delta scan, inspecting file modification timestamps against
     *     in-memory cache to return ONLY new or altered files. Minimizes downstream network and AI compute.
     *
     * Input:
     *     None: Compares directory state with processedFileTimestamps cache.
     *
     * Output:
     *     List<DocumentPayload>: Collection containing only new or modified document payloads.
     */
    public List<DocumentPayload> scanForChanges() {
        Path dirPath = resolveTargetDirectory();
        return scanDirectoryInternal(dirPath, true);
    }

    /**
     * Function:
     *     Scans an explicit directory path and returns all matching PDF document payloads.
     *
     * Input:
     *     pathStr (String): Target directory path string.
     *
     * Output:
     *     List<DocumentPayload>: Collection of valid PDF payloads located within the specified folder.
     */
    public List<DocumentPayload> scanDirectory(String pathStr) {
        return scanDirectoryInternal(Paths.get(pathStr), false);
    }

    /**
     * Function:
     *     Internal NIO-based scanning engine utilizing DirectoryStream for low-memory iterator traversal.
     *     Optionally filters entries based on delta modification timestamps.
     *
     * Input:
     *     dirPath (Path): Filesystem path to scan.
     *     deltaOnly (boolean): When true, excludes files whose lastModified time hasn't changed.
     *
     * Output:
     *     List<DocumentPayload>: Filtered list of DocumentPayload objects.
     */
    private List<DocumentPayload> scanDirectoryInternal(Path dirPath, boolean deltaOnly) {
        if (!Files.exists(dirPath) || !Files.isDirectory(dirPath)) {
            logger.warn("SOP storage directory is unreachable or invalid: {}", dirPath);
            return Collections.emptyList();
        }

        List<DocumentPayload> payloads = new ArrayList<>();

        // Use NIO DirectoryStream to prevent allocating large File[] arrays on the heap
        try (DirectoryStream<Path> stream = Files.newDirectoryStream(dirPath, "*.pdf")) {
            for (Path entry : stream) {
                File file = entry.toFile();
                if (isValidPdf(file)) {
                    long currentModified = file.lastModified();
                    String canonicalKey = file.getAbsolutePath();

                    if (deltaOnly) {
                        Long priorModified = processedFileTimestamps.get(canonicalKey);
                        if (priorModified == null || priorModified < currentModified) {
                            payloads.add(createPayload(file));
                            processedFileTimestamps.put(canonicalKey, currentModified);
                        }
                    } else {
                        payloads.add(createPayload(file));
                        processedFileTimestamps.put(canonicalKey, currentModified);
                    }
                }
            }
        } catch (IOException e) {
            logger.error("I/O failure while streaming directory {}: {}", dirPath, e.getMessage());
        }

        return payloads;
    }

    /**
     * Function:
     *     Validates file integrity, ensuring it represents a readable, non-empty, non-hidden PDF file.
     *
     * Input:
     *     file (File): Filesystem file handle.
     *
     * Output:
     *     boolean: True if the file meets corporate SOP document standards.
     */
    public boolean isValidPdf(File file) {
        return file != null
                && file.isFile()
                && !file.isHidden()
                && !file.getName().startsWith(".")
                && file.length() > 0
                && file.getName().toLowerCase().endsWith(SUPPORTED_EXTENSION);
    }

    /**
     * Function:
     *     Converts a verified File pointer into a serialized DocumentPayload DTO,
     *     calculating file size in kilobytes and converting timestamp to system local time.
     *
     * Input:
     *     file (File): Source file on the local filesystem.
     *
     * Output:
     *     DocumentPayload: Populated DTO ready for network dispatch.
     */
    public DocumentPayload createPayload(File file) {
        long sizeKb = Math.max(1, file.length() / 1024);
        LocalDateTime lastModTime = LocalDateTime.ofInstant(
                Instant.ofEpochMilli(file.lastModified()),
                ZoneId.systemDefault()
        );

        return new DocumentPayload(
                file.getName(),
                file.getAbsolutePath(),
                sizeKb,
                lastModTime
        );
    }

    /**
     * Function:
     *     Retrieves the configured raw target directory string.
     *
     * Input:
     *     None.
     *
     * Output:
     *     String: The configured directory path.
     */
    public String getTargetDirectory() {
        return targetDirectory;
    }

    /**
     * Function:
     *     Configures the target directory path for SOP scanning.
     *
     * Input:
     *     targetDirectory (String): Path string to set.
     *
     * Output:
     *     None.
     */
    public void setTargetDirectory(String targetDirectory) {
        this.targetDirectory = targetDirectory;
    }
}
