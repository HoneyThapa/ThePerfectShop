import streamlit as st
import pandas as pd

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="The Perfect Shop",
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
                <li>Risk List</li>
                <li>Action List</li>
                <li>Savings Dashboard</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("📂 Upload Data")
        uploaded_file = st.file_uploader("Attach CSV file", type=["csv"])

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
# PAGE 2 — Risk & Action Lists
# --------------------------------------------------
def page_risk_action():
    st.markdown('<div class="page-animate">', unsafe_allow_html=True)

    df = st.session_state.uploaded_df
    if df is None:
        st.warning("Upload CSV first.")
        return

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

# --------------------------------------------------
# PAGE 3 — Dashboard
# --------------------------------------------------
def page_dashboard():
    st.markdown('<div class="page-animate">', unsafe_allow_html=True)

    st.markdown('<div class="glass-box"><h1 style="color:white;">💰 Savings Dashboard</h1></div>', unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    c1.metric("Total At-Risk Value", "₹2,50,000")
    c2.metric("Expected Savings", "₹1,20,000")
    c3.metric("Actions Proposed", "18")

    if st.button("🔁 Start Over"):
        st.session_state.page = 1
        st.session_state.uploaded_df = None
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
