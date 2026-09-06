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
# Global Styling - Minimalist Design System
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

    /* Main Container */
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

    /* Code Blocks */
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

    /* Clean Chat Message Styling (No left gray avatar artifact) */
    div[data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 8px 0 !important;
        gap: 0 !important;
    }
    div[data-testid="stChatMessageAvatarUser"],
    div[data-testid="stChatMessageAvatarAssistant"],
    div[data-testid="chatAvatarIcon-user"],
    div[data-testid="chatAvatarIcon-assistant"] {
        display: none !important;
        width: 0 !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stChatMessageContent"] {
        padding: 0 !important;
        margin: 0 !important;
        color: #18181b !important;
        font-size: 0.94rem !important;
        line-height: 1.65 !important;
    }

    /* Bottom Chat Input Bar - Remove ALL red borders & gray left artifacts */
    div[data-testid="stChatInput"] {
        max-width: 800px !important;
        margin: 0 auto !important;
        padding: 0 !important;
    }
    div[data-testid="stChatInput"],
    div[data-testid="stChatInput"] * {
        outline: none !important;
    }
    div[data-testid="stChatInput"] > div {
        background-color: #ffffff !important;
        border: 1px solid #e4e4e7 !important;
        border-radius: 24px !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04) !important;
        padding: 2px 10px !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    div[data-testid="stChatInput"] > div:focus-within {
        border-color: #71717a !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
    }
    div[data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #18181b !important;
        font-size: 0.92rem !important;
        padding: 10px 12px !important;
    }
    div[data-testid="stChatInput"] button {
        background: transparent !important;
        border: none !important;
        color: #71717a !important;
    }
    div[data-testid="stChatInput"] button:hover {
        color: #18181b !important;
    }

    /* 3 Jumping Thinking Dots */
    .thinking-dots {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 0;
        margin: 4px 0;
    }
    .thinking-dots .dot {
        width: 7px;
        height: 7px;
        background-color: #94a3b8;
        border-radius: 50%;
        display: inline-block;
        animation: bounce-dot 1.4s infinite ease-in-out both;
    }
    .thinking-dots .dot:nth-child(1) {
        animation-delay: -0.32s;
    }
    .thinking-dots .dot:nth-child(2) {
        animation-delay: -0.16s;
    }
    .thinking-dots .dot:nth-child(3) {
        animation-delay: 0s;
    }
    @keyframes bounce-dot {
        0%, 80%, 100% {
            transform: scale(0.4);
            opacity: 0.3;
        }
        40% {
            transform: scale(1.15);
            opacity: 1;
            background-color: #18181b;
        }
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
# Login Screen Component - Strictly Compact (300px Standard)
# -----------------------------------------------------------------------------
def render_login_portal() -> None:
    """
    Renders an ultra-compact, minimalist login gateway aligned with standard login modal dimensions.
    """
    st.markdown("""
    <style>
        .dash-login-wrapper {
            max-width: 300px;
            margin: 0 auto;
        }
        .dash-brand-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 38px;
            height: 38px;
            background: #18181b;
            color: #ffffff;
            border-radius: 9px;
            margin-bottom: 10px;
            font-size: 1.05rem;
            font-weight: 700;
        }
        .dash-title {
            font-size: 1.5rem;
            font-weight: 300;
            letter-spacing: -0.03em;
            color: #09090b;
            margin-bottom: 2px;
        }
        .dash-title span {
            font-weight: 700;
        }
        .dash-subtitle {
            font-size: 0.78rem;
            color: #71717a;
            margin-bottom: 20px;
        }
        div[data-testid="stForm"] {
            max-width: 300px !important;
            margin: 0 auto !important;
            padding: 0 !important;
        }
        div[data-testid="stTextInput"] {
            max-width: 300px !important;
            margin: 0 auto 4px auto !important;
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
            font-size: 0.85rem !important;
            padding: 7px 11px !important;
            height: 36px !important;
            width: 100% !important;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: #18181b !important;
            box-shadow: 0 0 0 1px #18181b !important;
        }
        div[data-testid="stFormSubmitButton"] {
            max-width: 300px !important;
            margin: 0 auto !important;
        }
        div[data-testid="stFormSubmitButton"] button {
            background-color: #18181b !important;
            color: #ffffff !important;
            border: 1px solid #18181b !important;
            border-radius: 8px !important;
            padding: 7px 12px !important;
            font-weight: 600 !important;
            font-size: 0.85rem !important;
            margin-top: 6px !important;
            width: 100% !important;
            height: 36px !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover {
            background-color: #27272a !important;
        }
        .dash-demo-box {
            max-width: 300px;
            margin: 18px auto 0 auto;
            padding: 9px 12px;
            background: #fafafa;
            border: 1px solid #f4f4f5;
            border-radius: 8px;
            font-size: 0.70rem;
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
            font-size: 0.70rem;
        }
    </style>
    """, unsafe_allow_html=True)

    _, col_center, _ = st.columns([1.6, 1.0, 1.6])

    with col_center:
        st.markdown("<div style='height: 12vh;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="dash-login-wrapper" style="text-align: center;">
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
            <div style="font-weight: 600; color: #18181b; margin-bottom: 2px; text-transform: uppercase; font-size: 0.64rem; letter-spacing: 0.05em;">Demo Accounts</div>
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
# ChatGPT-style Input Bar & Thinking Animation Handler
# -----------------------------------------------------------------------------
user_query = st.chat_input("Message DaSH Chatbot...")

if user_query:
    st.session_state["messages"].append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        # 3 Jumping Thinking Dots Indicator
        thinking_placeholder = st.empty()
        thinking_placeholder.markdown("""
        <div class="thinking-dots">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
        </div>
        """, unsafe_allow_html=True)

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

                # Clear jumping dots and render answer
                thinking_placeholder.empty()
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
                thinking_placeholder.empty()
                err = f"API Error ({response.status_code}): {response.text}"
                st.error(err)
                st.session_state["messages"].append({"role": "assistant", "content": err, "citations": []})
        except Exception as ex:
            thinking_placeholder.empty()
            err = f"Failed to communicate with AI Engine: {str(ex)}"
            st.error(err)
            st.session_state["messages"].append({"role": "assistant", "content": err, "citations": []})
