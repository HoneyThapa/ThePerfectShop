import streamlit as st
import pandas as pd
import requests
import json
from datetime import date, datetime
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional

# --------------------------------------------------
# Configuration
# --------------------------------------------------
API_BASE_URL = "http://localhost:8000"

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="ThePerfectShop - Connected",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# Custom CSS for background image
# --------------------------------------------------
def add_background():
    """Add background image to the dashboard"""
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{get_base64_of_bin_file('Background.png')}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .main .block-container {{
            background-color: rgba(0, 0, 0, 0.7);
            padding: 2rem;
            border-radius: 15px;
            margin-top: 2rem;
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        .sidebar .sidebar-content {{
            background-color: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(10px);
        }}
        /* Make all text white and bold */
        .stApp, .stApp * {{
            color: white !important;
        }}
        /* Title styling */
        h1, h2, h3, h4, h5, h6 {{
            color: white !important;
            font-weight: bold !important;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8) !important;
        }}
        /* Metric styling */
        .metric-container {{
            background-color: rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
            padding: 1rem !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }}
        [data-testid="metric-container"] {{
            background-color: rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
            padding: 1rem !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }}
        [data-testid="metric-container"] * {{
            color: white !important;
            font-weight: bold !important;
        }}
        /* Button styling */
        .stButton > button {{
            background-color: rgba(255, 255, 255, 0.2) !important;
            color: white !important;
            border: 2px solid rgba(255, 255, 255, 0.3) !important;
            font-weight: bold !important;
            backdrop-filter: blur(5px) !important;
        }}
        .stButton > button:hover {{
            background-color: rgba(255, 255, 255, 0.3) !important;
            border: 2px solid rgba(255, 255, 255, 0.5) !important;
        }}
        /* Sidebar styling */
        .sidebar .sidebar-content * {{
            color: white !important;
        }}
        /* Success/Error message styling */
        .stSuccess, .stError, .stWarning, .stInfo {{
            background-color: rgba(0, 0, 0, 0.6) !important;
            color: white !important;
            border-radius: 10px !important;
        }}
        /* DataFrame styling */
        .stDataFrame {{
            background-color: rgba(255, 255, 255, 0.9) !important;
            border-radius: 10px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def get_base64_of_bin_file(bin_file):
    """Convert binary file to base64 string"""
    import base64
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# --------------------------------------------------
# Session state init
# --------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = 1

if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None

if "api_connected" not in st.session_state:
    st.session_state.api_connected = False

# --------------------------------------------------
# API Helper Functions
# --------------------------------------------------
def check_api_connection():
    """Check if the backend API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            return True, health_data
        return False, None
    except Exception as e:
        return False, str(e)

def get_risk_analysis(snapshot_date: str = None):
    """Get risk analysis from backend"""
    try:
        if not snapshot_date:
            snapshot_date = date.today().strftime("%Y-%m-%d")
        
        response = requests.get(f"{API_BASE_URL}/risk", params={"snapshot_date": snapshot_date})
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error getting risk analysis: {e}")
        return None

def get_actions():
    """Get actions from backend"""
    try:
        response = requests.get(f"{API_BASE_URL}/actions/")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error getting actions: {e}")
        return []

def get_kpi_dashboard():
    """Get KPI dashboard data from backend"""
    try:
        response = requests.get(f"{API_BASE_URL}/kpis/dashboard")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error getting KPI dashboard: {e}")
        return None

def get_features_summary():
    """Get features summary from backend"""
    try:
        response = requests.get(f"{API_BASE_URL}/features/summary")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error getting features summary: {e}")
        return None

# --------------------------------------------------
# Sidebar - API Status
# --------------------------------------------------
def show_api_status():
    """Show API connection status in sidebar"""
    with st.sidebar:
        st.header("🔌 API Status")
        
        is_connected, health_data = check_api_connection()
        
        if is_connected:
            st.success("✅ Backend Connected")
            if health_data:
                db_status = health_data.get('checks', {}).get('database', {}).get('status', 'unknown')
                if db_status == 'healthy':
                    st.success("✅ Database Connected")
                else:
                    st.warning(f"⚠️ Database: {db_status}")
            st.session_state.api_connected = True
        else:
            st.error("❌ Backend Disconnected")
            st.warning("Start the backend server:")
            st.code("cd backend && python -m uvicorn app.main:app --reload")
            st.session_state.api_connected = False

# --------------------------------------------------
# PAGE 1 — Dashboard Overview (New)
# --------------------------------------------------
def page_dashboard():
    # Add background image
    add_background()
    
    st.title("🛒 ThePerfectShop - Dashboard")
    
    show_api_status()
    
    if not st.session_state.api_connected:
        st.error("Please start the backend server to use the dashboard.")
        return
    
    # Get dashboard data
    kpi_data = get_kpi_dashboard()
    features_data = get_features_summary()
    
    if kpi_data:
        st.subheader("📊 Key Performance Indicators")
        
        # KPI Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total At-Risk Value", 
                f"${kpi_data.get('total_at_risk_value', 0):,.2f}"
            )
        
        with col2:
            st.metric(
                "Recovered Value", 
                f"${kpi_data.get('recovered_value', 0):,.2f}"
            )
        
        with col3:
            st.metric(
                "Write-off Reduction", 
                f"{kpi_data.get('write_off_reduction', 0):.1f}%"
            )
        
        with col4:
            st.metric(
                "Inventory Turnover", 
                f"+{kpi_data.get('inventory_turnover_improvement', 0):.1f}%"
            )
    
    st.markdown("---")
    
    # Navigation buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📈 View Risk Analysis", use_container_width=True):
            st.session_state.page = 2
            st.rerun()
    
    with col2:
        if st.button("🛠️ Action Management", use_container_width=True):
            st.session_state.page = 3
            st.rerun()
    
    with col3:
        if st.button("📊 Detailed Analytics", use_container_width=True):
            st.session_state.page = 4
            st.rerun()
    
    # System Information
    if features_data:
        st.subheader("📋 System Information")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**Store-SKU Combinations:** {features_data.get('total_store_sku_combinations', 0)}")
        
        with col2:
            snapshot_date = features_data.get('snapshot_date')
            if snapshot_date:
                st.info(f"**Last Updated:** {snapshot_date}")
            else:
                st.info("**Status:** Ready for data")

# --------------------------------------------------
# PAGE 2 — Risk Analysis
# --------------------------------------------------
def page_risk_analysis():
    # Add background image
    add_background()
    
    st.title("⚠️ Risk Analysis")
    
    show_api_status()
    
    if not st.session_state.api_connected:
        st.error("Please start the backend server to view risk analysis.")
        return
    
    # Date selector
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_date = st.date_input(
            "Analysis Date",
            value=date.today(),
            help="Select date for risk analysis"
        )
    
    with col2:
        if st.button("🔄 Refresh Analysis"):
            st.rerun()
    
    # Get risk data
    risk_data = get_risk_analysis(selected_date.strftime("%Y-%m-%d"))
    
    if risk_data:
        if isinstance(risk_data, list) and len(risk_data) > 0:
            # Convert to DataFrame
            df_risk = pd.DataFrame(risk_data)
            
            st.subheader(f"🚨 Risk Items ({len(df_risk)} found)")
            
            # Display risk data
            st.dataframe(df_risk, use_container_width=True)
            
            # Download button
            csv = df_risk.to_csv(index=False)
            st.download_button(
                "📥 Download Risk Analysis",
                csv,
                file_name=f"risk_analysis_{selected_date}.csv",
                mime="text/csv"
            )
        else:
            st.info("✅ No high-risk items found for the selected date.")
    else:
        st.warning("Unable to fetch risk analysis data.")
    
    # Navigation
    if st.button("🏠 Back to Dashboard"):
        st.session_state.page = 1
        st.rerun()

# --------------------------------------------------
# PAGE 3 — Action Management
# --------------------------------------------------
def page_action_management():
    # Add background image
    add_background()
    
    st.title("🛠️ Action Management")
    
    show_api_status()
    
    if not st.session_state.api_connected:
        st.error("Please start the backend server to manage actions.")
        return
    
    # Get actions data
    actions_data = get_actions()
    
    if actions_data and len(actions_data) > 0:
        # Convert to DataFrame
        df_actions = pd.DataFrame(actions_data)
        
        st.subheader(f"📋 Recommended Actions ({len(df_actions)} items)")
        
        # Action filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'status' in df_actions.columns:
                status_filter = st.selectbox(
                    "Filter by Status",
                    options=['All'] + list(df_actions['status'].unique())
                )
                if status_filter != 'All':
                    df_actions = df_actions[df_actions['status'] == status_filter]
        
        with col2:
            if 'action_type' in df_actions.columns:
                type_filter = st.selectbox(
                    "Filter by Type",
                    options=['All'] + list(df_actions['action_type'].unique())
                )
                if type_filter != 'All':
                    df_actions = df_actions[df_actions['action_type'] == type_filter]
        
        # Display actions
        st.dataframe(df_actions, use_container_width=True)
        
        # Download button
        csv = df_actions.to_csv(index=False)
        st.download_button(
            "📥 Download Actions",
            csv,
            file_name=f"actions_{date.today()}.csv",
            mime="text/csv"
        )
        
    else:
        st.info("📝 No actions available. Actions will appear here when risk analysis identifies opportunities.")
    
    # Navigation
    if st.button("🏠 Back to Dashboard"):
        st.session_state.page = 1
        st.rerun()

# --------------------------------------------------
# PAGE 4 — Detailed Analytics
# --------------------------------------------------
def page_detailed_analytics():
    # Add background image
    add_background()
    
    st.title("📊 Detailed Analytics")
    
    show_api_status()
    
    if not st.session_state.api_connected:
        st.error("Please start the backend server to view analytics.")
        return
    
    # Get all data
    kpi_data = get_kpi_dashboard()
    features_data = get_features_summary()
    
    if kpi_data:
        st.subheader("💰 Financial Impact")
        
        # Create financial impact chart
        financial_data = {
            'Metric': ['At-Risk Value', 'Recovered Value', 'Potential Savings'],
            'Amount': [
                kpi_data.get('total_at_risk_value', 0),
                kpi_data.get('recovered_value', 0),
                kpi_data.get('total_at_risk_value', 0) - kpi_data.get('recovered_value', 0)
            ]
        }
        
        fig = px.bar(
            financial_data, 
            x='Metric', 
            y='Amount',
            title='Financial Impact Overview',
            color='Metric'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance metrics
        st.subheader("📈 Performance Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Write-off reduction gauge
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = kpi_data.get('write_off_reduction', 0),
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Write-off Reduction %"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, 25], 'color': "lightgray"},
                        {'range': [25, 50], 'color': "yellow"},
                        {'range': [50, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        with col2:
            # Inventory turnover gauge
            fig_gauge2 = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = kpi_data.get('inventory_turnover_improvement', 0),
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Inventory Turnover Improvement %"},
                gauge = {
                    'axis': {'range': [None, 20]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 5], 'color': "lightgray"},
                        {'range': [5, 10], 'color': "yellow"},
                        {'range': [10, 20], 'color': "lightblue"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 15
                    }
                }
            ))
            st.plotly_chart(fig_gauge2, use_container_width=True)
    
    # Navigation
    if st.button("🏠 Back to Dashboard"):
        st.session_state.page = 1
        st.rerun()

# --------------------------------------------------
# Router
# --------------------------------------------------
def main():
    # Navigation menu in sidebar
    with st.sidebar:
        st.markdown("---")
        st.header("🧭 Navigation")
        
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.page = 1
            st.rerun()
        
        if st.button("⚠️ Risk Analysis", use_container_width=True):
            st.session_state.page = 2
            st.rerun()
        
        if st.button("🛠️ Actions", use_container_width=True):
            st.session_state.page = 3
            st.rerun()
        
        if st.button("📊 Analytics", use_container_width=True):
            st.session_state.page = 4
            st.rerun()
    
    # Route to appropriate page
    if st.session_state.page == 1:
        page_dashboard()
    elif st.session_state.page == 2:
        page_risk_analysis()
    elif st.session_state.page == 3:
        page_action_management()
    elif st.session_state.page == 4:
        page_detailed_analytics()

if __name__ == "__main__":
    main()