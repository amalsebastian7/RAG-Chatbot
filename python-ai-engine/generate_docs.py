import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

SOPS_DIR = "/Users/amalsebastian/Desktop/RAG Chatbot/data/sops"
os.makedirs(SOPS_DIR, exist_ok=True)

styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    'DocTitle',
    parent=styles['Heading1'],
    fontSize=22,
    leading=26,
    textColor=colors.HexColor('#0f172a'),
    spaceAfter=15
)

h1_style = ParagraphStyle(
    'DocH1',
    parent=styles['Heading2'],
    fontSize=14,
    leading=18,
    textColor=colors.HexColor('#1e293b'),
    spaceBefore=14,
    spaceAfter=8,
    keepWithNext=True
)

body_style = ParagraphStyle(
    'DocBody',
    parent=styles['Normal'],
    fontSize=9.5,
    leading=14,
    textColor=colors.HexColor('#334155'),
    spaceAfter=8
)

code_style = ParagraphStyle(
    'DocCode',
    parent=styles['Code'],
    fontSize=8.5,
    leading=12,
    textColor=colors.HexColor('#09090b'),
    backColor=colors.HexColor('#f1f5f9'),
    borderColor=colors.HexColor('#cbd5e1'),
    borderWidth=1,
    borderPadding=6,
    spaceAfter=8
)

# -----------------------------------------------------------------------------
# 1. Jira Enterprise Documentation
# -----------------------------------------------------------------------------
def build_jira_pdf():
    pdf_path = os.path.join(SOPS_DIR, "Jira-Enterprise-Documentation.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    story = []

    story.append(Paragraph("JIRA ENTERPRISE SOFTWARE & SERVICE MANAGEMENT GUIDE", title_style))
    story.append(Paragraph("Official Enterprise Operations & Agile Administration Standard", body_style))
    story.append(Spacer(1, 15))

    sections = [
        ("SECTION 1.0 JIRA ARCHITECTURE AND PROJECT SETUP", 
         """Jira is structured around hierarchical entities: Instances, Projects, Boards, Issues, and Sub-tasks. 
         Enterprise teams must adhere to company-wide naming conventions for Projects (e.g., TEAM-YYYY-PROJ).
         Project Administrators are responsible for configuring issue types, components, versions, and custom field contexts.
         Company-managed projects use shared global permission and notification schemes, whereas team-managed projects allow local custom configurations."""),

        ("SECTION 2.0 AGILE SCRUM AND KANBAN METHODOLOGY",
         """Jira Software provides dedicated Scrum and Kanban board templates.
         Scrum boards are configured with a defined sprint cadence (standard 2-week iteration). Sprints must begin with a Sprint Planning ceremony and Story Point estimation using the Fibonacci sequence (1, 2, 3, 5, 8, 13).
         Kanban boards emphasize continuous delivery and require Work-In-Progress (WIP) limits configured on each column (e.g., In Progress limit = 3 per engineer) to prevent bottlenecking."""),

        ("SECTION 3.0 JIRA QUERY LANGUAGE (JQL) SPECIFICATION",
         """JQL enables advanced searching and reporting across all indexed issues.
         Key operators include '=', '!=', 'IN', 'NOT IN', '~' (text search), 'WAS', and 'CHANGED'.
         Example JQL queries for compliance audits:
         - Critical unassigned bugs: `project = 'PROD' AND issuetype = 'Bug' AND priority = 'Highest' AND assignee is EMPTY`
         - Overdue SLA items: `project = 'ITSM' AND statusCategory != 'Done' AND 'Time to resolution' = breached()`
         - Closed in current sprint: `project = 'ENG' AND sprint in openSprints() AND status = 'Closed' ORDER BY updated DESC`"""),

        ("SECTION 4.0 WORKFLOWS, STATUSES, AND PERMISSION SCHEMES",
         """Jira workflows represent the lifecycle of an issue from creation to completion.
         Standard Enterprise Workflow states: 1. Backlog -> 2. In Analysis -> 3. In Development -> 4. Code Review -> 5. QA Verification -> 6. Deployed/Closed.
         Transitions must enforce Conditions, Validators, and Post-Functions:
         - Validator: Pull request link must be attached before moving to 'Code Review'.
         - Post-Function: Automatically assign the issue to the Reporter when status transitions to 'QA Rejected'.
         Permission schemes control access levels: Browse Projects, Create Issues, Edit Issues, Assign Issues, and Administer Projects."""),

        ("SECTION 5.0 JIRA SERVICE DESK AND SLA MANAGEMENT",
         """Jira Service Management (JSM) handles IT support tickets, incident response, and change requests.
         Service Level Agreements (SLAs) track operational compliance with time-based goals:
         - Time to first response: Priority 1 (P1) < 15 minutes, Priority 2 (P2) < 1 hour, Priority 3 (P3) < 4 hours.
         - Time to resolution: P1 < 2 hours, P2 < 8 hours, P3 < 48 hours.
         SLAs pause during statuses 'Waiting on Customer' and resume upon customer reply."""),

        ("SECTION 6.0 REST API INTEGRATION AND AUTOMATION RULES",
         """Jira REST API v3 provides endpoints for automation and enterprise tool integration.
         Base URL: `https://jira.enterprise.local/rest/api/3/`
         Authentication: HTTP Basic Authentication using API Tokens generated from user account settings.
         Common endpoints:
         - `POST /rest/api/3/issue`: Create new issue with JSON payload containing fields (project, summary, description, issuetype).
         - `GET /rest/api/3/search?jql={query}`: Execute JQL search and return paginated issue results.
         - `POST /rest/api/3/issue/{issueIdOrKey}/transitions`: Execute a workflow status transition.""")
    ]

    for heading, text in sections:
        story.append(Paragraph(heading, h1_style))
        for p in text.strip().split("\n"):
            if p.strip().startswith("-") or p.strip().startswith("`"):
                story.append(Paragraph(p.strip(), code_style))
            else:
                story.append(Paragraph(p.strip(), body_style))
        story.append(Spacer(1, 10))

    doc.build(story)
    print(f"Generated: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")


# -----------------------------------------------------------------------------
# 2. Microsoft SSMS Administration Guide
# -----------------------------------------------------------------------------
def build_ssms_pdf():
    pdf_path = os.path.join(SOPS_DIR, "Microsoft-SSMS-Administration-Guide.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    story = []

    story.append(Paragraph("MICROSOFT SQL SERVER MANAGEMENT STUDIO (SSMS) GUIDE", title_style))
    story.append(Paragraph("Database Administrator & Query Environment Operational Standards", body_style))
    story.append(Spacer(1, 15))

    sections = [
        ("SECTION 1.0 SSMS ARCHITECTURE AND CONNECTION MANAGEMENT",
         """SQL Server Management Studio (SSMS) is an integrated environment for managing SQL Server and Azure SQL databases.
         Connection Authentication modes:
         - Windows Authentication: Uses Kerberos/NTLM Active Directory tokens. Highly recommended for all production DBA tasks.
         - SQL Server Authentication: Uses server-level database logins with SHA-512 hashed passwords. Requires 'Mixed Mode' authentication.
         - Azure Active Directory (MFA / Universal): Used for cloud instances requiring two-factor interactive verification.
         Connection properties must specify Network Protocol (TCP/IP), Packet Size (4096 bytes default), and Connection Timeout (30 seconds)."""),

        ("SECTION 2.0 OBJECT EXPLORER NAVIGATION AND DATABASE ADMINISTRATION",
         """Object Explorer displays the hierarchical tree of database engine objects:
         - Databases (System Databases: master, model, msdb, tempdb; and User Databases).
         - Security (Logins, Server Roles, Credentials, Cryptographic Keys).
         - Server Objects (Backup Devices, Linked Servers, Endpoints).
         - Management (Activity Monitor, Database Mail, Maintenance Plans, Extended Events).
         - SQL Server Agent (Jobs, Alerts, Operators, Error Logs)."""),

        ("SECTION 3.0 QUERY EDITOR, PARSER, AND EXECUTION PLAN ANALYSIS",
         """The Query Editor provides IntelliSense, syntax checking, code formatting, and debugging capabilities.
         Execution Plan Diagnostics:
         - Estimated Execution Plan (Ctrl+L): Generated by the Query Optimizer without executing the query.
         - Actual Execution Plan (Ctrl+M): Includes runtime metrics (actual row count, elapsed CPU time, memory grants).
         - Key plan operators to optimize: Table Scan, Index Scan (costly on large tables), Hash Match (memory intensive), Key Lookup (indicates missing covering index), and Sort (spills to tempdb if memory grant is insufficient)."""),

        ("SECTION 4.0 BACKUP, RESTORE, AND DISASTER RECOVERY PROCEDURES",
         """Backup strategies ensure Point-In-Time recovery and zero data loss in production environments:
         - Full Database Backup: Backs up the entire database including all data files and active transaction logs.
         - Differential Backup: Captures all data pages changed since the last Full backup (uses differential bitmap).
         - Transaction Log Backup: Backs up active log records and truncates committed transactions (requires FULL recovery model).
         SSMS Disaster Recovery: Right-click database -> Tasks -> Restore -> Database -> Select Point-In-Time timeline."""),

        ("SECTION 5.0 EXTENDED EVENTS, PROFILER, AND PERFORMANCE MONITORING",
         """Extended Events (XEvents) is the modern, ultra-lightweight diagnostic system replacing legacy SQL Server Profiler.
         SSMS provides Live Data Viewer for active XEvent sessions:
         - `sqlserver.query_post_execution_showplan`: Captures actual query plans for long-running transactions.
         - `sqlserver.error_reported`: Captures server-side exceptions, fatal connection drops, and syntax errors.
         - Activity Monitor (Ctrl+Alt+A): Displays live CPU consumption, Waiting Tasks, Database I/O, and Head Blocker processes."""),

        ("SECTION 6.0 SQL SERVER AGENT JOBS AND MAINTENANCE AUTOMATION",
         """SQL Server Agent handles automated scheduled tasks, alerts, and notifications.
         Standard maintenance plan tasks configured via SSMS Maintenance Plan Wizard:
         - Check Database Integrity (`DBCC CHECKDB`): Scheduled weekly on Sundays at 02:00 AM.
         - Rebuild / Reorganize Indexes (`ALTER INDEX REBUILD`): Fragmentation > 30% requires REBUILD; 10-30% requires REORGANIZE.
         - Update Statistics (`sp_updatestats`): Ensures the Query Optimizer maintains accurate cardinality estimations.""" )
    ]

    for heading, text in sections:
        story.append(Paragraph(heading, h1_style))
        for p in text.strip().split("\n"):
            if p.strip().startswith("-") or p.strip().startswith("`"):
                story.append(Paragraph(p.strip(), code_style))
            else:
                story.append(Paragraph(p.strip(), body_style))
        story.append(Spacer(1, 10))

    doc.build(story)
    print(f"Generated: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")


# -----------------------------------------------------------------------------
# 3. Transact-SQL Language Reference
# -----------------------------------------------------------------------------
def build_tsql_pdf():
    pdf_path = os.path.join(SOPS_DIR, "Transact-SQL-Language-Reference.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    story = []

    story.append(Paragraph("TRANSACT-SQL (T-SQL) COMPREHENSIVE LANGUAGE REFERENCE", title_style))
    story.append(Paragraph("Complete Syntax, Data Manipulation, Stored Procedures, and Optimization Standard", body_style))
    story.append(Spacer(1, 15))

    sections = [
        ("SECTION 1.0 T-SQL LANGUAGE OVERVIEW AND DATA TYPES",
         """Transact-SQL (T-SQL) is Microsoft's proprietary extension for SQL Server.
         Standard Data Types:
         - Exact Numerics: `BIGINT` (8 bytes), `INT` (4 bytes), `SMALLINT` (2 bytes), `DECIMAL(p,s)` / `NUMERIC(p,s)`, `MONEY`.
         - Character Strings: `VARCHAR(n)` (non-Unicode dynamic), `NVARCHAR(n)` (Unicode UTF-16, 2 bytes per char), `VARCHAR(MAX)` (up to 2GB).
         - Date and Time: `DATETIME2` (100ns precision, recommended over legacy `DATETIME`), `DATE`, `TIME`, `DATETIMEOFFSET`.
         - Binary and Special: `VARBINARY(MAX)`, `UNIQUEIDENTIFIER` (GUID), `XML`, `JSON` (stored as NVARCHAR with `ISJSON()` validation)."""),

        ("SECTION 2.0 DATA QUERY LANGUAGE (DQL) AND ADVANCED JOINS",
         """The fundamental query syntax follows the logical execution order: FROM -> ON -> JOIN -> WHERE -> GROUP BY -> HAVING -> SELECT -> DISTINCT -> ORDER BY -> TOP/OFFSET.
         Join Types:
         - `INNER JOIN`: Returns rows where join condition matches in both tables.
         - `LEFT OUTER JOIN`: Returns all rows from left table and matched rows from right (or NULL).
         - `FULL OUTER JOIN`: Returns rows when there is a match in either table.
         - `CROSS APPLY` and `OUTER APPLY`: Invokes a table-valued function or subquery for each outer row (similar to correlated subquery with multiple column return)."""),

        ("SECTION 3.0 COMMON TABLE EXPRESSIONS (CTE) AND WINDOW FUNCTIONS",
         """Common Table Expressions (CTEs) simplify complex modular logic and recursive hierarchies.
         Syntax: `WITH CTE_Name AS (SELECT Column1, Column2 FROM TableName) SELECT * FROM CTE_Name;`
         Recursive CTEs consist of an Anchor member, `UNION ALL`, and a Recursive member referencing the CTE name.
         Window Functions compute aggregations over specified partitions without collapsing rows:
         - `ROW_NUMBER() OVER (PARTITION BY DepartmentId ORDER BY Salary DESC)`: Assigns unique sequential integers.
         - `RANK()` and `DENSE_RANK()`: Handle ties with gaps and without gaps respectively.
         - `LEAD(col, 1) OVER (...)` and `LAG(col, 1) OVER (...)`: Access following or preceding row values."""),

        ("SECTION 4.0 STORED PROCEDURES, FUNCTIONS, AND TRIGGERS",
         """Stored Procedures provide precompiled execution plans, modularity, and security separation.
         Example Stored Procedure with parameters and output:
         `CREATE PROCEDURE dbo.usp_ProcessOrder @OrderId INT, @Status NVARCHAR(50) OUTPUT AS BEGIN SET NOCOUNT ON; UPDATE Orders SET Status = @Status WHERE OrderId = @OrderId; SET @Status = 'SUCCESS'; END;`
         User-Defined Functions (UDF):
         - Scalar UDFs: Return single value. Avoid in large WHERE clauses due to row-by-row invocation penalties.
         - Inline Table-Valued Functions (iTVF): Return table variable directly; inlined by optimizer like a view.
         DML Triggers: `AFTER INSERT, UPDATE, DELETE` or `INSTEAD OF` triggers operating on virtual `inserted` and `deleted` tables."""),

        ("SECTION 5.0 TRANSACTIONS, CONCURRENCY, AND ERROR HANDLING",
         """Transactions enforce ACID guarantees (Atomicity, Consistency, Isolation, Durability).
         Transaction Syntax with Structured Exception Handling:
         `BEGIN TRY BEGIN TRANSACTION; -- Statements COMMIT TRANSACTION; END TRY BEGIN CATCH IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION; THROW; END CATCH;`
         Transaction Isolation Levels:
         - `READ UNCOMMITTED` (Dirty Reads allowed).
         - `READ COMMITTED` (Default; prevents dirty reads using shared read locks).
         - `READ COMMITTED SNAPSHOT (RCSI)`: Row-versioning in tempdb; non-blocking reads.
         - `REPEATABLE READ`: Shared locks held until end of transaction.
         - `SERIALIZABLE`: Key-range locking; highest isolation, lowest concurrency."""),

        ("SECTION 6.0 INDEXING ARCHITECTURE AND T-SQL OPTIMIZATION",
         """Indexing is critical for fast retrieval and reducing I/O bottlenecks:
         - Clustered Index: Sorts and stores data rows in the table based on their key values (one per table).
         - Non-Clustered Index: Separate structure containing index keys and row locators (pointers to heap or clustered key).
         - Covering Index (`INCLUDE` clause): Adds non-key columns to leaf level to eliminate Key Lookups.
         Best Practices for High-Performance T-SQL:
         1. Ensure predicates are SARGable (Search Argument Able): Avoid `WHERE YEAR(CreateDate) = 2026`; use `WHERE CreateDate >= '2026-01-01' AND CreateDate < '2027-01-01'`.
         2. Avoid `SELECT *`; explicitly list required column names to minimize memory grants and network traffic.
         3. Use `SET NOCOUNT ON` in stored procedures to suppress row count messages.""" )
    ]

    for heading, text in sections:
        story.append(Paragraph(heading, h1_style))
        for p in text.strip().split("\n"):
            if p.strip().startswith("-") or p.strip().startswith("`") or p.strip().startswith("1."):
                story.append(Paragraph(p.strip(), code_style))
            else:
                story.append(Paragraph(p.strip(), body_style))
        story.append(Spacer(1, 10))

    doc.build(story)
    print(f"Generated: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")

if __name__ == "__main__":
    build_jira_pdf()
    build_ssms_pdf()
    build_tsql_pdf()
