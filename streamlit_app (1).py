import streamlit as st
import pandas as pd

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
# PAGE 1 — Upload CSV
# --------------------------------------------------
def page_upload():
    st.title("🛒 ThePerfectShop")

    st.write(
        """
        Upload your inventory / sales CSV file to generate:
        - Risk List  
        - Action List  
        - Savings Dashboard
        """
    )

    with st.sidebar:
        st.header("📂 Upload Data")
        uploaded_file = st.file_uploader(
            "Attach CSV file",
            type=["csv"]
        )

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.session_state.uploaded_df = df

        st.success("CSV uploaded successfully!")
        st.dataframe(df.head())

        if st.button("🚀 Submit & Continue"):
            st.session_state.page = 2
            st.rerun()


# --------------------------------------------------
# PAGE 2 — Risk & Action Lists
# --------------------------------------------------
def page_risk_action():
    st.title("⚠️ Risk List & 📋 Action List")

    df = st.session_state.uploaded_df

    if df is None:
        st.warning("No data found. Please upload a CSV first.")
        return

    # ---- MOCK LOGIC (replace later with real pipeline) ----
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
# PAGE 3 — Savings Dashboard
# --------------------------------------------------
def page_dashboard():
    st.title("💰 Savings Dashboard & Analysis")

    # ---- KPI Section ----
    col1, col2, col3 = st.columns(3)

    col1.metric("Total At-Risk Value", "₹ 2,50,000")
    col2.metric("Expected Savings", "₹ 1,20,000")
    col3.metric("Actions Proposed", "18")

    st.markdown("---")

    # ---- Charts / Analysis Placeholder ----
    st.subheader("📊 Analysis Results")

    st.info(
        """
        This section will contain:
        - Savings trends
        - Risk reduction over time
        - Action effectiveness

        (Hook your ML / scoring pipeline here)
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
