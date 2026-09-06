import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import streamlit as st

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="DaSH Chatbot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

PYTHON_API_URL = os.getenv("PYTHON_API_URL", "http://localhost:8000")
JAVA_API_URL = os.getenv("JAVA_API_URL", "http://localhost:8080")


def create_resilient_session() -> requests.Session:
    """
    Constructs a persistent requests.Session with connection pooling and retry strategy.
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


http_session = create_resilient_session()

# -----------------------------------------------------------------------------
# Authentication State
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
            "content": "Hey, how may I help you today?",
            "citations": []
        }
    ]

# -----------------------------------------------------------------------------
# Global Styling - Unified Clean White & ChatGPT-like Interface
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

    /* Global Typography & Palette */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    
    .stApp {
        background-color: #ffffff !important;
        color: #18181b !important;
    }

    /* Completely hide deploy button, 3-dots settings menu (#MainMenu), toolbar, sidebar, and header chrome */
    #MainMenu, 
    .stDeployButton, 
    [data-testid="stDeployButton"],
    [data-testid="stToolbar"],
    [data-testid="stHeaderActionElements"],
    [data-testid="stStatusWidget"],
    header[data-testid="stHeader"],
    header,
    footer,
    [data-testid="stSidebar"], 
    [data-testid="collapsedControl"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    /* Constrain main conversation container to ChatGPT ergonomic width */
    .main .block-container {
        max-width: 820px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 7rem !important;
        margin: 0 auto !important;
    }

    /* Top Navigation Bar */
    .top-bar-user {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.88rem;
        font-weight: 600;
        color: #18181b;
        background: #f4f4f5;
        padding: 5px 12px;
        border-radius: 20px;
        border: 1px solid #e4e4e7;
    }
    .top-bar-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10b981;
    }

    /* Terminate Session Red Button */
    button[data-testid="stBaseButton-secondary"]:has(div:contains("Terminate Session")),
    div[data-testid="stButton"] button:has(p:contains("Terminate Session")) {
        background-color: #fff1f2 !important;
        color: #e11d48 !important;
        border: 1px solid #fecdd3 !important;
        border-radius: 20px !important;
        padding: 4px 14px !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        transition: all 0.15s ease !important;
        box-shadow: none !important;
        height: auto !important;
        min-height: unset !important;
    }
    button[data-testid="stBaseButton-secondary"]:has(div:contains("Terminate Session")):hover,
    div[data-testid="stButton"] button:has(p:contains("Terminate Session")):hover {
        background-color: #ffe4e6 !important;
        border-color: #fda4af !important;
        color: #be123c !important;
        transform: translateY(-1px);
    }

    /* Suggestion Grid Cards */
    .suggestion-card-btn button {
        background: #ffffff !important;
        border: 1px solid #e4e4e7 !important;
        border-radius: 12px !important;
        color: #18181b !important;
        text-align: left !important;
        padding: 14px !important;
        min-height: 88px !important;
        height: 100% !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
        transition: all 0.18s ease !important;
    }
    .suggestion-card-btn button:hover {
        background: #fafafa !important;
        border-color: #d4d4d8 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05) !important;
        transform: translateY(-2px);
    }

    /* Chat Messages - ChatGPT aesthetic */
    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 16px 0 !important;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        background-color: #f4f4f5 !important;
        border-radius: 16px !important;
        padding: 14px 18px !important;
        margin-bottom: 12px !important;
    }

    /* ChatGPT Bottom Fixed Input Bar */
    div[data-testid="stChatInput"] {
        max-width: 820px !important;
        margin: 0 auto !important;
        padding: 0 !important;
    }
    div[data-testid="stChatInput"] textarea {
        background-color: #ffffff !important;
        border: 1px solid #d4d4d8 !important;
        border-radius: 24px !important;
        color: #18181b !important;
        font-size: 0.92rem !important;
        padding: 12px 20px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stChatInput"] textarea:focus {
        border-color: #18181b !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
    }

    /* Expander / Citations */
    div[data-testid="stExpander"] {
        border: 1px solid #e4e4e7 !important;
        border-radius: 10px !important;
        background: #fafafa !important;
        box-shadow: none !important;
        margin-top: 8px !important;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Login Screen Component
# -----------------------------------------------------------------------------
def render_login_portal() -> None:
    """
    Renders an artistic, minimalist plain white login gateway for DaSH Chatbot.
    """
    st.markdown("""
    <style>
        .main .block-container {
            max-width: 380px !important;
            padding-top: 12vh !important;
            padding-bottom: 6vh !important;
            margin: 0 auto !important;
        }

        .dash-brand-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 48px;
            height: 48px;
            background: #18181b;
            color: #ffffff;
            border-radius: 14px;
            margin-bottom: 16px;
            font-size: 1.25rem;
            font-weight: 700;
        }

        .dash-title {
            font-size: 1.85rem;
            font-weight: 300;
            letter-spacing: -0.035em;
            color: #09090b;
            margin-bottom: 4px;
        }

        .dash-title span {
            font-weight: 700;
        }

        .dash-subtitle {
            font-size: 0.84rem;
            color: #71717a;
            margin-bottom: 28px;
        }

        /* Form Inputs */
        div[data-testid="stTextInput"] {
            margin-bottom: 6px;
        }
        div[data-testid="stTextInput"] label {
            color: #52525b !important;
            font-size: 0.78rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.02em !important;
        }
        div[data-testid="stTextInput"] input {
            background-color: #ffffff !important;
            border: 1px solid #e4e4e7 !important;
            border-radius: 10px !important;
            color: #09090b !important;
            font-size: 0.9rem !important;
            padding: 10px 14px !important;
            transition: all 0.15s ease-in-out !important;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #18181b !important;
            box-shadow: 0 0 0 1px #18181b !important;
        }

        /* Form Submit Button */
        div[data-testid="stFormSubmitButton"] button {
            background-color: #18181b !important;
            color: #ffffff !important;
            border: 1px solid #18181b !important;
            border-radius: 10px !important;
            padding: 10px 16px !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            margin-top: 12px !important;
            width: 100% !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover {
            background-color: #27272a !important;
            border-color: #27272a !important;
            transform: translateY(-1px);
        }

        /* Demo Credentials Box */
        .dash-demo-box {
            margin-top: 28px;
            padding: 14px 16px;
            background: #fafafa;
            border: 1px solid #f4f4f5;
            border-radius: 10px;
            font-size: 0.76rem;
            color: #71717a;
            line-height: 1.6;
            text-align: left;
        }
        .dash-demo-box code {
            background: #ffffff;
            color: #09090b;
            border: 1px solid #e4e4e7;
            padding: 1px 5px;
            border-radius: 4px;
            font-size: 0.74rem;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align: center;">
        <div class="dash-brand-icon">D</div>
        <div class="dash-title"><span>DaSH</span> Chatbot</div>
        <div class="dash-subtitle">Enter your credentials to continue</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("auth_form", border=False):
        user_input = st.text_input("Username", placeholder="e.g. admin")
        pass_input = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Log in", use_container_width=True)

        if submitted:
            if user_input in CREDENTIALS and CREDENTIALS[user_input] == pass_input:
                st.session_state["authenticated"] = True
                st.session_state["username"] = user_input
                st.rerun()
            else:
                st.error("Invalid username or password.")

    st.markdown("""
    <div class="dash-demo-box">
        <div style="font-weight: 600; color: #18181b; margin-bottom: 4px; text-transform: uppercase; font-size: 0.68rem; letter-spacing: 0.05em;">Demo Credentials</div>
        <div>Admin: <code>admin</code> / <code>sopsecure2026</code></div>
        <div>Analyst: <code>analyst</code> / <code>enterprise2026</code></div>
    </div>
    """, unsafe_allow_html=True)


if not st.session_state["authenticated"]:
    render_login_portal()
    st.stop()


# -----------------------------------------------------------------------------
# Authenticated Screen: Top Navigation Bar
# -----------------------------------------------------------------------------
col_left, col_right = st.columns([6, 2])

with col_left:
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 10px;">
        <div class="top-bar-user">
            <span class="top-bar-dot"></span>
            <span>{st.session_state['username']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_right:
    if st.button("Terminate Session", key="btn_logout", use_container_width=False):
        st.session_state["authenticated"] = False
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": "Hey, how may I help you today?",
                "citations": []
            }
        ]
        st.rerun()

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 8 Minimalist Frequent Suggestions Grid (Jira, SSMS & T-SQL)
# -----------------------------------------------------------------------------
SUGGESTIONS = [
    ("🎯 Jira JQL Queries", "Overdue SLAs & search filters", "What are standard JQL query examples for finding overdue or breached SLA tickets?"),
    ("⏱️ JSM SLA Targets", "P1, P2, P3 response & fix goals", "What are the standard SLA response and resolution times for P1, P2, and P3 tickets?"),
    ("🔄 Jira Workflows", "States, transitions & validators", "What are the standard workflow states and transition validators in enterprise Jira?"),
    ("📊 SSMS Execution Plans", "Estimated vs Actual plan metrics", "What is the difference between Estimated and Actual Execution Plans in SSMS?"),
    ("💾 SSMS Backup Recovery", "Full, Diff & Log disaster recovery", "What are the differences between Full, Differential, and Transaction Log backups in SSMS?"),
    ("🔍 SSMS Extended Events", "XEvents vs legacy Profiler", "How do Extended Events replace SQL Server Profiler for performance monitoring in SSMS?"),
    ("⚡ T-SQL Window Functions", "ROW_NUMBER, RANK & LEAD/LAG", "How do ROW_NUMBER, RANK, DENSE_RANK, and LEAD work in T-SQL queries?"),
    ("🛡️ T-SQL Transactions", "ACID, Isolation & TRY...CATCH", "How is structured error handling implemented with BEGIN TRY...CATCH and ROLLBACK in T-SQL?")
]

selected_prompt = None

# Show suggestions grid on new / fresh conversations
if len(st.session_state["messages"]) <= 1:
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # Row 1 (Cards 1 to 4)
    cols_row1 = st.columns(4)
    for idx in range(4):
        title, desc, query = SUGGESTIONS[idx]
        with cols_row1[idx]:
            st.markdown('<div class="suggestion-card-btn">', unsafe_allow_html=True)
            if st.button(f"**{title}**\n\n{desc}", key=f"sug_{idx}", use_container_width=True):
                selected_prompt = query
            st.markdown('</div>', unsafe_allow_html=True)

    # Row 2 (Cards 5 to 8)
    cols_row2 = st.columns(4)
    for idx in range(4, 8):
        title, desc, query = SUGGESTIONS[idx]
        with cols_row2[idx - 4]:
            st.markdown('<div class="suggestion-card-btn">', unsafe_allow_html=True)
            if st.button(f"**{title}**\n\n{desc}", key=f"sug_{idx}", use_container_width=True):
                selected_prompt = query
            st.markdown('</div>', unsafe_allow_html=True)
            
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Chat Conversation History
# -----------------------------------------------------------------------------
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        citations = message.get("citations", [])
        if citations:
            with st.expander(f"📚 Verified Sources & Citations ({len(citations)} references)"):
                for idx, c in enumerate(citations):
                    doc = c.get('document', 'Document')
                    section = f" -> {c.get('section')}" if c.get('section') else ""
                    page = f" -> Page {c.get('page')}" if c.get('page') else ""
                    st.markdown(f"**[{idx+1}]: {doc}{section}{page}**")
                    st.markdown(f"> *\"{c.get('snippet')}\"*")


# -----------------------------------------------------------------------------
# ChatGPT-style Input Bar & Response Handler
# -----------------------------------------------------------------------------
user_query = st.chat_input("Message DaSH Chatbot...") or selected_prompt

if user_query:
    st.session_state["messages"].append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
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
                                doc = c.get('document', 'Document')
                                section = f" -> {c.get('section')}" if c.get('section') else ""
                                page = f" -> Page {c.get('page')}" if c.get('page') else ""
                                st.markdown(f"**[{idx+1}]: {doc}{section}{page}**")
                                st.markdown(f"> *\"{c.get('snippet')}\"*")

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
