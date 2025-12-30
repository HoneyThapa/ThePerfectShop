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
# Custom CSS - Enhanced with AI features
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

/* AI Glass boxes - Special styling for AI features */
.ai-glass-box {
    background: rgba(0,100,200,0.25);
    backdrop-filter: blur(14px);
    border-radius: 24px;
    padding: 30px 40px;
    margin: 20px 0;
    border: 1px solid rgba(0,150,255,0.3);
    box-shadow: 0 8px 32px rgba(0,100,200,0.2);
}

.ai-glass-box-sm {
    background: rgba(0,100,200,0.2);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 14px 26px;
    width: fit-content;
    margin: 0 auto 12px auto;
    border: 1px solid rgba(0,150,255,0.3);
}

/* AI Action cards */
.ai-action-card {
    background: rgba(255,255,255,0.1);
    backdrop-filter: blur(8px);
    border-radius: 12px;
    padding: 15px;
    margin: 10px 0;
    border-left: 4px solid #00ff88;
    transition: all 0.3s ease;
}

.ai-action-card:hover {
    background: rgba(255,255,255,0.15);
    transform: translateY(-2px);
}

.ai-action-high { border-left-color: #ff4444; }
.ai-action-medium { border-left-color: #ffaa00; }
.ai-action-low { border-left-color: #00ff88; }

/* Chat Interface */
.chat-glass-container {
    background: rgba(0,0,0,0.4);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 20px;
    margin: 20px 0;
    border: 1px solid rgba(255,255,255,0.1);
}

/* Title */
.glass-title {
    font-family: 'Anton SC', sans-serif;
    font-size: clamp(42px, 8vw, 110px);
    color: white;
    letter-spacing: 3px;
}

/* AI Title */
.ai-glass-title {
    font-family: 'Anton SC', sans-serif;
    font-size: clamp(24px, 4vw, 48px);
    color: white;
    letter-spacing: 2px;
    text-shadow: 0 0 20px rgba(0,150,255,0.5);
}

/* Text */
.glass-text {
    color: white;
    font-size: 18px;
}

.ai-glass-text {
    color: white;
    font-size: 16px;
    opacity: 0.9;
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

/* AI KPI chip */
.ai-kpi-chip {
    display: inline-block;
    padding: 8px 18px;
    border-radius: 999px;
    background: rgba(0,150,255,0.3);
    color: white;
    font-weight: 600;
    margin-bottom: 12px;
    border: 1px solid rgba(0,150,255,0.5);
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
    background: rgba(0,100,200,0.8);
    backdrop-filter: blur(10px);
    border-radius: 50px;
    padding: 15px 20px;
    border: 1px solid rgba(0,150,255,0.5);
    box-shadow: 0 4px 20px rgba(0,100,200,0.3);
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

/* AI Modal */
.ai-modal-box {
    background: rgba(0,0,0,0.9);
    backdrop-filter: blur(20px);
    padding: 40px;
    max-width: 800px;
    border-radius: 24px;
    border: 1px solid rgba(0,150,255,0.3);
    box-shadow: 0 20px 60px rgba(0,100,200,0.4);
}

/* Pulse animation for AI elements */
@keyframes aiPulse {
    0% { box-shadow: 0 0 0 0 rgba(0,150,255,0.4); }
    70% { box-shadow: 0 0 0 10px rgba(0,150,255,0); }
    100% { box-shadow: 0 0 0 0 rgba(0,150,255,0); }
}

.ai-pulse {
    animation: aiPulse 2s infinite;
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
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", f"HTTP {response.status_code}")
            except:
                error_detail = f"HTTP {response.status_code}: {response.text[:100]}"
            return {"error": f"API error: {error_detail}"}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Please try again."}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to AI service. Please check if the backend is running."}
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
            error_detail = "Unknown error"
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", f"HTTP {response.status_code}")
            except:
                error_detail = f"HTTP {response.status_code}: {response.text[:100]}"
            return {"error": f"API error: {error_detail}"}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Please try again."}
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to AI service. Please check if the backend is running."}
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
# PAGE 1 — Upload (Enhanced with AI)
# --------------------------------------------------
def page_upload():
    st.markdown('<div class="page-animate">', unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-box">
        <div class="glass-title">THE PERFECT SHOP</div>
        <div class="glass-text">
            Upload your inventory / sales CSV file to generate:
            <ul>
                <li>🤖 AI-Powered Risk Analysis</li>
                <li>🎯 Smart Action Recommendations</li>
                <li>💬 Conversational AI Assistant</li>
                <li>💰 Intelligent Savings Dashboard</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("📂 Upload Data")
        uploaded_file = st.file_uploader("Attach CSV file", type=["csv"])
        
        # AI Preferences in sidebar with glass styling
        st.markdown("---")
        st.markdown("### 🤖 AI Settings")
        
        if st.session_state.user_preferences is None:
            st.session_state.user_preferences = get_user_preferences()
        
        prefs = st.session_state.user_preferences
        
        optimize_for = st.selectbox(
            "Optimize for:",
            ["balanced", "stability", "profit", "waste_min"],
            index=["balanced", "stability", "profit", "waste_min"].index(prefs.get("optimize_for", "balanced")),
            help="Choose your optimization priority for AI recommendations"
        )
        
        service_level = st.selectbox(
            "Service Level Priority:",
            ["low", "medium", "high"],
            index=["low", "medium", "high"].index(prefs.get("service_level_priority", "medium")),
            help="Balance between service level and waste reduction"
        )
        
        multi_location = st.selectbox(
            "Multi-location Aggressiveness:",
            ["low", "medium", "high"],
            index=["low", "medium", "high"].index(prefs.get("multi_location_aggressiveness", "medium")),
            help="How aggressive should store-to-store transfers be"
        )
        
        if st.button("💾 Save AI Preferences"):
            new_prefs = {
                "optimize_for": optimize_for,
                "service_level_priority": service_level,
                "multi_location_aggressiveness": multi_location
            }
            if update_user_preferences(new_prefs):
                st.session_state.user_preferences = new_prefs
                st.success("✅ AI preferences saved!")
            else:
                st.error("❌ Failed to save preferences")

    if uploaded_file:
        st.session_state.uploaded_df = pd.read_csv(uploaded_file)
        st.success("✅ CSV uploaded successfully!")
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

    # AI Insights Panel with glass styling
    render_ai_insights_panel()

    # Traditional Risk & Action Lists
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

    if st.button("➡️ Next: Dashboard"):
        st.session_state.page = 3
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # AI Chat button with glass styling
    if not st.session_state.show_ai_chat:
        with st.container():
            st.markdown('<div class="ai-chat-btn">', unsafe_allow_html=True)
            if st.button("💬 AI Assistant"):
                st.session_state.show_ai_chat = True
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

    # AI Summary with glass styling
    if st.session_state.ai_insights:
        insights = st.session_state.ai_insights
        st.markdown("""
        <div class="ai-glass-box">
            <div class="ai-glass-title">🤖 AI EXECUTIVE SUMMARY</div>
            <div class="ai-glass-text">
        """, unsafe_allow_html=True)
        st.info(insights.get("executive_summary", "AI analysis completed successfully."))
        st.markdown('</div></div>', unsafe_allow_html=True)
        
        # Show confidence scores
        if "confidence_scores" in insights:
            conf = insights["confidence_scores"]
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Data Quality", f"{conf.get('data_quality', 0.8)*100:.0f}%")
            with col2:
                st.metric("Recommendation Confidence", f"{conf.get('recommendation_confidence', 0.7)*100:.0f}%")

    # What-if simulation with glass styling
    st.markdown("""
    <div class="ai-glass-box">
        <div class="ai-glass-title">🔮 AI WHAT-IF SIMULATION</div>
    </div>
    """, unsafe_allow_html=True)
    
    markdown_pct = st.slider("If we apply markdown %:", 0, 50, 20)
    expected_increase = markdown_pct * 2.5  # Simple assumption
    st.info(f"💡 **AI Prediction**: {markdown_pct}% markdown could increase sell-through by ~{expected_increase:.1f}% (based on historical patterns)")

    if st.button("🔁 Start Over"):
        st.session_state.page = 1
        st.session_state.uploaded_df = None
        st.session_state.ai_insights = None
        st.session_state.chat_messages = []
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# AI Components with Glass Styling
# --------------------------------------------------
def render_ai_insights_panel():
    """Render AI insights panel with glass morphism"""
    if st.session_state.ai_insights is None:
        st.markdown("""
        <div class="ai-glass-box ai-pulse">
            <div class="ai-glass-title">🤖 AI OPERATIONS COPILOT</div>
            <div class="ai-glass-text">
                Get AI-powered insights and action recommendations for your inventory
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🤖 Get AI Insights", key="get_insights", type="primary", use_container_width=True):
                with st.spinner("🧠 AI is analyzing your inventory data..."):
                    insights = get_ai_insights(snapshot_date=date.today())
                    if "error" not in insights:
                        st.session_state.ai_insights = insights
                        st.session_state.show_action_popup = True
                        st.success("✅ AI analysis complete!")
                        st.rerun()
                    else:
                        st.error(f"❌ AI service unavailable: {insights['error']}")
        return
    
    insights = st.session_state.ai_insights
    
    # AI Insights with glass styling
    st.markdown("""
    <div class="ai-glass-box">
        <div class="ai-glass-title">🤖 AI OPERATIONS COPILOT</div>
        <div class="ai-glass-text">Analysis Complete - Review insights below</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Executive Summary
    if "executive_summary" in insights:
        st.info(f"**🎯 Executive Summary:** {insights['executive_summary']}")
    
    # Key Metrics with AI styling
    if "key_metrics" in insights:
        metrics = insights["key_metrics"]
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="ai-kpi-chip">💰 At Risk Value</div>', unsafe_allow_html=True)
            st.metric("", f"${metrics.get('total_at_risk_value', 0):,.0f}")
        with col2:
            st.markdown('<div class="ai-kpi-chip">🔥 High Risk</div>', unsafe_allow_html=True)
            st.metric("", metrics.get('high_risk_batches', 0))
        with col3:
            st.markdown('<div class="ai-kpi-chip">🟡 Medium Risk</div>', unsafe_allow_html=True)
            st.metric("", metrics.get('medium_risk_batches', 0))
        with col4:
            st.markdown('<div class="ai-kpi-chip">📅 Avg Days</div>', unsafe_allow_html=True)
            avg_days = metrics.get('avg_days_to_expiry', 0)
            st.metric("", f"{avg_days:.0f}")
    
    # Action Summary Button
    if "prioritized_actions" in insights and insights["prioritized_actions"]:
        action_count = len(insights["prioritized_actions"])
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(f"🎯 Review {action_count} AI Actions", key="show_actions", type="primary", use_container_width=True):
                st.session_state.show_action_popup = True
                st.rerun()
    
    # Show actions if popup is enabled
    if st.session_state.get("show_action_popup", False):
        render_ai_actions()
    
    # Control buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Analysis", key="refresh_insights", use_container_width=True):
            st.session_state.ai_insights = None
            st.session_state.show_action_popup = False
            st.rerun()
    with col2:
        if st.button("📊 Toggle Actions", key="toggle_actions", use_container_width=True):
            st.session_state.show_action_popup = not st.session_state.get("show_action_popup", False)
            st.rerun()

def render_ai_actions():
    """Render AI actions with glass styling"""
    insights = st.session_state.ai_insights
    if not insights or "prioritized_actions" not in insights:
        return
    
    actions = insights["prioritized_actions"]
    
    st.markdown("""
    <div class="ai-glass-box">
        <div class="ai-glass-title">🎯 AI ACTION RECOMMENDATIONS</div>
        <div class="ai-glass-text">Review and provide feedback on each recommendation</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize action responses
    if "action_responses" not in st.session_state:
        st.session_state.action_responses = {}
    
    # Display actions in tabs for better organization
    if len(actions) > 3:
        tab_names = [f"Action {i+1}" for i in range(min(len(actions), 5))]
        tabs = st.tabs(tab_names)
        
        for i, (tab, action) in enumerate(zip(tabs, actions[:5])):
            with tab:
                render_single_ai_action(i, action)
    else:
        for i, action in enumerate(actions):
            render_single_ai_action(i, action)
    
    # Close button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ Close Actions Review", key="close_actions", type="primary", use_container_width=True):
            st.session_state.show_action_popup = False
            st.rerun()

def render_single_ai_action(index: int, action: dict):
    """Render a single AI action with glass styling"""
    action_key = f"action_{index}"
    priority = action.get('priority', 'medium')
    
    # Action card with glass styling
    priority_class = f"ai-action-{priority}"
    st.markdown(f"""
    <div class="ai-action-card {priority_class}">
        <h4 style="color: white; margin: 0 0 10px 0;">
            {action.get('action_type', 'Unknown').title()} - {priority.title()} Priority
        </h4>
        <p style="color: white; opacity: 0.9; margin: 5px 0;">
            {action.get('description', 'No description')}
        </p>
        <small style="color: white; opacity: 0.7;">
            Expected: {action.get('expected_impact', 'Unknown impact')}
        </small>
    </div>
    """, unsafe_allow_html=True)
    
    # Confidence indicator
    confidence = action.get('confidence', 0.5)
    st.progress(confidence, text=f"AI Confidence: {confidence*100:.0f}%")
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Will Consider", key=f"consider_{index}", use_container_width=True):
            st.session_state.action_responses[action_key] = "will_consider"
            record_feedback(
                f"action_{index}_{date.today().isoformat()}",
                "accepted",
                f"popup_action_{index}",
                action.get('action_type', 'unknown'),
                action.get('parameters', {}),
                action.get('confidence', 0.5)
            )
            st.success("✅ Marked as 'Will Consider'")
            st.rerun()
    
    with col2:
        if st.button("❌ Reject", key=f"reject_{index}", use_container_width=True):
            st.session_state.action_responses[action_key] = "rejected"
            record_feedback(
                f"action_{index}_{date.today().isoformat()}",
                "rejected",
                f"popup_action_{index}",
                action.get('action_type', 'unknown'),
                action.get('parameters', {}),
                action.get('confidence', 0.5)
            )
            st.error("❌ Marked as 'Rejected'")
            st.rerun()
    
    # Show current status
    current_response = st.session_state.action_responses.get(action_key)
    if current_response:
        if current_response == "will_consider":
            st.success("Status: ✅ Will Consider")
        else:
            st.error("Status: ❌ Rejected")

# --------------------------------------------------
# AI Chat Modal
# --------------------------------------------------
if st.session_state.show_ai_chat:
    st.markdown("""
    <div class="modal-bg">
        <div class="ai-modal-box">
            <div class="ai-glass-title">💬 AI ASSISTANT</div>
            <div class="ai-glass-text">Ask me anything about your inventory</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize chat with hello message
    if not st.session_state.chat_messages:
        with st.spinner("🤖 AI Assistant is connecting..."):
            hello_response = send_chat_message("Hello! Please introduce yourself and tell me how you can help with inventory management.")
            if "error" not in hello_response:
                st.session_state.chat_messages.append({
                    "role": "ai", 
                    "content": hello_response.get("response", "Hello! I'm your AI inventory assistant.")
                })
            else:
                st.session_state.chat_messages.append({
                    "role": "ai", 
                    "content": "Hello! I'm your AI inventory assistant. How can I help optimize your operations?"
                })
    
    # Chat history
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**🤖 AI:** {msg['content']}")
    
    # Chat input
    user_input = st.text_input("Ask me anything...", key="chat_input")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Send 📤", key="send_chat"):
            if user_input:
                st.session_state.chat_messages.append({"role": "user", "content": user_input})
                with st.spinner("🤖 AI is thinking..."):
                    response = send_chat_message(user_input)
                    if "error" not in response:
                        ai_response = response.get("response", "I couldn't process that request.")
                        st.session_state.chat_messages.append({"role": "ai", "content": ai_response})
                    else:
                        st.session_state.chat_messages.append({"role": "ai", "content": f"Error: {response['error']}"})
                st.rerun()
    
    with col2:
        if st.button("Clear 🗑️", key="clear_chat"):
            st.session_state.chat_messages = []
            st.rerun()
    
    with col3:
        if st.button("Close ❌", key="close_chat"):
            st.session_state.show_ai_chat = False
            st.rerun()

# --------------------------------------------------
# LOGIN MODAL (Original styling preserved)
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