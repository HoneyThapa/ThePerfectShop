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

/* Remove problematic modal and chat styles that cause issues */
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
# AI Components
# --------------------------------------------------
def render_ai_insights_panel():
    """Render AI insights panel"""
    if st.session_state.ai_insights is None:
        # Create a nice call-to-action
        st.markdown("""
        <div class="ai-insights-panel">
            <h3 style="color: white; margin-top: 0;">🤖 AI Operations Copilot</h3>
            <p style="color: white; opacity: 0.9;">Get AI-powered insights and action recommendations for your inventory</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🤖 Get AI Insights", key="get_insights", type="primary", use_container_width=True):
                with st.spinner("🧠 AI is analyzing your inventory data..."):
                    insights = get_ai_insights(snapshot_date=date.today())
                    if "error" not in insights:
                        st.session_state.ai_insights = insights
                        # Show action popup automatically
                        st.session_state.show_action_popup = True
                        st.success("✅ AI analysis complete! Review actions below.")
                        st.rerun()
                    else:
                        st.error(f"❌ AI service unavailable: {insights['error']}")
        return
    
    insights = st.session_state.ai_insights
    
    # Header
    st.markdown("""
    <div class="ai-insights-panel">
        <h3 style="color: white; margin-top: 0;">🤖 AI Operations Copilot - Analysis Complete</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Executive Summary in an info box
    if "executive_summary" in insights:
        st.info(f"**🎯 Executive Summary:** {insights['executive_summary']}")
    
    # Key Metrics in columns
    if "key_metrics" in insights:
        st.markdown("### 📊 Key Metrics")
        metrics = insights["key_metrics"]
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "At Risk Value", 
                f"${metrics.get('total_at_risk_value', 0):,.0f}",
                help="Total value of inventory at risk of expiring"
            )
        with col2:
            st.metric(
                "High Risk Batches", 
                metrics.get('high_risk_batches', 0),
                help="Number of batches with high expiry risk"
            )
        with col3:
            st.metric(
                "Medium Risk Batches", 
                metrics.get('medium_risk_batches', 0),
                help="Number of batches with medium expiry risk"
            )
        with col4:
            avg_days = metrics.get('avg_days_to_expiry', 0)
            st.metric(
                "Avg Days to Expiry", 
                f"{avg_days:.0f}",
                help="Average days until expiry across all batches",
                delta=None if avg_days >= 0 else "⚠️ Past expiry"
            )
    
    # Action Summary Button
    if "prioritized_actions" in insights and insights["prioritized_actions"]:
        action_count = len(insights["prioritized_actions"])
        st.markdown("### 🎯 Action Recommendations")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**{action_count} actions identified** based on your inventory analysis")
        with col2:
            if st.button(f"📋 Review {action_count} Actions", key="show_actions", type="primary", use_container_width=True):
                st.session_state.show_action_popup = True
                st.rerun()
    
    # Control buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Analysis", key="refresh_insights", use_container_width=True):
            st.session_state.ai_insights = None
            st.session_state.show_action_popup = False
            st.rerun()
    with col2:
        if st.button("📊 View Detailed Actions", key="toggle_actions", use_container_width=True):
            st.session_state.show_action_popup = not st.session_state.get("show_action_popup", False)
            st.rerun()

def render_action_popup():
    """Render action recommendations using Streamlit native components"""
    if not st.session_state.get("show_action_popup", False):
        return
    
    insights = st.session_state.ai_insights
    if not insights or "prioritized_actions" not in insights:
        return
    
    actions = insights["prioritized_actions"]
    
    # Use Streamlit's native container instead of HTML modal
    st.markdown("---")
    st.markdown("## 🎯 Action Recommendations Review")
    st.info(f"**{len(actions)} actions identified** - Please review each recommendation below:")
    
    # Initialize action responses if not exists
    if "action_responses" not in st.session_state:
        st.session_state.action_responses = {}
    
    # Create tabs for better organization
    if len(actions) > 3:
        # Use tabs for many actions
        tab_names = [f"Action {i+1}" for i in range(min(len(actions), 5))]
        tabs = st.tabs(tab_names)
        
        for i, (tab, action) in enumerate(zip(tabs, actions[:5])):
            with tab:
                render_single_action(i, action)
    else:
        # Use columns for few actions
        cols = st.columns(min(len(actions), 3))
        for i, (col, action) in enumerate(zip(cols, actions)):
            with col:
                render_single_action(i, action)
    
    # Show remaining actions in expanders if more than 5
    if len(actions) > 5:
        st.markdown("### Additional Actions")
        for i, action in enumerate(actions[5:], start=5):
            with st.expander(f"Action {i+1}: {action.get('action_type', 'Unknown').title()}", expanded=False):
                render_single_action(i, action)
    
    # Control buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ Close Actions Review", key="close_popup", type="primary", use_container_width=True):
            st.session_state.show_action_popup = False
            st.rerun()

def render_single_action(index: int, action: dict):
    """Render a single action recommendation"""
    action_key = f"action_{index}"
    
    # Action details
    st.markdown(f"**{action.get('action_type', 'Unknown').title()}**")
    st.markdown(f"*{action.get('priority', 'medium').title()} Priority*")
    
    # Priority color indicator
    priority = action.get('priority', 'medium')
    if priority == 'high':
        st.error(f"🔴 High Priority Action")
    elif priority == 'medium':
        st.warning(f"🟡 Medium Priority Action")
    else:
        st.success(f"🟢 Low Priority Action")
    
    st.markdown(f"**Description:** {action.get('description', 'No description')}")
    st.markdown(f"**Expected Impact:** {action.get('expected_impact', 'Unknown impact')}")
    
    # Confidence bar
    confidence = action.get('confidence', 0.5)
    st.progress(confidence, text=f"Confidence: {confidence*100:.0f}%")
    
    # Action buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Will Consider", key=f"consider_{index}", use_container_width=True):
            st.session_state.action_responses[action_key] = "will_consider"
            # Record feedback
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
            # Record feedback
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
    
    st.markdown("---")

def render_ai_chat():
    """Render AI chat interface"""
    if not st.session_state.show_ai_chat:
        return
    
    st.markdown("---")
    st.markdown("### 💬 AI Assistant")
    
    # Initialize chat with hello message if empty
    if not st.session_state.chat_messages:
        with st.spinner("🤖 AI Assistant is connecting..."):
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
    
    # Chat history in a container with better styling
    chat_container = st.container()
    with chat_container:
        for i, msg in enumerate(st.session_state.chat_messages):
            if msg["role"] == "user":
                # User message - right aligned
                st.markdown(f"""
                <div style="text-align: right; margin: 10px 0;">
                    <div style="display: inline-block; background: #0066cc; color: white; 
                                padding: 10px 15px; border-radius: 15px 15px 5px 15px; 
                                max-width: 70%; text-align: left;">
                        <strong>You:</strong> {msg["content"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # AI message - left aligned
                st.markdown(f"""
                <div style="text-align: left; margin: 10px 0;">
                    <div style="display: inline-block; background: #f0f2f6; color: #333; 
                                padding: 10px 15px; border-radius: 15px 15px 15px 5px; 
                                max-width: 70%; text-align: left; border-left: 4px solid #00cc88;">
                        <strong>🤖 AI:</strong> {msg["content"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Chat input section
    st.markdown("---")
    
    # Quick action buttons
    st.markdown("**Quick Questions:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("❓ Top Risks", key="quick_risks"):
            quick_message = "What are the top 3 risks I should focus on?"
            st.session_state.chat_messages.append({"role": "user", "content": quick_message})
            with st.spinner("🤖 AI is thinking..."):
                response = send_chat_message(quick_message)
                if "error" not in response:
                    ai_response = response.get("response", "I couldn't process that request.")
                    st.session_state.chat_messages.append({"role": "ai", "content": ai_response})
                else:
                    st.session_state.chat_messages.append({"role": "ai", "content": f"Error: {response['error']}"})
            st.rerun()
    
    with col2:
        if st.button("💰 Reduce Waste", key="quick_waste"):
            quick_message = "How can I reduce waste in my inventory?"
            st.session_state.chat_messages.append({"role": "user", "content": quick_message})
            with st.spinner("🤖 AI is thinking..."):
                response = send_chat_message(quick_message)
                if "error" not in response:
                    ai_response = response.get("response", "I couldn't process that request.")
                    st.session_state.chat_messages.append({"role": "ai", "content": ai_response})
                else:
                    st.session_state.chat_messages.append({"role": "ai", "content": f"Error: {response['error']}"})
            st.rerun()
    
    with col3:
        if st.button("📊 Explain Metrics", key="quick_metrics"):
            quick_message = "Can you explain what the key metrics mean?"
            st.session_state.chat_messages.append({"role": "user", "content": quick_message})
            with st.spinner("🤖 AI is thinking..."):
                response = send_chat_message(quick_message)
                if "error" not in response:
                    ai_response = response.get("response", "I couldn't process that request.")
                    st.session_state.chat_messages.append({"role": "ai", "content": ai_response})
                else:
                    st.session_state.chat_messages.append({"role": "ai", "content": f"Error: {response['error']}"})
            st.rerun()
    
    # Text input for custom questions
    user_input = st.text_input("💬 Ask me anything about your inventory...", key="chat_input", placeholder="Type your question here...")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Send 📤", key="send_chat", type="primary", use_container_width=True):
            if user_input:
                # Add user message
                st.session_state.chat_messages.append({"role": "user", "content": user_input})
                
                # Get AI response
                with st.spinner("🤖 AI is thinking..."):
                    response = send_chat_message(user_input)
                    if "error" not in response:
                        ai_response = response.get("response", "I couldn't process that request.")
                        st.session_state.chat_messages.append({"role": "ai", "content": ai_response})
                    else:
                        st.session_state.chat_messages.append({"role": "ai", "content": f"Error: {response['error']}"})
                
                st.rerun()
            else:
                st.warning("Please enter a message first!")
    
    with col2:
        if st.button("Clear Chat 🗑️", key="clear_chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.success("Chat cleared!")
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
        st.warning("⚠️ Please upload CSV data first to see AI insights and risk analysis.")
        st.info("👆 Use the file uploader in the sidebar to get started!")
        return

    # AI Insights Panel at the top
    render_ai_insights_panel()
    
    # Render action recommendations if popup is enabled
    if st.session_state.get("show_action_popup", False):
        render_action_popup()

    # Data visualization section
    st.markdown("---")
    st.markdown("## 📊 Risk & Action Analysis")

    # Mock data for demo (in real app, this would come from API)
    risk_list = df.head(10).copy()
    risk_list["Risk Score"] = [90,80,95,70,60,85,75,65,88,92]

    action_list = df.head(10).copy()
    action_list["Recommended Action"] = "MARKDOWN"
    action_list["Expected Savings"] = "₹500"

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ⚠️ Risk List")
        st.markdown("🔥 **High Risk Items:** 6 items need immediate attention")
        st.dataframe(risk_list, use_container_width=True, height=300)
        st.download_button("📤 Export Risk List", risk_list.to_csv(index=False), "risk_list.csv", use_container_width=True)

    with col2:
        st.markdown("### 🛠️ Action List")
        st.markdown("💰 **Estimated Savings:** ₹3,000 potential recovery")
        st.dataframe(action_list, use_container_width=True, height=300)
        st.download_button("📤 Export Action List", action_list.to_csv(index=False), "action_list.csv", use_container_width=True)

    # AI Chat Interface
    if st.session_state.show_ai_chat:
        render_ai_chat()

    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("➡️ Next: Dashboard", key="next_dashboard", type="primary", use_container_width=True):
            st.session_state.page = 3
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # AI Chat toggle button - better positioned
    if not st.session_state.show_ai_chat:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("💬 Open AI Chat Assistant", key="open_chat", use_container_width=True):
                st.session_state.show_ai_chat = True
                st.rerun()
    else:
        # Close chat button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("❌ Close AI Chat", key="close_chat", use_container_width=True):
                st.session_state.show_ai_chat = False
                st.rerun()

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
