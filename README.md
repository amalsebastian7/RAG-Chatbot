{\rtf1\ansi\ansicpg1252\cocoartf2870
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;\f1\fswiss\fcharset0 Helvetica-Bold;}
{\colortbl;\red255\green255\blue255;\red0\green0\blue0;\red255\green255\blue255;\red16\green16\blue16;
\red64\green139\blue255;\red252\green125\blue209;\red83\green209\blue96;\red24\green24\blue24;\red0\green0\blue0;
\red239\green236\blue236;}
{\*\expandedcolortbl;;\cssrgb\c0\c0\c0;\cssrgb\c100000\c100000\c100000;\cssrgb\c7843\c7843\c7843;
\cssrgb\c30980\c62745\c100000;\cssrgb\c100000\c58824\c85490;\cssrgb\c37647\c83922\c45098;\cssrgb\c12157\c12157\c12157;\cssrgb\c0\c0\c0\c54902;
\cssrgb\c94902\c94118\c94118;}
{\*\listtable{\list\listtemplateid1\listhybrid{\listlevel\levelnfc23\levelnfcn23\leveljc0\leveljcn0\levelfollow0\levelstartat0\levelspace360\levelindent0{\*\levelmarker \{disc\}}{\leveltext\leveltemplateid1\'01\uc0\u8226 ;}{\levelnumbers;}\fi-360\li720\lin720 }{\listname ;}\listid1}
{\list\listtemplateid2\listhybrid{\listlevel\levelnfc23\levelnfcn23\leveljc0\leveljcn0\levelfollow0\levelstartat0\levelspace360\levelindent0{\*\levelmarker \{disc\}}{\leveltext\leveltemplateid101\'01\uc0\u8226 ;}{\levelnumbers;}\fi-360\li720\lin720 }{\listname ;}\listid2}}
{\*\listoverridetable{\listoverride\listid1\listoverridecount0\ls1}{\listoverride\listid2\listoverridecount0\ls2}}
\paperw11900\paperh16840\margl1440\margr1440\vieww17180\viewh14600\viewkind0
\deftab720
\pard\pardeftab720\qc\partightenfactor0

\f0\fs48 \cf0 \expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec2 \
\pard\pardeftab720\partightenfactor0

\fs28 \cf3 \cb4 \strokec3 <\cf5 \strokec5 h1\cf3 \strokec3  \cf6 \strokec6 align\cf3 \strokec3 =\cf7 \strokec7 "center"\cf3 \strokec3 >\uc0\u55357 \u57057 \u65039  Enterprise Local RAG Chatbot</\cf5 \strokec5 h1\cf3 \strokec3 >\
\
<\cf5 \strokec5 p\cf3 \strokec3  \cf6 \strokec6 align\cf3 \strokec3 =\cf7 \strokec7 "center"\cf3 \strokec3 >\
  <\cf5 \strokec5 img\cf3 \strokec3  \cf6 \strokec6 src\cf3 \strokec3 =\cf7 \strokec7 "https://img.shields.io/badge/Java_21-Spring_Boot-6DB33F?style=for-the-badge&logo=spring&logoColor=white"\cf3 \strokec3  \cf6 \strokec6 alt\cf3 \strokec3 =\cf7 \strokec7 "Java Spring Boot"\cf3 \strokec3  />\
  <\cf5 \strokec5 img\cf3 \strokec3  \cf6 \strokec6 src\cf3 \strokec3 =\cf7 \strokec7 "https://img.shields.io/badge/Python_3.9+-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"\cf3 \strokec3  \cf6 \strokec6 alt\cf3 \strokec3 =\cf7 \strokec7 "Python FastAPI"\cf3 \strokec3  />\
  <\cf5 \strokec5 img\cf3 \strokec3  \cf6 \strokec6 src\cf3 \strokec3 =\cf7 \strokec7 "https://img.shields.io/badge/AI-Ollama_%7C_Llama_3.1-000000?style=for-the-badge&logo=meta&logoColor=white"\cf3 \strokec3  \cf6 \strokec6 alt\cf3 \strokec3 =\cf7 \strokec7 "Ollama LLM"\cf3 \strokec3  />\
  <\cf5 \strokec5 img\cf3 \strokec3  \cf6 \strokec6 src\cf3 \strokec3 =\cf7 \strokec7 "https://img.shields.io/badge/Vector_DB-ChromaDB-FF4F00?style=for-the-badge"\cf3 \strokec3  \cf6 \strokec6 alt\cf3 \strokec3 =\cf7 \strokec7 "Chroma DB"\cf3 \strokec3  />\
</\cf5 \strokec5 p\cf3 \strokec3 >\
\
## \uc0\u55357 \u56524  Project Overview\
This repository contains a 
\f1\b **100% locally hosted, air-gapped Retrieval-Augmented Generation (RAG) system**
\f0\b0  designed to securely index and query sensitive corporate Standard Operating Procedures (SOPs). \
\
Built as a 
\f1\b **polyglot microservices architecture**
\f0\b0 , the system utilizes Java (Spring Boot) for robust enterprise file orchestration and Python (FastAPI/LangChain) for advanced AI computation and vector mathematics. No data ever leaves the host machine, guaranteeing zero data leakage to public APIs.\
\
---\
\
## \uc0\u55356 \u57303 \u65039  High-Level Polyglot Architecture\
\
The system is split into two distinct engines communicating over REST. Java monitors the file system and orchestrates the ingestion pipeline, while Python handles text chunking, embedding, and LLM inference.\
\
\pard\pardeftab720\partightenfactor0
\cf7 \strokec7 ```mermaid\
graph LR\
    subgraph UI [User Interface]\
        Streamlit[Streamlit Chat]\
    end\
\
    subgraph JavaEngine [Java Spring Boot Orchestrator]\
        Scanner[File Scanner]\
        Client[API Bridge]\
    end\
\
    subgraph PythonEngine [Python FastAPI AI Engine]\
        LangChain[LangChain Pipeline]\
        Chroma[(ChromaDB)]\
    end\
\
    subgraph Models [Ollama Local Inference]\
        Embed[nomic-embed-text]\
        LLM[llama3.1]\
    end\
\
    Dir[(Local PDFs)] -->|Scanned| Scanner\
    Scanner -->|JSON Payload| Client\
    Client -->|HTTP POST| LangChain\
    LangChain <-->|Embed & Retrieve| Chroma\
    Chroma <--> Embed\
    Streamlit <-->|Query/Response| LangChain\
    LangChain <-->|Generate Answer| LLM\
\pard\pardeftab720\partightenfactor0

\f1\b\fs36 \cf8 \cb1 \strokec8 \uc0\u55358 \u56809  Java Domain Model & UML\
\pard\pardeftab720\partightenfactor0

\f0\b0\fs24 \cf8 The Java orchestrator is built using strict Object-Oriented Programming (OOP) principles, separating data transfer objects, services, and scheduling components.\
\
\pard\pardeftab720\partightenfactor0
\cf3 \cb4 \strokec3 Code snippet\cb1 \
\pard\pardeftab720\qc\partightenfactor0

\fs48 \cf0 \strokec2 \
\
\
\
\pard\pardeftab720\partightenfactor0

\fs28 \cf3 \cb4 \strokec3 classDiagram\
    direction TB\
    class DocumentPayload \{\
        -String fileName\
        -String absolutePath\
        -long fileSizeKb\
        -LocalDateTime lastModified\
        +getFileName() String\
        +getAbsolutePath() String\
    \}\
\
    class FileScannerService \{\
        -String targetDirectory\
        -String supportedExtension\
        +scanDirectory() List~DocumentPayload~\
        -isValidPdf(File) boolean\
    \}\
\
    class PythonApiClient \{\
        -String pythonEngineUrl\
        +sendForProcessing(DocumentPayload) boolean\
        -buildHttpHeaders() HttpHeaders\
    \}\
\
    class ScanScheduler \{\
        -FileScannerService scanner\
        -PythonApiClient client\
        +executeScheduledScan() void\
    \}\
\
    ScanScheduler --> FileScannerService : Triggers\
    ScanScheduler --> PythonApiClient : Routes\
    FileScannerService --> DocumentPayload : Instantiates\
\pard\pardeftab720\partightenfactor0

\f1\b\fs36 \cf8 \cb1 \strokec8 \uc0\u55357 \u56960  Key Features\
\pard\tx220\tx720\pardeftab720\li720\fi-720\partightenfactor0
\ls1\ilvl0
\fs24 \cf8 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec8 Strict Context Grounding:
\f0\b0  The LLM is heavily prompted to prevent hallucinations. Every response explicitly cites the 
\f1\b Source Document Name
\f0\b0  and 
\f1\b Section Header
\f0\b0 .\uc0\u8232 \
\ls1\ilvl0
\f1\b \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec8 Automated Ingestion:
\f0\b0  The Java scheduler automatically detects new PDFs added to the 
\fs30 \cf9 \cb10 \strokec9 data/sops/
\fs24 \cf8 \cb1 \strokec8  directory and streams them to the AI engine.\uc0\u8232 \
\ls1\ilvl0
\f1\b \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec8 Semantic Context Chunking:
\f0\b0  Uses LangChain's 
\fs30 \cf9 \cb10 \strokec9 RecursiveCharacterTextSplitter
\fs24 \cf8 \cb1 \strokec8  (1000 tokens, 200 overlap) to ensure paragraphs are not broken mid-sentence.\uc0\u8232 \
\ls1\ilvl0
\f1\b \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec8 Secure Authentication:
\f0\b0  The Streamlit front-end requires local credential authentication before granting access to the SOP knowledge base.\uc0\u8232 \
\pard\pardeftab720\partightenfactor0

\f1\b\fs36 \cf8 \uc0\u55357 \u56514  Directory Structure\
\pard\pardeftab720\partightenfactor0

\f0\b0\fs24 \cf3 \cb4 \strokec3 Plaintext
\fs48 \cf0 \cb1 \strokec2 \
\pard\pardeftab720\qc\partightenfactor0
\cf0 \
\pard\pardeftab720\partightenfactor0

\fs28 \cf3 \cb4 \strokec3 RAG Chatbot/\
\uc0\u9500 \u9472 \u9472  data/\
\uc0\u9474    \u9492 \u9472 \u9472  sops/                  # Local dummy PDF storage \
\uc0\u9500 \u9472 \u9472  docs/                      # Architectural diagrams & specifications\
\uc0\u9500 \u9472 \u9472  evidence/                  # Jira sprint tracking and compliance logs\
\uc0\u9500 \u9472 \u9472  java-orchestrator/         # Spring Boot module (File polling & routing)\
\uc0\u9500 \u9472 \u9472  python-ai-engine/          # FastAPI module (Vector DB & LLM integration)\
\uc0\u9492 \u9472 \u9472  README.md                  # Project documentation\
\pard\pardeftab720\partightenfactor0

\f1\b\fs36 \cf8 \cb1 \strokec8 \uc0\u55357 \u56826 \u65039  Deployment Roadmap\
\pard\tx220\tx720\pardeftab720\li720\fi-720\partightenfactor0
\ls2\ilvl0
\fs24 \cf8 \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec8 Phase 1 (Current):
\f0\b0  Local development prototype on Apple Silicon (M1 MacBook Pro) leveraging Apple Metal Performance Shaders (MPS) for hardware acceleration.\uc0\u8232 \
\ls2\ilvl0
\f1\b \kerning1\expnd0\expndtw0 \outl0\strokewidth0 {\listtext	\uc0\u8226 	}\expnd0\expndtw0\kerning0
\outl0\strokewidth0 \strokec8 Phase 2 (Target):
\f0\b0  Containerized deployment using 
\f1\b Podman
\f0\b0  (rootless containers) on a dedicated Home Server (Dell OptiPlex, 32GB RAM). Remote access will be secured via a 
\f1\b Tailscale
\f0\b0  zero-config VPN tunnel.
\fs28 \cf3 \cb4 \strokec3 \
\pard\pardeftab720\partightenfactor0
\cf3 ***}