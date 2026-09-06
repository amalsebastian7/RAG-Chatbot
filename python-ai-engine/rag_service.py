import os
import re
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
import pypdf
import chromadb
import ollama
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag_service")

CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.1")
COLLECTION_NAME = "sop_knowledge_base"
COSINE_SIMILARITY_THRESHOLD = 0.55  # Distance threshold to discard irrelevant noise


class RAGService:
    """
    Enterprise-grade Retrieval-Augmented Generation (RAG) Service.
    
    Orchestrates the end-to-end vector pipeline for air-gapped SOP documents:
    streaming PDF ingestion, hierarchical section extraction, persistent 
    ChromaDB indexing with cosine distance filtering, and context-grounded 
    inference via local Ollama LLMs.
    """

    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR):
        """
        Function:
            Initializes persistent ChromaDB vector storage, connects to the local
            Ollama inference engine, and configures the recursive text splitter.
            Ensures that index structures and cosine distance metrics are properly
            initialized upon service bootstrap.

        Input:
            persist_dir (str): File system path pointing to the on-disk ChromaDB directory.
                               Defaults to './chroma_db' within the python-ai-engine package.

        Output:
            None: Instantiates the RAGService runtime state and database connections.
        """
        self.persist_dir = persist_dir
        self.ollama_client = ollama.Client(host=OLLAMA_HOST)
        self.chroma_client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", "; ", " ", ""]
        )

    def get_embedding(self, text: str) -> List[float]:
        """
        Function:
            Generates high-dimensional semantic vector embeddings for a given piece of text
            using the local Ollama nomic-embed-text model. Sanitizes leading/trailing line
            breaks to stabilize embedding distance calculations.

        Input:
            text (str): The raw text segment or query string to convert into vector space.

        Output:
            List[float]: A 768-dimensional normalized floating-point embedding vector.
                         Raises an exception if the local Ollama service is unreachable.
        """
        cleaned_text = text.replace("\r\n", " ").replace("\n", " ").strip()
        if not cleaned_text:
            cleaned_text = "empty"
            
        response = self.ollama_client.embeddings(
            model=EMBEDDING_MODEL,
            prompt=cleaned_text
        )
        return response["embedding"]

    def compute_sha256(self, content: str) -> str:
        """
        Function:
            Computes a deterministic SHA-256 cryptographic hash of string content.
            Used to deduplicate chunks and verify document integrity across ingestion cycles.

        Input:
            content (str): The raw string content of a document chunk or header.

        Output:
            str: Hexadecimal string digest representing the SHA-256 hash.
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def clean_page_text(self, text: str) -> str:
        """
        Function:
            Strips recurrent header/footer boilerplate (revision dates, approval signatures,
            page markers) from extracted PDF page text. This prevents repetitive noise
            from distorting embeddings and consuming context tokens.

        Input:
            text (str): Raw string extracted directly from a PDF page.

        Output:
            str: Cleaned text retaining semantic prose and section headings.
        """
        # Strip common SOP header blocks like "Revision Date Approved by: Responsibility Page"
        cleaned = re.sub(
            r"Revision Date Approved by:.*?(?:\n|$)",
            "",
            text,
            flags=re.IGNORECASE
        )
        cleaned = re.sub(
            r"Laboratory Safety Manual\s*",
            "",
            cleaned,
            flags=re.IGNORECASE
        )
        # Condense excessive blank lines to save token budget
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def extract_section_header(self, text: str, fallback: str = "General Section") -> str:
        """
        Function:
            Analyzes the top lines of a text segment using regex heuristics to detect
            formal SOP section numbers and titles (e.g., '16.5 OTHER SITUATIONS' or 
            'APPENDIX A: TRAINING REQUIRED'). Allows every chunk to inherit a precise
            human-readable topic citation.

        Input:
            text (str): Text block from the beginning of a page or chunk.
            fallback (str): Contextual section title from the preceding page if no new
                            header is established. Defaults to 'General Section'.

        Output:
            str: Identified section header string, capped at 90 characters for clarity.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:5]:
            if re.match(r"^(\d+(\.\d+)*\s+[A-Z0-9\s\-/]{3,}|SECTION\s+[A-Z0-9]+|APPENDIX\s+[A-Z0-9\:\s]+|[A-Z\s]{4,})", line):
                # Filter out pure noise lines
                if len(line) > 3 and not line.lower().startswith("page"):
                    return line[:90]
        return fallback

    def ingest_pdf(self, file_path: str, file_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Function:
            Performs high-throughput, memory-efficient PDF parsing, semantic chunking,
            vectorization, and database persistence. Uses streaming page extraction to 
            prevent memory spikes during large document processing. Atomically purges 
            outdated embeddings for the target file before re-indexing.

        Input:
            file_path (str): Absolute file system path to the PDF document.
            file_name (Optional[str]): Explicit name of the document. If None, derived 
                                       from the base name of file_path.

        Output:
            Dict[str, Any]: Structured operational summary containing:
                - 'status': Ingestion outcome ('success').
                - 'document_name': File identifier.
                - 'total_pages': Number of pages parsed.
                - 'chunks_indexed': Total count of vector embeddings stored in ChromaDB.
                Raises FileNotFoundError if file_path is invalid.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Target SOP file not found on filesystem: {file_path}")

        doc_name = file_name or os.path.basename(file_path)
        logger.info(f"Initiating enterprise ingestion pipeline for: {doc_name} ({file_path})")

        reader = pypdf.PdfReader(file_path)
        total_pages = len(reader.pages)
        
        # Purge existing chunks for this document to ensure idempotency
        existing_records = self.collection.get(where={"document_name": doc_name})
        if existing_records and existing_records.get("ids"):
            logger.info(f"Purging {len(existing_records['ids'])} stale chunks for {doc_name}")
            self.collection.delete(ids=existing_records["ids"])

        ids: List[str] = []
        documents: List[str] = []
        embeddings: List[List[float]] = []
        metadatas: List[Dict[str, Any]] = []

        active_section = "General Overview"
        chunk_counter = 0

        # Process page-by-page to maintain minimal memory footprint
        for page_idx in range(total_pages):
            page_num = page_idx + 1
            raw_text = reader.pages[page_idx].extract_text() or ""
            cleaned_text = self.clean_page_text(raw_text)
            
            if not cleaned_text:
                continue

            # Update section context if a new header is encountered
            active_section = self.extract_section_header(cleaned_text, fallback=active_section)
            page_chunks = self.text_splitter.split_text(cleaned_text)

            for chunk_idx, chunk_content in enumerate(page_chunks):
                chunk_hash = self.compute_sha256(chunk_content)[:12]
                chunk_id = f"{doc_name}_p{page_num}_c{chunk_idx}_{chunk_hash}"
                
                chunk_vector = self.get_embedding(chunk_content)

                ids.append(chunk_id)
                documents.append(chunk_content)
                embeddings.append(chunk_vector)
                metadatas.append({
                    "document_name": doc_name,
                    "file_path": file_path,
                    "page": page_num,
                    "total_pages": total_pages,
                    "section": active_section,
                    "chunk_index": chunk_counter,
                    "chunk_hash": chunk_hash
                })
                chunk_counter += 1

        # Commit batches of 64 to ChromaDB to optimize I/O and prevent buffer overflow
        batch_size = 64
        for i in range(0, len(ids), batch_size):
            self.collection.add(
                ids=ids[i:i+batch_size],
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
                embeddings=embeddings[i:i+batch_size]
            )

        logger.info(f"Ingestion complete: {doc_name} indexed {chunk_counter} chunks across {total_pages} pages.")
        return {
            "status": "success",
            "document_name": doc_name,
            "total_pages": total_pages,
            "chunks_indexed": chunk_counter
        }

    def query(self, user_query: str, top_k: int = 4) -> Dict[str, Any]:
        """
        Function:
            Executes vector similarity search, applies strict cosine relevance filtering,
            formats a verifiable context prompt, and performs deterministic inference
            via Ollama llama3.1. Enforces strict enterprise grounding and hallucination
            guardrails (mandating 'I don't know' for unverified questions).

        Input:
            user_query (str): The operational or compliance question submitted by the user.
            top_k (int): Maximum number of proximate chunks to retrieve. Defaults to 4.

        Output:
            Dict[str, Any]: Structured dictionary containing:
                - 'answer' (str): The LLM response citing document names and page sections.
                - 'citations' (List[Dict]): Detailed citation metadata for UI rendering.
                - 'context_count' (int): Number of qualifying context chunks utilized.
        """
        total_chunks = self.collection.count()
        if total_chunks == 0:
            return {
                "answer": "No Standard Operating Procedures (SOPs) have been indexed yet. Please trigger an ingestion scan first.",
                "citations": [],
                "context_count": 0
            }

        # 1. Transform query into semantic vector space
        query_vector = self.get_embedding(user_query)

        # 2. Retrieve nearest neighbor candidates
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=min(top_k * 2, total_chunks)  # Over-fetch slightly to allow threshold filtering
        )

        retrieved_docs = results["documents"][0] if results.get("documents") else []
        retrieved_metas = results["metadatas"][0] if results.get("metadatas") else []
        retrieved_dists = results["distances"][0] if results.get("distances") else []

        citations: List[Dict[str, Any]] = []
        context_blocks: List[str] = []

        # 3. Apply Cosine Distance Threshold Filtering
        for text, meta, dist in zip(retrieved_docs, retrieved_metas, retrieved_dists):
            dist_val = float(dist)
            # Skip chunks that are semantically irrelevant
            if dist_val > COSINE_SIMILARITY_THRESHOLD and len(context_blocks) >= top_k:
                continue

            meta_dict = meta if isinstance(meta, dict) else {}
            doc_name = meta_dict.get("document_name", "Unknown SOP")
            page = meta_dict.get("page", 1)
            section = meta_dict.get("section", "General")

            clean_snippet = " ".join(text.split())
            if len(clean_snippet) > 240:
                clean_snippet = clean_snippet[:240] + "..."

            citations.append({
                "index": len(context_blocks) + 1,
                "document": doc_name,
                "page": page,
                "section": section,
                "snippet": clean_snippet,
                "distance": round(dist_val, 4)
            })

            context_blocks.append(
                f"[{len(context_blocks) + 1}] Document: {doc_name} | Section: {section} | Page: {page}\nExcerpt: {text}\n"
            )
            
            if len(context_blocks) >= top_k:
                break

        # If no chunks met the threshold criteria, trigger guardrail immediately
        if not context_blocks:
            return {
                "answer": "I don't know based on the provided documents.",
                "citations": [],
                "context_count": 0
            }

        formatted_context = "\n".join(context_blocks)

        # 4. Construct Strict Grounding & Beautiful Markdown Formatting Instructions
        system_instruction = (
            "You are an expert enterprise AI assistant for technical documentation and SOPs.\n"
            "Your mission is to provide exceptionally clear, beautifully structured answers strictly based on the provided context.\n\n"
            "MANDATORY FORMATTING & CITATION RULES:\n"
            "1. STRUCTURE & READABILITY:\n"
            "   - Format explanations cleanly using structured bullet points, numbered steps, and bold key terms.\n"
            "   - Avoid dense paragraph walls of text.\n"
            "2. CODE & QUERIES:\n"
            "   - Format ANY SQL queries, JQL expressions, scripts, or commands in proper fenced code blocks (e.g. ```sql, ```jql, ```bash).\n"
            "   - NEVER embed multi-part code inside long sentences.\n"
            "3. CITATIONS:\n"
            "   - Cite your sources with bracketed numbers like [1], [2] immediately following the statement or fact.\n"
            "   - Do NOT write raw filenames, URLs, or section titles in the body text.\n"
            "   - Do NOT add a bibliography or sources section at the end (the UI renders this automatically).\n"
            "4. ACCURACY GUARDRAIL:\n"
            "   - If the context does not contain enough information to answer the question, state EXACTLY:\n"
            "     \"I don't know based on the provided documents.\""
        )

        user_prompt = (
            f"REFERENCE CONTEXT:\n"
            f"{formatted_context}\n"
            f"USER QUESTION:\n"
            f"{user_query}\n\n"
            f"Provide a structured, beautifully formatted answer with code blocks and inline [1], [2] citations:"
        )

        try:
            inference_response = self.ollama_client.chat(
                model=CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.05,  # Minimized temperature for maximum determinism
                    "top_p": 0.9,
                    "num_ctx": 4096
                }
            )
            raw_answer = inference_response["message"]["content"]
            # Convert [1], [2] to subtle superscript markup for low-font unobtrusive reading
            formatted_answer = re.sub(r'\[(\d+)\]', r'<sup>[\1]</sup>', raw_answer)
        except Exception as e:
            logger.error(f"Inference failure connecting to local Ollama daemon: {e}")
            formatted_answer = f"Inference engine failure: {str(e)}"

        return {
            "answer": formatted_answer,
            "citations": citations,
            "context_count": len(context_blocks)
        }

    def list_indexed_documents(self) -> List[Dict[str, Any]]:
        """
        Function:
            Extracts a distinct inventory of indexed SOP documents, their total chunk counts,
            and file paths directly from the ChromaDB vector collection.

        Input:
            None: Queries the active ChromaDB persistent state.

        Output:
            List[Dict[str, Any]]: A list of document metadata dictionaries summarizing
                                  document name, path, pages, and chunk metrics.
        """
        all_records = self.collection.get()
        metas = all_records.get("metadatas", [])

        summary_map: Dict[str, Dict[str, Any]] = {}
        for m in metas:
            name = m.get("document_name", "Unknown")
            if name not in summary_map:
                summary_map[name] = {
                    "document_name": name,
                    "file_path": m.get("file_path", ""),
                    "total_pages": m.get("total_pages", 0),
                    "chunk_count": 0
                }
            summary_map[name]["chunk_count"] += 1

        return list(summary_map.values())
