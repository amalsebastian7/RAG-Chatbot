import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import streamlit as st

# Configure layout and browser metadata
st.set_page_config(
    page_title="Enterprise Local RAG Chatbot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

PYTHON_API_URL = os.getenv("PYTHON_API_URL", "http://localhost:8000")
JAVA_API_URL = os.getenv("JAVA_API_URL", "http://localhost:8080")


def create_resilient_session() -> requests.Session:
    """
    Function:
        Constructs and configures a thread-safe requests.Session equipped with connection pooling
        and exponential backoff retry policies. Avoids socket exhaustion and reduces network latency
        for high-frequency status polling in the Streamlit runtime.

    Input:
        None: Uses system default networking parameters.

    Output:
        requests.Session: Configured HTTP session with persistent connection pooling.
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=2,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(pool_connections=10, pool_maxsize=20, max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


# Shared persistent session singleton
http_session = create_resilient_session()

# Enterprise Dark Theme Styling
st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0f172a 0%, #020617 90%);
        color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .hero-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 24px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    .hero-title {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-top: 6px;
        margin-bottom: 0;
    }
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .status-online {
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    .status-offline {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# US-01: Authentication State
# -----------------------------------------------------------------------------
CREDENTIALS = {
    "admin": "sopsecure2026",
    "analyst": "enterprise2026"
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "assistant",
            "content": "Welcome. I am your air-gapped SOP compliance assistant. All responses are derived strictly from internal policy documentation with exact source citations.",
            "citations": []
        }
    ]


def render_login_portal() -> None:
    """
    Function:
        Renders the US-01 authentication gateway, preventing unauthorized users
        from viewing or interacting with sensitive corporate SOP data.

    Input:
        None: Operates directly on Streamlit session state and form inputs.

    Output:
        None: Mutates st.session_state['authenticated'] upon successful validation.
    """
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="color: #38bdf8; margin-bottom: 4px;">🛡️ Enterprise SOP Portal</h1>
            <p style="color: #94a3b8; font-size: 0.95rem;">Air-Gapped Knowledge System (US-01 Authentication)</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("auth_form"):
            st.markdown("##### 🔐 Workplace Credentials Required")
            user_input = st.text_input("Username", placeholder="e.g., admin")
            pass_input = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Verify & Access Knowledge Base", use_container_width=True)

            if submitted:
                if user_input in CREDENTIALS and CREDENTIALS[user_input] == pass_input:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = user_input
                    st.rerun()
                else:
                    st.error("Authentication failed. Invalid username or security credentials.")

        st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.5); padding: 12px; border-radius: 8px; border: 1px solid #334155; margin-top: 16px; font-size: 0.8rem; color: #94a3b8;">
            <strong>Authorized Demo Accounts:</strong><br>
            Username: <code>admin</code> | Password: <code>sopsecure2026</code><br>
            Username: <code>analyst</code> | Password: <code>enterprise2026</code>
        </div>
        """, unsafe_allow_html=True)


if not st.session_state["authenticated"]:
    render_login_portal()
    st.stop()


# -----------------------------------------------------------------------------
# Microservice Telemetry & Remote Control
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3)
def query_python_health() -> tuple:
    """
    Function:
        Polls the Python FastAPI health diagnostic endpoint. Uses a 3-second cache
        to prevent redundant HTTP requests during frequent user clicks.

    Input:
        None: Targets configured PYTHON_API_URL.

    Output:
        tuple[bool, dict]: (is_healthy, health_metadata_dict).
    """
    try:
        r = http_session.get(f"{PYTHON_API_URL}/api/health", timeout=2)
        return r.status_code == 200, r.json()
    except Exception:
        return False, {}


@st.cache_data(ttl=3)
def query_java_status() -> tuple:
    """
    Function:
        Polls the Java Spring Boot orchestrator status endpoint to verify directory
        monitoring and ingestion telemetry. Cached for 3 seconds.

    Input:
        None: Targets configured JAVA_API_URL.

    Output:
        tuple[bool, dict]: (is_online, orchestrator_status_dict).
    """
    try:
        r = http_session.get(f"{JAVA_API_URL}/api/scan/status", timeout=2)
        return r.status_code == 200, r.json()
    except Exception:
        return False, {}


@st.cache_data(ttl=5)
def fetch_indexed_catalog() -> list:
    """
    Function:
        Retrieves the complete catalog of indexed SOP documents and chunk statistics
        from the Python AI Engine. Cached for 5 seconds.

    Input:
        None: Targets /api/documents.

    Output:
        list[dict]: Array of document metadata records.
    """
    try:
        r = http_session.get(f"{PYTHON_API_URL}/api/documents", timeout=3)
        if r.status_code == 200:
            return r.json()
        return []
    except Exception:
        return []


def trigger_orchestrator_scan(force_all: bool = True) -> tuple:
    """
    Function:
        Dispatches an on-demand instruction to the Java Spring Boot orchestrator,
        triggering an immediate filesystem re-scan and sync with Python.

    Input:
        force_all (bool): If true, forces re-ingestion of all detected files.

    Output:
        tuple[bool, dict]: (success_flag, response_payload).
    """
    try:
        r = http_session.post(
            f"{JAVA_API_URL}/api/scan/trigger?forceAll={str(force_all).lower()}",
            timeout=15
        )
        return r.status_code == 200, r.json()
    except Exception as e:
        return False, {"message": str(e)}


# -----------------------------------------------------------------------------
# Sidebar: System Architecture & Inventory
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🖥️ Polyglot Microservices")

    py_online, py_data = query_python_health()
    java_online, java_data = query_java_status()

    col_a, col_b = st.columns(2)
    with col_a:
        if py_online:
            st.markdown('<div class="status-badge status-online">● Python AI (8000)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-badge status-offline">● Python AI (Offline)</div>', unsafe_allow_html=True)
    with col_b:
        if java_online:
            st.markdown('<div class="status-badge status-online">● Java Orchestrator</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-badge status-offline">● Java (Offline)</div>', unsafe_allow_html=True)

    st.markdown("<hr style='margin: 12px 0; border-color: #334155;'>", unsafe_allow_html=True)

    st.markdown("##### 🧠 Local AI Stack")
    st.markdown("""
    - **Inference**: `llama3.1:latest` (Ollama)
    - **Vector Math**: `nomic-embed-text`
    - **Storage**: ChromaDB (Persistent Cosine)
    """)

    st.markdown("<hr style='margin: 12px 0; border-color: #334155;'>", unsafe_allow_html=True)

    st.markdown("##### 📁 Active SOP Inventory")
    catalog = fetch_indexed_catalog()
    if catalog:
        for doc in catalog:
            st.markdown(f"📄 **{doc.get('document_name')}**")
            st.caption(f"Pages: {doc.get('total_pages')} | Vector Chunks: {doc.get('chunk_count')}")
    else:
        st.caption("No SOP documents currently indexed in vector store.")

    st.markdown("<hr style='margin: 12px 0; border-color: #334155;'>", unsafe_allow_html=True)

    st.markdown("##### ⚙️ Pipeline Control")
    if st.button("🔄 Trigger Java Directory Ingestion", use_container_width=True):
        with st.spinner("Orchestrator scanning local sops folder..."):
            ok, res = trigger_orchestrator_scan(force_all=True)
            if ok:
                st.success(f"Dispatched: {res.get('message', 'Completed')}")
                # Invalidate cached catalog to reflect updates immediately
                fetch_indexed_catalog.clear()
                st.rerun()
            else:
                st.error(f"Scan failed: {res.get('message')}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption(f"Session User: **{st.session_state['username']}**")
    if st.button("🚪 Terminate Session", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["messages"] = []
        st.rerun()

# -----------------------------------------------------------------------------
# Main Chat Area
# -----------------------------------------------------------------------------
st.markdown("""
<div class="hero-card">
    <div class="hero-title">🛡️ Corporate SOP Knowledge Assistant</div>
    <div class="hero-subtitle">
        Air-gapped semantic search and verified question-answering.
        Strictly grounded in internal standard operating procedures with transparent section citations.
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("##### 💡 Suggested Compliance Queries:")
chip1, chip2, chip3 = st.columns(3)
selected_prompt = None

with chip1:
    if st.button("🔑 Password & Device Policy", use_container_width=True):
        selected_prompt = "What are the password and encryption requirements for mobile devices?"
with chip2:
    if st.button("🧪 Chemical Spill Procedure", use_container_width=True):
        selected_prompt = "What is the emergency protocol if a chemical spill occurs on the body?"
with chip3:
    if st.button("⚠️ Out-of-Scope Test", use_container_width=True):
        selected_prompt = "What is the corporate reimbursement policy for commercial astronaut training?"

# Render conversation history
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        citations = message.get("citations", [])
        if citations:
            with st.expander(f"📚 Verified Sources & Citations ({len(citations)} references)"):
                for idx, c in enumerate(citations):
                    st.markdown(f"""
                    **Citation {idx+1}: {c.get('document')}**  
                    *Page:* `{c.get('page')}` | *Section:* `{c.get('section')}` | *Cosine Distance:* `{c.get('distance', 0):.4f}`  
                    > {c.get('snippet')}
                    """)

user_query = st.chat_input("Ask a question about internal Standard Operating Procedures...") or selected_prompt

if user_query:
    st.session_state["messages"].append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Performing semantic vector retrieval & local LLM reasoning..."):
            try:
                response = http_session.post(
                    f"{PYTHON_API_URL}/api/chat",
                    json={"query": user_query, "top_k": 4},
                    timeout=90
                )

                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    citations = data.get("citations", [])

                    st.markdown(answer)

                    if citations:
                        with st.expander(f"📚 Verified Sources & Citations ({len(citations)} references)"):
                            for idx, c in enumerate(citations):
                                st.markdown(f"""
                                **Citation {idx+1}: {c.get('document')}**  
                                *Page:* `{c.get('page')}` | *Section:* `{c.get('section')}` | *Cosine Distance:* `{c.get('distance', 0):.4f}`  
                                > {c.get('snippet')}
                                """)

                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": answer,
                        "citations": citations
                    })
                else:
                    err = f"API Error ({response.status_code}): {response.text}"
                    st.error(err)
                    st.session_state["messages"].append({"role": "assistant", "content": err, "citations": []})
            except Exception as ex:
                err = f"Failed to communicate with AI Engine: {str(ex)}"
                st.error(err)
                st.session_state["messages"].append({"role": "assistant", "content": err, "citations": []})
