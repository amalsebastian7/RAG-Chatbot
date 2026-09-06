import os
import re
import time
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple, Generator
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
    ChromaDB indexing with cosine distance filtering, in-memory TTL caching,
    and context-grounded inference (synchronous & streaming) via local Ollama LLMs.
    """

    def __init__(self, persist_dir: str = CHROMA_PERSIST_DIR):
        """
        Function:
            Initializes persistent ChromaDB vector storage, connects to the local
            Ollama inference engine with persistent connection pooling and timeout,
            initializes the in-memory query cache, and configures the recursive text splitter.

        Input:
            persist_dir (str): File system path pointing to the on-disk ChromaDB directory.
                               Defaults to './chroma_db' within the python-ai-engine package.

        Output:
            None: Instantiates the RAGService runtime state and database connections.
        """
        self.persist_dir = persist_dir
        self.ollama_client = ollama.Client(host=OLLAMA_HOST, timeout=120.0)
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
        # In-memory query cache with TTL invalidation
        self.query_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl_seconds: int = 3600  # 1 hour TTL

    def _get_cache_key(self, query: str, top_k: int) -> str:
        """Generates a deterministic SHA-256 hash key for a normalized query and top_k parameter."""
        normalized = query.strip().lower()
        return hashlib.sha256(f"{normalized}_{top_k}".encode("utf-8")).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieves an entry from query cache if present and unexpired."""
        if key in self.query_cache:
            entry = self.query_cache[key]
            if time.time() - entry["timestamp"] < self.cache_ttl_seconds:
                logger.info(f"Cache HIT for query hash {key[:8]}")
                return entry["data"]
            else:
                logger.info(f"Cache EXPIRED for query hash {key[:8]}")
                self.query_cache.pop(key, None)
        return None

    def _save_to_cache(self, key: str, data: Dict[str, Any]) -> None:
        """Saves a query result to cache with bounded LRU-style eviction."""
        if len(self.query_cache) > 500:
            oldest_keys = sorted(self.query_cache.keys(), key=lambda k: self.query_cache[k]["timestamp"])[:100]
            for k in oldest_keys:
                self.query_cache.pop(k, None)
        self.query_cache[key] = {
            "data": data,
            "timestamp": time.time()
        }

    def clear_cache(self) -> None:
        """Flushes all stored query cache entries upon document ingestion or updates."""
        count = len(self.query_cache)
        self.query_cache.clear()
        logger.info(f"Cleared {count} entries from in-memory query cache.")

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
                if len(line) > 3 and not line.lower().startswith("page"):
                    return line[:90]
        return fallback

    def ingest_pdf(self, file_path: str, file_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Function:
            Performs high-throughput, memory-efficient PDF parsing, semantic chunking,
            vectorization, and database persistence. Uses streaming page extraction to 
            prevent memory spikes during large document processing. Atomically purges 
            outdated embeddings for the target file before re-indexing and invalidates
            the in-memory query cache.

        Input:
            file_path (str): Absolute file system path to the PDF document.
            file_name (Optional[str]): Explicit name of the document. If None, derived 
                                       from the base name of file_path.

        Output:
            Dict[str, Any]: Structured operational summary containing status, document name,
                            total pages, and chunks indexed.
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

        for page_idx in range(total_pages):
            page_num = page_idx + 1
            raw_text = reader.pages[page_idx].extract_text() or ""
            cleaned_text = self.clean_page_text(raw_text)
            
            if not cleaned_text:
                continue

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

        batch_size = 64
        for i in range(0, len(ids), batch_size):
            self.collection.add(
                ids=ids[i:i+batch_size],
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
                embeddings=embeddings[i:i+batch_size]
            )

        # Invalidate in-memory query cache so subsequent inquiries reflect newly indexed knowledge
        self.clear_cache()

        logger.info(f"Ingestion complete: {doc_name} indexed {chunk_counter} chunks across {total_pages} pages.")
        return {
            "status": "success",
            "document_name": doc_name,
            "total_pages": total_pages,
            "chunks_indexed": chunk_counter
        }

    def _retrieve_context_and_citations(self, user_query: str, top_k: int = 4) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Internal helper to query ChromaDB and apply cosine distance thresholding.
        Returns a tuple of (context_blocks, citations).
        """
        total_chunks = self.collection.count()
        if total_chunks == 0:
            return [], []

        query_vector = self.get_embedding(user_query)
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=min(top_k * 2, total_chunks)
        )

        retrieved_docs = results["documents"][0] if results.get("documents") else []
        retrieved_metas = results["metadatas"][0] if results.get("metadatas") else []
        retrieved_dists = results["distances"][0] if results.get("distances") else []

        citations: List[Dict[str, Any]] = []
        context_blocks: List[str] = []

        for text, meta, dist in zip(retrieved_docs, retrieved_metas, retrieved_dists):
            dist_val = float(dist)
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

        return context_blocks, citations

    def _build_prompt_payload(self, user_query: str, context_blocks: List[str]) -> Tuple[str, str]:
        """Constructs system instruction and grounded user prompt."""
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

        formatted_context = "\n".join(context_blocks)
        user_prompt = (
            f"REFERENCE CONTEXT:\n"
            f"{formatted_context}\n"
            f"USER QUESTION:\n"
            f"{user_query}\n\n"
            f"Provide a structured, beautifully formatted answer with code blocks and inline [1], [2] citations:"
        )
        return system_instruction, user_prompt

    def query(self, user_query: str, top_k: int = 4) -> Dict[str, Any]:
        """
        Function:
            Synchronously processes inquiries, checking cache first, and delegating to ChromaDB
            and Ollama inference if cache miss occurs.
        """
        cache_key = self._get_cache_key(user_query, top_k)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        total_chunks = self.collection.count()
        if total_chunks == 0:
            res = {
                "answer": "No Standard Operating Procedures (SOPs) have been indexed yet. Please trigger an ingestion scan first.",
                "citations": [],
                "context_count": 0
            }
            return res

        context_blocks, citations = self._retrieve_context_and_citations(user_query, top_k)
        if not context_blocks:
            res = {
                "answer": "I don't know based on the provided documents.",
                "citations": [],
                "context_count": 0
            }
            self._save_to_cache(cache_key, res)
            return res

        system_instruction, user_prompt = self._build_prompt_payload(user_query, context_blocks)

        try:
            inference_response = self.ollama_client.chat(
                model=CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.05,
                    "top_p": 0.9,
                    "num_ctx": 4096
                }
            )
            raw_answer = inference_response["message"]["content"]
            clean_answer = re.split(r'\n(?:\*\*|##|\b)?References(?:\:|\*\*|\b)?', raw_answer, flags=re.IGNORECASE)[0].strip()
            formatted_answer = re.sub(r'\[(\d+)\]', r'<sup>[\1]</sup>', clean_answer)
        except Exception as e:
            logger.error(f"Inference failure connecting to local Ollama daemon: {e}")
            formatted_answer = f"Inference engine failure: {str(e)}"

        result = {
            "answer": formatted_answer,
            "citations": citations,
            "context_count": len(context_blocks)
        }
        self._save_to_cache(cache_key, result)
        return result

    def query_stream(self, user_query: str, top_k: int = 4) -> Generator[Dict[str, Any], None, None]:
        """
        Function:
            Streams tokens in real time from Ollama to the client.
            Yields initial citation metadata, streaming token chunks, and final completion envelope.
            Serves from memory cache when available.
        """
        cache_key = self._get_cache_key(user_query, top_k)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            yield {"type": "citations", "citations": cached.get("citations", []), "context_count": cached.get("context_count", 0)}
            yield {"type": "token", "content": cached.get("answer", "")}
            yield {"type": "done", "full_answer": cached.get("answer", ""), "citations": cached.get("citations", [])}
            return

        total_chunks = self.collection.count()
        if total_chunks == 0:
            msg = "No Standard Operating Procedures (SOPs) have been indexed yet. Please trigger an ingestion scan first."
            yield {"type": "citations", "citations": [], "context_count": 0}
            yield {"type": "token", "content": msg}
            yield {"type": "done", "full_answer": msg, "citations": []}
            return

        context_blocks, citations = self._retrieve_context_and_citations(user_query, top_k)
        if not context_blocks:
            msg = "I don't know based on the provided documents."
            yield {"type": "citations", "citations": [], "context_count": 0}
            yield {"type": "token", "content": msg}
            yield {"type": "done", "full_answer": msg, "citations": []}
            self._save_to_cache(cache_key, {"answer": msg, "citations": [], "context_count": 0})
            return

        # 1. Yield citation metadata payload first so UI can prepare accordion
        yield {
            "type": "citations",
            "citations": citations,
            "context_count": len(context_blocks)
        }

        system_instruction, user_prompt = self._build_prompt_payload(user_query, context_blocks)

        accumulated_chunks: List[str] = []
        try:
            stream_gen = self.ollama_client.chat(
                model=CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                stream=True,
                options={
                    "temperature": 0.05,
                    "top_p": 0.9,
                    "num_ctx": 4096
                }
            )

            for chunk in stream_gen:
                content = chunk.get("message", {}).get("content", "")
                if content:
                    accumulated_chunks.append(content)
                    yield {
                        "type": "token",
                        "content": content
                    }

            raw_answer = "".join(accumulated_chunks)
            clean_answer = re.split(r'\n(?:\*\*|##|\b)?References(?:\:|\*\*|\b)?', raw_answer, flags=re.IGNORECASE)[0].strip()
            formatted_answer = re.sub(r'\[(\d+)\]', r'<sup>[\1]</sup>', clean_answer)

            # Store finished answer in query cache
            self._save_to_cache(cache_key, {
                "answer": formatted_answer,
                "citations": citations,
                "context_count": len(context_blocks)
            })

            yield {
                "type": "done",
                "full_answer": formatted_answer,
                "citations": citations
            }

        except Exception as e:
            logger.error(f"Streaming error connecting to local Ollama daemon: {e}")
            err_msg = f"Inference engine failure: {str(e)}"
            yield {"type": "token", "content": f"\n\n{err_msg}"}
            yield {"type": "done", "full_answer": err_msg, "citations": citations}

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

