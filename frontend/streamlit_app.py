import streamlit as st
import pandas as pd
import requests
import json
from datetime import date, datetime
from typing import Dict, Any, List

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="The Perfect Shop - AI Operations Copilot",
    layout="wide"
)

# --------------------------------------------------
# Session state
# --------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = 1

if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None

if "show_login" not in st.session_state:
    st.session_state.show_login = False

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "show_ai_chat" not in st.session_state:
    st.session_state.show_ai_chat = False

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "ai_insights" not in st.session_state:
    st.session_state.ai_insights = None

if "user_preferences" not in st.session_state:
    st.session_state.user_preferences = None

if "show_action_popup" not in st.session_state:
    st.session_state.show_action_popup = False

# Backend API base URL
API_BASE = "http://localhost:8000"

# --------------------------------------------------
# Custom CSS
# --------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton+SC&display=swap');

/* Background */
.stApp {
    background-image: url("https://eu-images.contentstack.com/v3/assets/blt58a1f8f560a1ab0e/bltfedad5432e37a8b8/669f14c173512f96edb058a3/The_20Fresh_20Market-2nd_20Carmel_20IN_20store-grand_20opening-produce_20dept.jpg");
    background-size: cover;
    background-position: center;
}

/* Page animation */
.page-animate {
    animation: pageFadeSlide 0.45s ease-out;
}

@keyframes pageFadeSlide {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Glass boxes */
.glass-box {
    background: rgba(0,0,0,0.35);
    backdrop-filter: blur(14px);
    border-radius: 24px;
    padding: 50px 60px;
    max-width: 900px;
}

.glass-box-sm {
    background: rgba(0,0,0,0.35);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 14px 26px;
    width: fit-content;
    margin: 0 auto 12px auto;
}

/* AI Insights Panel */
.ai-insights-panel {
    background: rgba(0,100,200,0.15);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid rgba(0,150,255,0.3);
    margin-bottom: 20px;
}

.ai-action-card {
    background: rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 15px;
    margin: 10px 0;
    border-left: 4px solid #00ff88;
}

.ai-action-high { border-left-color: #ff4444; }
.ai-action-medium { border-left-color: #ffaa00; }
.ai-action-low { border-left-color: #00ff88; }

/* Chat Interface */
.chat-container {
    background: rgba(0,0,0,0.4);
    border-radius: 16px;
    padding: 20px;
    max-height: 400px;
    overflow-y: auto;
}

.chat-message {
    margin: 10px 0;
    padding: 10px 15px;
    border-radius: 12px;
}

.chat-user {
    background: rgba(0,100,255,0.3);
    margin-left: 20px;
}

.chat-ai {
    background: rgba(0,200,100,0.3);
    margin-right: 20px;
}

/* Title */
.glass-title {
    font-family: 'Anton SC', sans-serif;
    font-size: clamp(42px, 8vw, 110px);
    color: white;
    letter-spacing: 3px;
}

/* Text */
.glass-text {
    color: white;
    font-size: 18px;
}

/* KPI chip */
.kpi-chip {
    display: inline-block;
    padding: 8px 18px;
    border-radius: 999px;
    background: rgba(255,255,255,0.12);
    color: white;
    font-weight: 600;
    margin-bottom: 12px;
}

/* Dataframe styling */
[data-testid="stDataFrame"] {
    background: rgba(15,15,15,0.85);
    border-radius: 16px;
    padding: 8px;
}

[data-testid="stDataFrame"] tbody tr:hover {
    background-color: rgba(255,196,45,0.15);
}

/* Login button */
.login-btn {
    position: fixed;
    bottom: 30px;
    left: 30px;
    z-index: 9999;
}

/* AI Chat button */
.ai-chat-btn {
    position: fixed;
    bottom: 30px;
    right: 30px;
    z-index: 9999;
}

/* Modal */
.modal-bg {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.75);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
}

.modal-box {
    background: white;
    padding: 30px;
    width: 360px;
    border-radius: 22px;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# API Helper Functions
# --------------------------------------------------
def get_ai_insights(snapshot_date: date = None, store_id: str = None, sku_id: str = None) -> Dict[str, Any]:
    """Get AI insights from backend"""
    try:
        payload = {
            "snapshot_date": snapshot_date.isoformat() if snapshot_date else None,
            "store_id": store_id,
            "sku_id": sku_id,
            "top_n": 20
        }
        response = requests.post(f"{API_BASE}/ai/insights", json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}

def send_chat_message(message: str, store_id: str = None, sku_id: str = None) -> Dict[str, Any]:
    """Send chat message to AI"""
    try:
        payload = {
            "message": message,
            "store_id": store_id,
            "sku_id": sku_id,
            "snapshot_date": date.today().isoformat()
        }
        response = requests.post(f"{API_BASE}/ai/chat", json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}

def record_feedback(recommendation_id: str, action: str, context_hash: str, action_type: str, action_parameters: Dict, risk_score: float):
    """Record user feedback"""
    try:
        payload = {
            "recommendation_id": recommendation_id,
            "action": action,
            "context_hash": context_hash,
            "action_type": action_type,
            "action_parameters": action_parameters,
            "risk_score": risk_score
        }
        response = requests.post(f"{API_BASE}/ai/feedback", json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

def get_user_preferences() -> Dict[str, Any]:
    """Get user preferences"""
    try:
        response = requests.get(f"{API_BASE}/preferences/", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "optimize_for": "balanced",
                "service_level_priority": "medium", 
                "multi_location_aggressiveness": "medium"
            }
    except:
        return {
            "optimize_for": "balanced",
            "service_level_priority": "medium",
            "multi_location_aggressiveness": "medium"
        }

def update_user_preferences(preferences: Dict[str, str]) -> bool:
    """Update user preferences"""
    try:
        response = requests.post(f"{API_BASE}/preferences/", json=preferences, timeout=10)
        return response.status_code == 200
    except:
        return False

# --------------------------------------------------
# AI Components
# --------------------------------------------------
def render_ai_insights_panel():
    """Render AI insights panel"""
    if st.session_state.ai_insights is None:
        if st.button("🤖 Get AI Insights", key="get_insights"):
            with st.spinner("Analyzing inventory data..."):
                insights = get_ai_insights(snapshot_date=date.today())
                if "error" not in insights:
                    st.session_state.ai_insights = insights
                    # Show action popup automatically
                    st.session_state.show_action_popup = True
                    st.rerun()
                else:
                    st.error(f"AI service unavailable: {insights['error']}")
        return
    
    insights = st.session_state.ai_insights
    
    st.markdown("""
    <div class="ai-insights-panel">
        <h3 style="color: white; margin-top: 0;">🤖 AI Operations Copilot</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Executive Summary
    if "executive_summary" in insights:
        st.markdown(f"**Executive Summary:** {insights['executive_summary']}")
    
    # Key Metrics
    if "key_metrics" in insights:
        metrics = insights["key_metrics"]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("At Risk Value", f"${metrics.get('total_at_risk_value', 0):,.2f}")
        with col2:
            st.metric("High Risk Batches", metrics.get('high_risk_batches', 0))
        with col3:
            st.metric("Avg Days to Expiry", f"{metrics.get('avg_days_to_expiry', 0):.1f}")
    
    # Action Summary Button
    if "prioritized_actions" in insights and insights["prioritized_actions"]:
        action_count = len(insights["prioritized_actions"])
        if st.button(f"📋 {action_count} Actions Needed - Click to Review", key="show_actions", type="primary"):
            st.session_state.show_action_popup = True
            st.rerun()
    
    if st.button("🔄 Refresh Insights", key="refresh_insights"):
        st.session_state.ai_insights = None
        st.rerun()

def render_action_popup():
    """Render action popup modal"""
    if not st.session_state.get("show_action_popup", False):
        return
    
    insights = st.session_state.ai_insights
    if not insights or "prioritized_actions" not in insights:
        return
    
    actions = insights["prioritized_actions"]
    
    # Create modal-like container
    st.markdown("""
    <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: rgba(0,0,0,0.7); z-index: 1000; display: flex; 
                align-items: center; justify-content: center;">
        <div style="background: white; padding: 30px; border-radius: 15px; 
                    max-width: 800px; max-height: 80vh; overflow-y: auto; margin: 20px;">
    """, unsafe_allow_html=True)
    
    st.markdown("# 🎯 Recommended Actions")
    st.markdown(f"**{len(actions)} actions identified** - Please review each recommendation:")
    
    # Initialize action responses if not exists
    if "action_responses" not in st.session_state:
        st.session_state.action_responses = {}
    
    for i, action in enumerate(actions):
        with st.expander(f"Action {i+1}: {action.get('action_type', 'Unknown').title()} - {action.get('priority', 'medium').title()} Priority", expanded=True):
            st.markdown(f"**Description:** {action.get('description', 'No description')}")
            st.markdown(f"**Expected Impact:** {action.get('expected_impact', 'Unknown impact')}")
            st.markdown(f"**Confidence:** {action.get('confidence', 0.5)*100:.0f}%")
            
            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 2])
            
            action_key = f"action_{i}"
            
            with col1:
                if st.button("✅ Will Consider", key=f"consider_{i}"):
                    st.session_state.action_responses[action_key] = "will_consider"
                    # Record feedback
                    record_feedback(
                        f"action_{i}_{date.today().isoformat()}",
                        "accepted",
                        f"popup_action_{i}",
                        action.get('action_type', 'unknown'),
                        action.get('parameters', {}),
                        action.get('confidence', 0.5)
                    )
                    st.success("✅ Marked as 'Will Consider'")
            
            with col2:
                if st.button("❌ Reject", key=f"reject_{i}"):
                    st.session_state.action_responses[action_key] = "rejected"
                    # Record feedback
                    record_feedback(
                        f"action_{i}_{date.today().isoformat()}",
                        "rejected",
                        f"popup_action_{i}",
                        action.get('action_type', 'unknown'),
                        action.get('parameters', {}),
                        action.get('confidence', 0.5)
                    )
                    st.error("❌ Marked as 'Rejected'")
            
            # Show current status
            current_response = st.session_state.action_responses.get(action_key)
            if current_response:
                status_color = "green" if current_response == "will_consider" else "red"
                status_text = "Will Consider" if current_response == "will_consider" else "Rejected"
                st.markdown(f"<span style='color: {status_color}; font-weight: bold;'>Status: {status_text}</span>", unsafe_allow_html=True)
    
    # Close button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Close Actions Review", key="close_popup", type="primary"):
            st.session_state.show_action_popup = False
            st.rerun()
    
    st.markdown("</div></div>", unsafe_allow_html=True)

def render_ai_chat():
    """Render AI chat interface"""
    if not st.session_state.show_ai_chat:
        return
    
    st.markdown("### 💬 AI Assistant")
    
    # Initialize chat with hello message if empty
    if not st.session_state.chat_messages:
        with st.spinner("AI Assistant is connecting..."):
            hello_response = send_chat_message("Hello! Please introduce yourself and tell me how you can help with inventory management.")
            if "error" not in hello_response:
                st.session_state.chat_messages.append({
                    "role": "ai", 
                    "content": hello_response.get("response", "Hello! I'm your AI inventory assistant. How can I help you today?")
                })
            else:
                st.session_state.chat_messages.append({
                    "role": "ai", 
                    "content": "Hello! I'm your AI inventory assistant. I can help you analyze risk data, understand inventory patterns, and suggest actions to optimize your operations. What would you like to know?"
                })
    
    # Chat history
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-message chat-user">You: {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message chat-ai">AI: {msg["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input
    user_input = st.text_input("Ask about your inventory...", key="chat_input")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Send", key="send_chat"):
            if user_input:
                # Add user message
                st.session_state.chat_messages.append({"role": "user", "content": user_input})
                
                # Get AI response
                with st.spinner("AI is thinking..."):
                    response = send_chat_message(user_input)
                    if "error" not in response:
                        ai_response = response.get("response", "I couldn't process that request.")
                        st.session_state.chat_messages.append({"role": "ai", "content": ai_response})
                    else:
                        st.session_state.chat_messages.append({"role": "ai", "content": f"Error: {response['error']}"})
                
                st.rerun()
    
    with col2:
        if st.button("Clear Chat", key="clear_chat"):
            st.session_state.chat_messages = []
            st.rerun()

def render_preferences_panel():
    """Render user preferences panel"""
    st.markdown("### ⚙️ AI Preferences")
    
    if st.session_state.user_preferences is None:
        st.session_state.user_preferences = get_user_preferences()
    
    prefs = st.session_state.user_preferences
    
    optimize_for = st.selectbox(
        "Optimize for:",
        ["balanced", "stability", "profit", "waste_min"],
        index=["balanced", "stability", "profit", "waste_min"].index(prefs.get("optimize_for", "balanced"))
    )
    
    service_level = st.selectbox(
        "Service Level Priority:",
        ["low", "medium", "high"],
        index=["low", "medium", "high"].index(prefs.get("service_level_priority", "medium"))
    )
    
    multi_location = st.selectbox(
        "Multi-location Aggressiveness:",
        ["low", "medium", "high"],
        index=["low", "medium", "high"].index(prefs.get("multi_location_aggressiveness", "medium"))
    )
    
    if st.button("Save Preferences"):
        new_prefs = {
            "optimize_for": optimize_for,
            "service_level_priority": service_level,
            "multi_location_aggressiveness": multi_location
        }
        if update_user_preferences(new_prefs):
            st.session_state.user_preferences = new_prefs
            st.success("Preferences saved!")
        else:
            st.error("Failed to save preferences")
# --------------------------------------------------
# PAGE 1 — Upload
# --------------------------------------------------
def page_upload():
    st.markdown('<div class="page-animate">', unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-box">
        <div class="glass-title">THE PERFECT SHOP</div>
        <div class="glass-text">
            Upload your inventory / sales CSV file to generate:
            <ul>
                <li>Risk List with AI Insights</li>
                <li>Smart Action Recommendations</li>
                <li>AI-Powered Savings Dashboard</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("📂 Upload Data")
        uploaded_file = st.file_uploader("Attach CSV file", type=["csv"])
        
        # AI Preferences in sidebar
        with st.expander("🤖 AI Settings"):
            render_preferences_panel()

    if uploaded_file:
        st.session_state.uploaded_df = pd.read_csv(uploaded_file)
        st.success("CSV uploaded successfully!")
        st.dataframe(st.session_state.uploaded_df.head())

        if st.button("🚀 Submit & Continue"):
            st.session_state.page = 2
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Login button
    if not st.session_state.logged_in:
        with st.container():
            st.markdown('<div class="login-btn">', unsafe_allow_html=True)
            if st.button("🔐 Login"):
                st.session_state.show_login = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# PAGE 2 — Risk & Action Lists with AI
# --------------------------------------------------
def page_risk_action():
    st.markdown('<div class="page-animate">', unsafe_allow_html=True)

    df = st.session_state.uploaded_df
    if df is None:
        st.warning("Upload CSV first.")
        return

    # AI Insights Panel at the top
    render_ai_insights_panel()
    
    # Render action popup if needed
    render_action_popup()

    # Mock data for demo (in real app, this would come from API)
    risk_list = df.head(10).copy()
    risk_list["Risk Score"] = [90,80,95,70,60,85,75,65,88,92]

    action_list = df.head(10).copy()
    action_list["Recommended Action"] = "MARKDOWN"
    action_list["Expected Savings"] = "₹500"

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="glass-box-sm"><h3 style="color:white;margin:0;">⚠️ Risk List</h3></div>', unsafe_allow_html=True)
        st.markdown('<div class="kpi-chip">🔥 High Risk Items: 6</div>', unsafe_allow_html=True)
        st.dataframe(risk_list, use_container_width=True)
        st.download_button("📤 Export Risk List", risk_list.to_csv(index=False), "risk_list.csv")

    with col2:
        st.markdown('<div class="glass-box-sm"><h3 style="color:white;margin:0;">🛠️ Action List</h3></div>', unsafe_allow_html=True)
        st.markdown('<div class="kpi-chip">💰 Est. Savings: ₹3,000</div>', unsafe_allow_html=True)
        st.dataframe(action_list, use_container_width=True)
        st.download_button("📤 Export Action List", action_list.to_csv(index=False), "action_list.csv")

    # AI Chat Interface
    if st.session_state.show_ai_chat:
        render_ai_chat()

    if st.button("➡️ Next: Dashboard"):
        st.session_state.page = 3
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # AI Chat button
    with st.container():
        st.markdown('<div class="ai-chat-btn">', unsafe_allow_html=True)
        if st.button("💬 AI Chat"):
            st.session_state.show_ai_chat = not st.session_state.show_ai_chat
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# PAGE 3 — AI-Enhanced Dashboard
# --------------------------------------------------
def page_dashboard():
    st.markdown('<div class="page-animate">', unsafe_allow_html=True)

    st.markdown('<div class="glass-box"><h1 style="color:white;">💰 AI-Powered Savings Dashboard</h1></div>', unsafe_allow_html=True)

    # Enhanced metrics with AI insights
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total At-Risk Value", "₹2,50,000")
    c2.metric("AI Expected Savings", "₹1,20,000", "↑15%")
    c3.metric("Actions Proposed", "18", "↑3")
    c4.metric("AI Confidence", "87%")

    # AI Summary
    if st.session_state.ai_insights:
        insights = st.session_state.ai_insights
        st.markdown("### 🤖 AI Executive Summary")
        st.info(insights.get("executive_summary", "AI analysis completed successfully."))
        
        # Show confidence scores
        if "confidence_scores" in insights:
            conf = insights["confidence_scores"]
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Data Quality", f"{conf.get('data_quality', 0.8)*100:.0f}%")
            with col2:
                st.metric("Recommendation Confidence", f"{conf.get('recommendation_confidence', 0.7)*100:.0f}%")

    # What-if simulation (simple demo)
    st.markdown("### 🔮 What-If Simulation")
    markdown_pct = st.slider("If we apply markdown %:", 0, 50, 20)
    expected_increase = markdown_pct * 2.5  # Simple assumption
    st.info(f"💡 **Assumption**: {markdown_pct}% markdown could increase sell-through by ~{expected_increase:.1f}% (based on historical patterns)")

    if st.button("🔁 Start Over"):
        st.session_state.page = 1
        st.session_state.uploaded_df = None
        st.session_state.ai_insights = None
        st.session_state.chat_messages = []
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# LOGIN MODAL
# --------------------------------------------------
if st.session_state.show_login:
    st.markdown("""
    <div class="modal-bg">
        <div class="modal-box">
            <h2 style="text-align:center;">🔐 Login</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.session_state.show_login = False
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")

    if st.button("Cancel"):
        st.session_state.show_login = False
        st.rerun()

# --------------------------------------------------
# Router
# --------------------------------------------------
if st.session_state.page == 1:
    page_upload()
elif st.session_state.page == 2:
    page_risk_action()
elif st.session_state.page == 3:
    page_dashboard()
