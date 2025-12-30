import streamlit as st
import pandas as pd
import requests
from datetime import date

# --------------------------------------------------
# Configuration
# --------------------------------------------------
API_BASE_URL = "http://localhost:8000"

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="ThePerfectShop",
    layout="wide"
)

# --------------------------------------------------
# Session state init
# --------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = 1

if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None

# --------------------------------------------------
# API Helper Functions
# --------------------------------------------------
def check_api_connection():
    """Check if the backend API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_risk_analysis():
    """Get risk analysis from backend"""
    try:
        response = requests.get(f"{API_BASE_URL}/risk?snapshot_date={date.today()}")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_actions():
    """Get actions from backend"""
    try:
        response = requests.get(f"{API_BASE_URL}/actions/")
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_kpi_dashboard():
    """Get KPI dashboard data from backend"""
    try:
        response = requests.get(f"{API_BASE_URL}/kpis/dashboard")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

# --------------------------------------------------
# PAGE 1 — Upload CSV (Updated to use backend)
# --------------------------------------------------
def page_upload():
    st.title("🛒 ThePerfectShop")

    # Check API connection
    api_connected = check_api_connection()
    
    if api_connected:
        st.success("✅ Connected to backend API")
    else:
        st.error("❌ Backend API not available. Start with: `python -m uvicorn app.main:app --reload`")

    st.write(
        """
        Upload your inventory / sales CSV file to generate:
        - Risk List  
        - Action List  
        - Savings Dashboard
        
        **Or skip upload to see demo data from the backend database.**
        """
    )

    with st.sidebar:
        st.header("📂 Upload Data")
        uploaded_file = st.file_uploader(
            "Attach CSV file",
            type=["csv"]
        )

    col1, col2 = st.columns(2)
    
    with col1:
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            st.session_state.uploaded_df = df

            st.success("CSV uploaded successfully!")
            st.dataframe(df.head())

            if st.button("🚀 Submit & Continue"):
                st.session_state.page = 2
                st.rerun()
    
    with col2:
        st.info("**Demo Mode Available**")
        st.write("Skip file upload and use backend database data:")
        
        if st.button("📊 View Backend Data", type="primary"):
            st.session_state.uploaded_df = "backend_data"
            st.session_state.page = 2
            st.rerun()


# --------------------------------------------------
# PAGE 2 — Risk & Action Lists (Updated to use backend)
# --------------------------------------------------
def page_risk_action():
    st.title("⚠️ Risk List & 📋 Action List")

    df = st.session_state.uploaded_df
    api_connected = check_api_connection()

    if df is None:
        st.warning("No data found. Please upload a CSV first.")
        return

    # Use backend data if available, otherwise use uploaded CSV
    if df == "backend_data" and api_connected:
        st.info("📡 Using live data from backend database")
        
        # Get data from backend
        risk_data = get_risk_analysis()
        actions_data = get_actions()
        
        # Convert to DataFrames
        if risk_data:
            risk_list = pd.DataFrame(risk_data)
        else:
            risk_list = pd.DataFrame({"message": ["No risk items found"]})
            
        if actions_data:
            action_list = pd.DataFrame(actions_data)
        else:
            action_list = pd.DataFrame({"message": ["No actions available"]})
            
    else:
        st.info("📁 Using uploaded CSV data")
        # ---- MOCK LOGIC for uploaded CSV ----
        risk_list = df.head(10).copy()
        risk_list["risk_score"] = 80

        action_list = df.head(10).copy()
        action_list["recommended_action"] = "MARKDOWN"
        action_list["expected_savings"] = 500

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🚨 Risk List")
        st.dataframe(risk_list)
        st.download_button(
            "Download Risk List",
            risk_list.to_csv(index=False),
            file_name="risk_list.csv",
            mime="text/csv"
        )

    with col2:
        st.subheader("🛠️ Action List")
        st.dataframe(action_list)
        st.download_button(
            "Download Action List",
            action_list.to_csv(index=False),
            file_name="action_list.csv",
            mime="text/csv"
        )

    st.markdown("---")

    if st.button("➡️ Next: Savings Dashboard"):
        st.session_state.page = 3
        st.rerun()


# --------------------------------------------------
# PAGE 3 — Savings Dashboard (Updated to use backend)
# --------------------------------------------------
def page_dashboard():
    st.title("💰 Savings Dashboard & Analysis")

    api_connected = check_api_connection()
    
    if api_connected:
        # Get real KPI data from backend
        kpi_data = get_kpi_dashboard()
        
        if kpi_data:
            st.success("📡 Live data from backend")
            
            # ---- Real KPI Section ----
            col1, col2, col3 = st.columns(3)

            col1.metric("Total At-Risk Value", f"${kpi_data.get('total_at_risk_value', 0):,.2f}")
            col2.metric("Expected Savings", f"${kpi_data.get('recovered_value', 0):,.2f}")
            col3.metric("Actions Proposed", f"{kpi_data.get('write_off_reduction', 0):.1f}%")
        else:
            st.warning("Could not fetch KPI data from backend")
    else:
        st.info("📊 Demo data (backend not connected)")
        
        # ---- Demo KPI Section ----
        col1, col2, col3 = st.columns(3)

        col1.metric("Total At-Risk Value", "₹ 2,50,000")
        col2.metric("Expected Savings", "₹ 1,20,000")
        col3.metric("Actions Proposed", "18")

    st.markdown("---")

    # ---- Charts / Analysis Placeholder ----
    st.subheader("📊 Analysis Results")

    if api_connected:
        st.success(
            """
            ✅ **Backend Connected** - Real-time data available
            
            This dashboard shows live metrics from your PostgreSQL database:
            - Risk analysis from current inventory
            - Action recommendations based on business rules
            - Financial impact calculations
            """
        )
    else:
        st.info(
            """
            This section will contain:
            - Savings trends
            - Risk reduction over time
            - Action effectiveness

            **To see live data:** Start the backend server:
            ```
            python -m uvicorn app.main:app --reload
            ```
            """
        )

    st.markdown("---")

    if st.button("🔁 Start Over"):
        st.session_state.page = 1
        st.session_state.uploaded_df = None
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
