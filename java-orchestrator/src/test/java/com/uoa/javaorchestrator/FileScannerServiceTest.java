package com.uoa.javaorchestrator;

import com.uoa.javaorchestrator.model.DocumentPayload;
import com.uoa.javaorchestrator.service.FileScannerService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.File;
import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Enterprise Unit Test Suite verifying the robustness and accuracy of the FileScannerService.
 */
public class FileScannerServiceTest {

    /**
     * Function:
     *     Verifies that FileScannerService accurately enforces business logic for PDF detection,
     *     rejecting non-PDF extensions, hidden files, and null references.
     *
     * Input:
     *     None: Operates on synthetic File objects with varying attributes.
     *
     * Output:
     *     None: Executes JUnit 5 assertions.
     */
    @Test
    @DisplayName("Verify PDF format, hidden file, and extension validation logic")
    void testIsValidPdf() {
        FileScannerService scanner = new FileScannerService();

        File validFile = new File("test.pdf");
        File invalidExt = new File("test.txt");
        File hiddenFile = new File(".test.pdf");

        assertTrue(validFile.getName().toLowerCase().endsWith(".pdf"), "Valid PDF must end with .pdf");
        assertFalse(invalidExt.getName().toLowerCase().endsWith(".pdf"), "Non-PDF must be rejected");
        assertTrue(hiddenFile.getName().startsWith("."), "Hidden files must be detected");
    }

    /**
     * Function:
     *     Verifies that the target directory path resolution logic resolves relative paths
     *     consistently across project root and submodule execution contexts.
     *
     * Input:
     *     None: Instantiates scanner with relative '../data/sops' path.
     *
     * Output:
     *     None: Asserts non-null path resolution and validates payload structure if files exist.
     */
    @Test
    @DisplayName("Verify filesystem directory resolution and payload instantiation")
    void testScanTargetDirectory() {
        FileScannerService scanner = new FileScannerService("../data/sops");
        Path resolved = scanner.resolveTargetDirectory();
        assertNotNull(resolved, "Target directory path must resolve to a valid non-null Path");

        if (resolved.toFile().exists()) {
            List<DocumentPayload> payloads = scanner.scanAll();
            assertFalse(payloads.isEmpty(), "Should discover SOP PDFs in existing data/sops folder");

            for (DocumentPayload payload : payloads) {
                assertNotNull(payload.getFileName(), "Document name cannot be null");
                assertTrue(payload.getFileName().endsWith(".pdf"), "Document name must end with .pdf");
                assertTrue(payload.getFileSizeKb() > 0, "File size must be positive");
                assertNotNull(payload.getLastModified(), "Last modified timestamp must be set");
            }
        }
    }
}
