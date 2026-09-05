package com.uoa.javaorchestrator.model;

import com.fasterxml.jackson.annotation.JsonFormat;
import java.io.Serializable;
import java.time.LocalDateTime;
import java.util.Objects;

/**
 * Enterprise Data Transfer Object (DTO) encapsulating SOP document metadata.
 * Transmitted across the REST bridge to the Python AI engine for vector chunking and indexing.
 */
public class DocumentPayload implements Serializable {

    private static final long serialVersionUID = 1L;

    private String fileName;
    private String absolutePath;
    private long fileSizeKb;

    @JsonFormat(pattern = "yyyy-MM-dd'T'HH:mm:ss")
    private LocalDateTime lastModified;

    /**
     * Function:
     *     Default no-argument constructor required for standard Jackson serialization/deserialization.
     *
     * Input:
     *     None.
     *
     * Output:
     *     None: Instantiates an empty DocumentPayload instance.
     */
    public DocumentPayload() {
    }

    /**
     * Function:
     *     Constructs a fully populated DocumentPayload representing a verified SOP file on the host filesystem.
     *
     * Input:
     *     fileName (String): The base name of the file (e.g., 'SOP-001-IT-Policy.pdf').
     *     absolutePath (String): The fully-qualified canonical path on the local OS.
     *     fileSizeKb (long): Total file size computed in kilobytes.
     *     lastModified (LocalDateTime): System timestamp representing the last write/update event.
     *
     * Output:
     *     None: Instantiates an immutable-ready DocumentPayload record.
     */
    public DocumentPayload(String fileName, String absolutePath, long fileSizeKb, LocalDateTime lastModified) {
        this.fileName = fileName;
        this.absolutePath = absolutePath;
        this.fileSizeKb = fileSizeKb;
        this.lastModified = lastModified;
    }

    /**
     * Function:
     *     Retrieves the base name of the SOP document.
     *
     * Input:
     *     None.
     *
     * Output:
     *     String: The file name string.
     */
    public String getFileName() {
        return fileName;
    }

    /**
     * Function:
     *     Assigns the base name of the SOP document.
     *
     * Input:
     *     fileName (String): The file name string.
     *
     * Output:
     *     None.
     */
    public void setFileName(String fileName) {
        this.fileName = fileName;
    }

    /**
     * Function:
     *     Retrieves the absolute filesystem path to the PDF document.
     *
     * Input:
     *     None.
     *
     * Output:
     *     String: The absolute canonical path on disk.
     */
    public String getAbsolutePath() {
        return absolutePath;
    }

    /**
     * Function:
     *     Assigns the absolute filesystem path to the PDF document.
     *
     * Input:
     *     absolutePath (String): The absolute path string.
     *
     * Output:
     *     None.
     */
    public void setAbsolutePath(String absolutePath) {
        this.absolutePath = absolutePath;
    }

    /**
     * Function:
     *     Retrieves the file size in kilobytes.
     *
     * Input:
     *     None.
     *
     * Output:
     *     long: File size in kilobytes.
     */
    public long getFileSizeKb() {
        return fileSizeKb;
    }

    /**
     * Function:
     *     Assigns the file size in kilobytes.
     *
     * Input:
     *     fileSizeKb (long): File size in kilobytes.
     *
     * Output:
     *     None.
     */
    public void setFileSizeKb(long fileSizeKb) {
        this.fileSizeKb = fileSizeKb;
    }

    /**
     * Function:
     *     Retrieves the last modified timestamp of the file.
     *
     * Input:
     *     None.
     *
     * Output:
     *     LocalDateTime: The date and time the file was last updated on disk.
     */
    public LocalDateTime getLastModified() {
        return lastModified;
    }

    /**
     * Function:
     *     Assigns the last modified timestamp of the file.
     *
     * Input:
     *     lastModified (LocalDateTime): The timestamp value.
     *
     * Output:
     *     None.
     */
    public void setLastModified(LocalDateTime lastModified) {
        this.lastModified = lastModified;
    }

    /**
     * Function:
     *     Evaluates equality based on absolute path and last modified timestamp,
     *     ensuring accurate set-membership evaluation in caching and synchronization pipelines.
     *
     * Input:
     *     o (Object): Candidate object for equality comparison.
     *
     * Output:
     *     boolean: True if both instances refer to the identical file path and modification time.
     */
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        DocumentPayload that = (DocumentPayload) o;
        return fileSizeKb == that.fileSizeKb &&
                Objects.equals(fileName, that.fileName) &&
                Objects.equals(absolutePath, that.absolutePath) &&
                Objects.equals(lastModified, that.lastModified);
    }

    /**
     * Function:
     *     Generates hash code using canonical file path and modified timestamp.
     *
     * Input:
     *     None.
     *
     * Output:
     *     int: Computed integer hash code.
     */
    @Override
    public int hashCode() {
        return Objects.hash(fileName, absolutePath, fileSizeKb, lastModified);
    }

    /**
     * Function:
     *     Returns a formatted string representation of the document metadata for logging.
     *
     * Input:
     *     None.
     *
     * Output:
     *     String: Formatted representation of payload fields.
     */
    @Override
    public String toString() {
        return "DocumentPayload{" +
                "fileName='" + fileName + '\'' +
                ", absolutePath='" + absolutePath + '\'' +
                ", fileSizeKb=" + fileSizeKb +
                ", lastModified=" + lastModified +
                '}';
    }
}
