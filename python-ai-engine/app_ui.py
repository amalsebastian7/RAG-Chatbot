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
# Global Styling - Unified Clean Minimalist & Code Aesthetics
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

    /* Completely hide deploy button, 3-dots settings menu, toolbar, sidebar, and headers */
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
        max-width: 800px !important;
        padding-top: 1.2rem !important;
        padding-bottom: 7rem !important;
        margin: 0 auto !important;
    }

    /* Top Navigation Bar */
    .top-bar-user {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.86rem;
        font-weight: 600;
        color: #18181b;
        background: #f4f4f5;
        padding: 4px 12px;
        border-radius: 20px;
        border: 1px solid #e4e4e7;
    }
    .top-bar-dot {
        width: 7px;
        height: 7px;
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
        padding: 3px 12px !important;
        font-size: 0.78rem !important;
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
    }

    /* Subtle Superscript Citations */
    sup {
        font-size: 0.70em !important;
        color: #64748b !important;
        font-weight: 600 !important;
        vertical-align: baseline !important;
        position: relative !important;
        top: -0.45em !important;
        margin-left: 2px !important;
        margin-right: 1px !important;
        letter-spacing: -0.02em !important;
    }

    /* Code Blocks & In-line Code Snippets */
    code {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace !important;
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
        padding: 2px 6px !important;
        border-radius: 5px !important;
        font-size: 0.86em !important;
    }
    pre {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 14px 18px !important;
        margin: 10px 0 !important;
        overflow-x: auto !important;
    }
    pre code {
        background: transparent !important;
        padding: 0 !important;
        font-size: 0.88em !important;
        color: #0f172a !important;
    }

    /* Chat Messages - ChatGPT aesthetic */
    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 14px 0 !important;
        font-size: 0.94rem !important;
        line-height: 1.65 !important;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="chatAvatarIcon-user"]) {
        background-color: #f4f4f5 !important;
        border-radius: 16px !important;
        padding: 12px 18px !important;
        margin-bottom: 12px !important;
    }

    /* ChatGPT Bottom Fixed Input Bar */
    div[data-testid="stChatInput"] {
        max-width: 800px !important;
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
# Login Screen Component - Compact ChatGPT Format
# -----------------------------------------------------------------------------
def render_login_portal() -> None:
    """
    Renders an artistic, compact, plain white login gateway for DaSH Chatbot.
    """
    st.markdown("""
    <style>
        .main .block-container {
            max-width: 310px !important;
            padding-top: 14vh !important;
            padding-bottom: 6vh !important;
            margin: 0 auto !important;
        }

        .dash-brand-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            background: #18181b;
            color: #ffffff;
            border-radius: 10px;
            margin-bottom: 12px;
            font-size: 1.1rem;
            font-weight: 700;
        }

        .dash-title {
            font-size: 1.6rem;
            font-weight: 300;
            letter-spacing: -0.03em;
            color: #09090b;
            margin-bottom: 2px;
        }

        .dash-title span {
            font-weight: 700;
        }

        .dash-subtitle {
            font-size: 0.8rem;
            color: #71717a;
            margin-bottom: 22px;
        }

        /* Form Inputs - Compact Height */
        div[data-testid="stTextInput"] {
            margin-bottom: 4px;
        }
        div[data-testid="stTextInput"] label {
            color: #52525b !important;
            font-size: 0.74rem !important;
            font-weight: 600 !important;
            margin-bottom: 2px !important;
        }
        div[data-testid="stTextInput"] input {
            background-color: #ffffff !important;
            border: 1px solid #e4e4e7 !important;
            border-radius: 8px !important;
            color: #09090b !important;
            font-size: 0.86rem !important;
            padding: 8px 12px !important;
            height: 38px !important;
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
            border-radius: 8px !important;
            padding: 8px 14px !important;
            font-weight: 600 !important;
            font-size: 0.86rem !important;
            margin-top: 8px !important;
            width: 100% !important;
            height: 38px !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover {
            background-color: #27272a !important;
            border-color: #27272a !important;
        }

        /* Demo Credentials Box */
        .dash-demo-box {
            margin-top: 22px;
            padding: 10px 14px;
            background: #fafafa;
            border: 1px solid #f4f4f5;
            border-radius: 8px;
            font-size: 0.72rem;
            color: #71717a;
            line-height: 1.5;
            text-align: left;
        }
        .dash-demo-box code {
            background: #ffffff;
            color: #09090b;
            border: 1px solid #e4e4e7;
            padding: 1px 4px;
            border-radius: 4px;
            font-size: 0.72rem;
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
                st.error("Invalid credentials.")

    st.markdown("""
    <div class="dash-demo-box">
        <div style="font-weight: 600; color: #18181b; margin-bottom: 2px; text-transform: uppercase; font-size: 0.65rem; letter-spacing: 0.05em;">Demo Accounts</div>
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
# Chat Conversation History
# -----------------------------------------------------------------------------
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

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
user_query = st.chat_input("Message DaSH Chatbot...")

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

                    st.markdown(answer, unsafe_allow_html=True)

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
