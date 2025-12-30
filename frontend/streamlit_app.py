import streamlit as st
import pandas as pd
import requests
from datetime import date, datetime
from typing import Dict, Any

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="The Perfect Shop - AI Operations Copilot",
    layout="wide",
    initial_sidebar_state="collapsed"  # we do NOT use Streamlit sidebar at all
)

# --------------------------------------------------
# Session state
# --------------------------------------------------
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "home"

if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None

if "csv_confirmed" not in st.session_state:
    st.session_state.csv_confirmed = False

if "show_login" not in st.session_state:
    st.session_state.show_login = False  # when True, main content becomes login screen

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "ai_insights" not in st.session_state:
    st.session_state.ai_insights = None

if "user_preferences" not in st.session_state:
    st.session_state.user_preferences = None

if "login_error" not in st.session_state:
    st.session_state.login_error = ""

# Backend API base URL
API_BASE = "http://localhost:8000"

BG_URL = "https://eu-images.contentstack.com/v3/assets/blt58a1f8f560a1ab0e/bltfedad5432e37a8b8/669f14c173512f96edb058a3/The_20Fresh_20Market-2nd_20Carmel_20IN_20store-grand_20opening-produce_20dept.jpg"

# --------------------------------------------------
# CSS (reliable background + blur via body::before)
# --------------------------------------------------
st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton+SC&display=swap');

/* Hard-disable Streamlit sidebar everywhere */
[data-testid="stSidebar"], button[data-testid="collapsedControl"] {{
    display: none !important;
}}
[data-testid="stAppViewContainer"] .main {{
    margin-left: 0 !important;
}}

/* -----------------------------
   Background + blur (reliable)
   Use body pseudo-elements, not .stApp
------------------------------ */
html, body {{
    height: 100%;
    background: #000 !important; /* fallback */
}}

.stApp {{
    background: transparent !important;
}}

/* Background image layer */
body::before {{
    content: "";
    position: fixed;
    inset: 0;
    z-index: -3;
    background-image: url("{BG_URL}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    transform: scale(1.03);
    filter: none; /* default = clean */
}}

/* Overlay tint layer */
body::after {{
    content: "";
    position: fixed;
    inset: 0;
    z-index: -2;
    background: rgba(0,0,0,0.0);
}}

/* CSV confirmed: dim slightly on home */
body.uploaded.tab-home::before {{ filter: brightness(0.60); }}
body.uploaded.tab-home::after  {{ background: rgba(0,0,0,0.25); }}

/* Any tab other than Home: blur + dark */
body.tab-inner::before {{ filter: blur(14px) brightness(0.35); }}
body.tab-inner::after  {{ background: rgba(0,0,0,0.55); }}

/* If CSV confirmed AND not Home: stronger dim */
body.uploaded.tab-inner::before {{ filter: blur(14px) brightness(0.28); }}
body.uploaded.tab-inner::after  {{ background: rgba(0,0,0,0.62); }}

/* Keep Streamlit content above overlays */
[data-testid="stAppViewContainer"] {{
    position: relative;
    z-index: 1;
}}

/* -----------------------------
   Permanent left panel (card)
   We cannot wrap Streamlit widgets inside a div, so:
   - insert a marker
   - style the column container that "has" the marker
------------------------------ */
.left-panel-marker {{ display: none !important; }}

/* The left column becomes the panel "card" */
div[data-testid="column"]:has(.left-panel-marker) {{
    position: sticky;
    top: 14px;
    margin: 14px 0 14px 14px;
    border-radius: 18px;

    height: calc(100vh - 28px);
    overflow-y: auto;
    overflow-x: hidden;

    padding: 18px 14px;
    background: rgba(0,0,0,0.92);
    backdrop-filter: blur(18px);

    border: 1px solid rgba(255,255,255,0.10);
    box-shadow: 0 20px 60px rgba(0,0,0,0.45);
}}

/* Buttons inside left panel */
div[data-testid="column"]:has(.left-panel-marker) .stButton > button {{
    background: rgba(255,255,255,0.10) !important;
    border: 1px solid rgba(255,255,255,0.20) !important;
    border-radius: 12px !important;
    color: white !important;
    backdrop-filter: blur(10px) !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}}
div[data-testid="column"]:has(.left-panel-marker) .stButton > button:hover {{
    background: rgba(255,255,255,0.20) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(0,0,0,0.30) !important;
}}
div[data-testid="column"]:has(.left-panel-marker) .stButton > button:disabled {{
    background: rgba(100,100,100,0.30) !important;
    color: rgba(255,255,255,0.40) !important;
    cursor: not-allowed !important;
}}

/* -----------------------------
   Existing UI styles (kept)
------------------------------ */
.glass-box {{
    background: rgba(0,0,0,0.40);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 50px 60px;
    max-width: 900px;
    margin: 0 auto;
    border: 1px solid rgba(255,255,255,0.10);
    box-shadow: 0 20px 60px rgba(0,0,0,0.30);
}}

.dark-container {{
    background: rgba(0,0,0,0.80);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 30px;
    margin: 20px 0;
    border: 1px solid rgba(255,255,255,0.10);
    box-shadow: 0 10px 40px rgba(0,0,0,0.50);
}}

.ai-glass-box {{
    background: rgba(0,20,40,0.80);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 30px 40px;
    margin: 20px 0;
    border: 1px solid rgba(0,150,255,0.30);
    box-shadow: 0 20px 60px rgba(0,100,200,0.20);
}}

.chat-gradient-container {{
    background: linear-gradient(135deg,
        rgba(0,20,40,0.95) 0%,
        rgba(0,40,80,0.90) 25%,
        rgba(0,60,120,0.85) 50%,
        rgba(0,40,80,0.90) 75%,
        rgba(0,20,40,0.95) 100%);
    backdrop-filter: blur(25px);
    border-radius: 20px;
    padding: 30px;
    margin: 20px 0;
    border: 1px solid rgba(0,150,255,0.30);
    box-shadow: 0 20px 60px rgba(0,100,200,0.20);
}}

.glass-title {{
    font-family: 'Anton SC', sans-serif;
    font-size: clamp(42px, 8vw, 110px);
    color: white;
    letter-spacing: 3px;
    text-shadow: 0 0 30px rgba(255,255,255,0.30);
    text-align: center;
    margin-bottom: 30px;
}}

.ai-glass-title {{
    font-family: 'Anton SC', sans-serif;
    font-size: clamp(24px, 4vw, 48px);
    color: white;
    letter-spacing: 2px;
    text-shadow: 0 0 30px rgba(0,150,255,0.60);
    text-align: center;
    margin-bottom: 20px;
}}

.glass-text {{
    color: white;
    font-size: 18px;
    text-shadow: 0 2px 10px rgba(0,0,0,0.50);
    text-align: center;
    line-height: 1.6;
}}

.ai-glass-text {{
    color: white;
    font-size: 16px;
    opacity: 0.9;
    text-shadow: 0 2px 10px rgba(0,0,0,0.50);
    text-align: center;
}}

.profile-card {{
    background: rgba(0,0,0,0.60);
    backdrop-filter: blur(15px);
    border-radius: 16px;
    padding: 20px;
    margin: 20px 0;
    border: 1px solid rgba(255,255,255,0.20);
    color: white;
}}

/* Hide Streamlit chrome */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}
</style>
""",
    unsafe_allow_html=True,
)

# --------------------------------------------------
# JS helpers (toggle BODY classes)
# --------------------------------------------------
def sync_tab_overlay_class():
    # If login is showing, treat as "inner" (blurred/darker)
    is_home = (st.session_state.current_tab == "home") and (not st.session_state.show_login)
    class_name = "tab-home" if is_home else "tab-inner"
    other = "tab-inner" if is_home else "tab-home"

    st.markdown(
        f"""
<script>
(function() {{
  const b = window.parent.document.body;
  if (!b) return;
  b.classList.remove('{other}');
  b.classList.add('{class_name}');
}})();
</script>
""",
        unsafe_allow_html=True,
    )


def sync_uploaded_class():
    if st.session_state.csv_confirmed:
        st.markdown(
            """
<script>
(function() {
  const b = window.parent.document.body;
  if (b) b.classList.add('uploaded');
})();
</script>
""",
            unsafe_allow_html=True,
        )

# --------------------------------------------------
# API Helper Functions
# --------------------------------------------------
def get_ai_insights(snapshot_date: date = None, store_id: str = None, sku_id: str = None) -> Dict[str, Any]:
    try:
        payload = {
            "snapshot_date": snapshot_date.isoformat() if snapshot_date else None,
            "store_id": store_id,
            "sku_id": sku_id,
            "top_n": 20,
        }
        response = requests.post(f"{API_BASE}/ai/insights", json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}


def send_chat_message(message: str, store_id: str = None, sku_id: str = None) -> Dict[str, Any]:
    try:
        payload = {
            "message": message,
            "store_id": store_id,
            "sku_id": sku_id,
            "snapshot_date": date.today().isoformat(),
        }
        response = requests.post(f"{API_BASE}/ai/chat", json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}


def get_user_preferences() -> Dict[str, Any]:
    try:
        response = requests.get(f"{API_BASE}/preferences/", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {
        "optimize_for": "balanced",
        "service_level_priority": "medium",
        "multi_location_aggressiveness": "medium",
    }


def update_user_preferences(preferences: Dict[str, str]) -> bool:
    try:
        response = requests.post(f"{API_BASE}/preferences/", json=preferences, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

# --------------------------------------------------
# Permanent Left Panel
# --------------------------------------------------
def render_left_panel():
    # Marker: CSS styles the entire column that contains this marker
    st.markdown('<div class="left-panel-marker"></div>', unsafe_allow_html=True)

    st.markdown("### 📂 Upload Data")
    uploaded_file = st.file_uploader("Attach CSV file", type=["csv"], key="lp_csv")

    if uploaded_file and not st.session_state.csv_confirmed:
        st.session_state.uploaded_df = pd.read_csv(uploaded_file)
        st.success("✅ CSV uploaded!")
        st.dataframe(st.session_state.uploaded_df.head(3), use_container_width=True)

        if st.button("✅ Confirm & Continue", use_container_width=True, key="lp_confirm"):
            st.session_state.csv_confirmed = True
            st.rerun()

    st.markdown("---")
    st.markdown("### 🧭 Navigation")

    nav_disabled = not st.session_state.csv_confirmed

    if st.button("🏠 Home", use_container_width=True, key="lp_home"):
        st.session_state.current_tab = "home"
        st.session_state.show_login = False
        st.session_state.login_error = ""
        st.rerun()

    if st.button("📊 Dashboard", use_container_width=True, disabled=nav_disabled, key="lp_dash"):
        st.session_state.current_tab = "dashboard"
        st.session_state.show_login = False
        st.session_state.login_error = ""
        st.rerun()

    if st.button("🤖 AI Insights", use_container_width=True, disabled=nav_disabled, key="lp_ai"):
        st.session_state.current_tab = "ai_insights"
        st.session_state.show_login = False
        st.session_state.login_error = ""
        st.rerun()

    if st.button("⚠️ Risk Analysis", use_container_width=True, disabled=nav_disabled, key="lp_risk"):
        st.session_state.current_tab = "risk_analysis"
        st.session_state.show_login = False
        st.session_state.login_error = ""
        st.rerun()

    if st.button("💬 AI Chatbot", use_container_width=True, disabled=nav_disabled, key="lp_chat"):
        st.session_state.current_tab = "ai_chatbot"
        st.session_state.show_login = False
        st.session_state.login_error = ""
        st.rerun()

    if st.button("👤 Profile", use_container_width=True, disabled=not st.session_state.logged_in, key="lp_profile"):
        st.session_state.current_tab = "profile"
        st.session_state.show_login = False
        st.session_state.login_error = ""
        st.rerun()

    st.markdown("---")

    if st.session_state.csv_confirmed:
        st.markdown("### 🤖 AI Settings")

        if st.session_state.user_preferences is None:
            st.session_state.user_preferences = get_user_preferences()

        prefs = st.session_state.user_preferences

        optimize_for = st.selectbox(
            "Optimize for:",
            ["balanced", "stability", "profit", "waste_min"],
            index=["balanced", "stability", "profit", "waste_min"].index(prefs.get("optimize_for", "balanced")),
            key="lp_optimize",
        )

        service_level = st.selectbox(
            "Service Level Priority:",
            ["low", "medium", "high"],
            index=["low", "medium", "high"].index(prefs.get("service_level_priority", "medium")),
            key="lp_service",
        )

        multi_location = st.selectbox(
            "Multi-location Aggressiveness:",
            ["low", "medium", "high"],
            index=["low", "medium", "high"].index(prefs.get("multi_location_aggressiveness", "medium")),
            key="lp_multi",
        )

        if st.button("💾 Save AI Preferences", use_container_width=True, key="lp_saveprefs"):
            new_prefs = {
                "optimize_for": optimize_for,
                "service_level_priority": service_level,
                "multi_location_aggressiveness": multi_location,
            }
            if update_user_preferences(new_prefs):
                st.session_state.user_preferences = new_prefs
                st.success("✅ Preferences saved!")
            else:
                st.error("❌ Failed to save preferences")

# --------------------------------------------------
# Tab Content
# --------------------------------------------------
def render_home_tab():
    st.markdown(
        """
<div class="glass-box">
  <div class="glass-title">THE PERFECT SHOP</div>
  <div class="glass-text">
    Welcome to your AI-powered inventory management system!
    <br><br>
    Upload your CSV file using the left panel to get started with:
    <ul style="text-align:left; max-width:500px; margin:20px auto;">
      <li>🤖 AI-Powered Risk Analysis</li>
      <li>🎯 Smart Action Recommendations</li>
      <li>💬 Conversational AI Assistant</li>
      <li>💰 Intelligent Savings Dashboard</li>
    </ul>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_dashboard_tab():
    st.markdown(
        """
<div class="dark-container">
  <div class="glass-title">💰 AI-POWERED SAVINGS DASHBOARD</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if st.session_state.uploaded_df is None:
        st.warning("Please upload a CSV file first.")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total At-Risk Value", "₹2,50,000")
    with col2:
        st.metric("AI Expected Savings", "₹1,20,000", "↑15%")
    with col3:
        st.metric("Actions Proposed", "18", "↑3")
    with col4:
        st.metric("AI Confidence", "87%")

    st.markdown(
        """
<div class="ai-glass-box">
  <div class="ai-glass-title">🔮 AI WHAT-IF SIMULATION</div>
</div>
""",
        unsafe_allow_html=True,
    )

    markdown_pct = st.slider("If we apply markdown %:", 0, 50, 20)
    expected_increase = markdown_pct * 2.5
    st.info(f"💡 **AI Prediction**: {markdown_pct}% markdown could increase sell-through by ~{expected_increase:.1f}%")


def render_ai_insights_tab():
    st.markdown(
        """
<div class="ai-glass-box">
  <div class="ai-glass-title">🤖 AI OPERATIONS COPILOT</div>
  <div class="ai-glass-text">Get AI-powered insights and action recommendations</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if st.session_state.uploaded_df is None:
        st.warning("Please upload a CSV file first.")
        return

    if st.session_state.ai_insights is None:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🤖 Get AI Insights", type="primary", use_container_width=True):
                with st.spinner("🧠 AI is analyzing your data..."):
                    insights = get_ai_insights(snapshot_date=date.today())
                    if "error" not in insights:
                        st.session_state.ai_insights = insights
                        st.success("✅ AI analysis complete!")
                        st.rerun()
                    else:
                        st.error(f"❌ AI service error: {insights['error']}")
    else:
        insights = st.session_state.ai_insights
        st.info(f"**🎯 Executive Summary:** {insights.get('executive_summary', 'Analysis completed.')}")
        if st.button("🔄 Refresh Analysis", use_container_width=True):
            st.session_state.ai_insights = None
            st.rerun()


def render_risk_analysis_tab():
    st.markdown(
        """
<div class="dark-container">
  <div class="glass-title">⚠️ RISK ANALYSIS</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if st.session_state.uploaded_df is None:
        st.warning("Please upload a CSV file first.")
        return

    df = st.session_state.uploaded_df
    risk_list = df.head(10).copy()
    risk_list["Risk Score"] = [90, 80, 95, 70, 60, 85, 75, 65, 88, 92]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ⚠️ Risk List")
        st.dataframe(risk_list, use_container_width=True)
        st.download_button("📤 Export Risk List", risk_list.to_csv(index=False), "risk_list.csv")

    with col2:
        st.markdown("### 🛠️ Action List")
        action_list = df.head(10).copy()
        action_list["Recommended Action"] = "MARKDOWN"
        action_list["Expected Savings"] = "₹500"
        st.dataframe(action_list, use_container_width=True)
        st.download_button("📤 Export Action List", action_list.to_csv(index=False), "action_list.csv")


def render_ai_chatbot_tab():
    st.markdown(
        """
<div class="chat-gradient-container">
  <div class="ai-glass-title">💬 AI ASSISTANT</div>
  <div class="ai-glass-text">Ask me anything about your inventory management</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if not st.session_state.chat_messages:
        with st.spinner("🤖 AI Assistant is connecting..."):
            hello_response = send_chat_message("Hello! Please introduce yourself.")
            if "error" not in hello_response:
                st.session_state.chat_messages.append(
                    {"role": "ai", "content": hello_response.get("response", "Hello! I'm your AI inventory assistant.")}
                )
            else:
                st.session_state.chat_messages.append(
                    {"role": "ai", "content": "Hello! I'm your AI inventory assistant. How can I help?"}
                )

    st.markdown('<div class="chat-gradient-container">', unsafe_allow_html=True)
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            st.markdown(
                f"""
<div style="background: rgba(0,100,200,0.3); padding: 15px; border-radius: 15px; margin: 10px 0;">
  <strong style="color: white;">You:</strong> <span style="color: white;">{msg['content']}</span>
</div>
""",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
<div style="background: rgba(0,0,0,0.5); padding: 15px; border-radius: 15px; margin: 10px 0;">
  <strong style="color: #00ff88;">🤖 AI:</strong> <span style="color: white;">{msg['content']}</span>
</div>
""",
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

    user_input = st.text_input("Ask me anything...", key="chat_input")
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Send 📤", key="send_chat", use_container_width=True):
            if user_input:
                st.session_state.chat_messages.append({"role": "user", "content": user_input})
                with st.spinner("🤖 AI is thinking..."):
                    response = send_chat_message(user_input)
                    if "error" not in response:
                        st.session_state.chat_messages.append(
                            {"role": "ai", "content": response.get("response", "I couldn't process that request.")}
                        )
                    else:
                        st.session_state.chat_messages.append({"role": "ai", "content": f"Error: {response['error']}"})
                st.rerun()

    with col2:
        if st.button("Clear 🗑️", key="clear_chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()


def render_profile_tab():
    st.markdown(
        """
<div class="dark-container">
  <div class="glass-title">👤 USER PROFILE</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if not st.session_state.logged_in:
        st.warning("Please log in to view your profile.")
        return

    st.markdown(
        f"""
<div class="profile-card">
  <h3>Welcome, {st.session_state.username}!</h3>
  <p><strong>Account Status:</strong> Active</p>
  <p><strong>Last Login:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
  <p><strong>CSV Files Processed:</strong> {1 if st.session_state.csv_confirmed else 0}</p>
  <p><strong>AI Insights Generated:</strong> {1 if st.session_state.ai_insights else 0}</p>
</div>
""",
        unsafe_allow_html=True,
    )

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.current_tab = "home"
        st.rerun()

# --------------------------------------------------
# Login page (KEEP AS IS)
# --------------------------------------------------
def render_login_page():
    st.markdown(
        """
<div class="glass-box">
  <div class="glass-title">LOGIN</div>
  <div class="glass-text">Enter your credentials to continue.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    left, mid, right = st.columns([1, 1.2, 1])
    with mid:
        st.markdown('<div class="dark-container">', unsafe_allow_html=True)

        if st.session_state.login_error:
            st.error(st.session_state.login_error)

        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Login", use_container_width=True):
                if username == "admin" and password == "admin123":
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.show_login = False
                    st.session_state.login_error = ""
                    st.session_state.current_tab = "home"
                    st.rerun()
                else:
                    st.session_state.login_error = "Invalid credentials"
                    st.rerun()

        with c2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_login = False
                st.session_state.login_error = ""
                st.rerun()

        st.markdown(
            """
<div style="margin-top: 16px; padding: 14px; border-radius: 14px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.15); color: white;">
  <strong>Demo Credentials</strong><br>
  Username: <code>admin</code><br>
  Password: <code>admin123</code>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------------
# Main
# --------------------------------------------------
def main():
    # Apply background classes every run
    sync_uploaded_class()
    sync_tab_overlay_class()

    # Permanent 2-column layout: left panel + content
    left_col, main_col = st.columns([0.26, 0.74], gap="small")

    with left_col:
        render_left_panel()

    with main_col:
        # If user clicked Login: replace main content with login page
        if (not st.session_state.logged_in) and st.session_state.show_login:
            render_login_page()
            return

        # Normal routing
        if st.session_state.current_tab == "home":
            render_home_tab()
        elif st.session_state.current_tab == "dashboard":
            render_dashboard_tab()
        elif st.session_state.current_tab == "ai_insights":
            render_ai_insights_tab()
        elif st.session_state.current_tab == "risk_analysis":
            render_risk_analysis_tab()
        elif st.session_state.current_tab == "ai_chatbot":
            render_ai_chatbot_tab()
        elif st.session_state.current_tab == "profile":
            render_profile_tab()

    # Login button (bottom-left) — unchanged behavior
    if not st.session_state.logged_in:
        st.markdown(
            """
<div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999;">
""",
            unsafe_allow_html=True,
        )
        if st.button("🔐 Login"):
            st.session_state.show_login = True
            st.session_state.login_error = ""
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
