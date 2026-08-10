# High-Level System Architecture: Local RAG Chatbot

## System Overview
For this project, I chose to design a polyglot microservices architecture. Instead of cramming everything into one massive application, I am separating the concerns to play to the strengths of different languages. Java handles the enterprise-level orchestration and file system monitoring, while Python handles the heavy AI computation and vector mathematics.

Crucially, the entire pipeline is air-gapped. No data ever leaves the host machine.

### System Data Flow
```mermaid
graph TD
    User((User)) -->|Authenticates & Queries| UI[Streamlit Front-End]
    UI -->|Sends Prompt| API[Python FastAPI Engine]
    
    subgraph Local File System
        Dir[data/sops/ Directory]
    </subgraph>
    
    subgraph Java Enterprise Orchestrator
        Scanner[File Scanner]
        Bridge[API Client]
    </subgraph>
    
    Dir -->|New PDF Added| Scanner
    Scanner -->|Extracts Metadata| Bridge
    Bridge -->|HTTP POST Payload| API
    
    subgraph AI Engine & Storage
        Chroma[(ChromaDB Vector Store)]
        Ollama[Ollama Local LLM]
    </subgraph>
    
    API <-->|Stores/Retrieves Vectors| Chroma
    API <-->|Prompts & Inference| Ollama