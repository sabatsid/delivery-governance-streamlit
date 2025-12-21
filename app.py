import streamlit as st
import pandas as pd
from pages.customer_page import customer_page
from pages.leadership_page import leadership_page
from pages.operations_page import operations_page
from pages.program_page import program_page

# -------------------------
# PAGE CONFIG (MUST BE FIRST)
# -------------------------
st.set_page_config(
    page_title="Delivery Governance Control Tower",
    layout="wide"
)

if "escalations_log" not in st.session_state:
    st.session_state["escalations_log"] = []

# -------------------------
# CUSTOMER TICKET STORE
# -------------------------
if "customer_tickets" not in st.session_state:
    st.session_state.customer_tickets = []

# -------------------------
# APP MODE (Demo vs Secure)
# -------------------------
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "Demo"


# -------------------------
# LOAD EXCEL DATA
# -------------------------
@st.cache_data
def load_data():
    excel_file = "Delivery_governance_data.xlsx"
    
    orders_master = pd.read_excel(excel_file, sheet_name="Orders_Master")
    order_task_execution = pd.read_excel(excel_file, sheet_name="Order_Task_Execution")
    task_dictionary = pd.read_excel(excel_file, sheet_name="Process_Task_Dictionary")
    hold_reasons = pd.read_excel(excel_file, sheet_name="Hold_Reason_LOV")
    escalation_matrix = pd.read_excel(excel_file, sheet_name="Escalation_Matrix")
    login_credentials = pd.read_excel(excel_file, sheet_name="Login_Credentials")

    return {
        "orders": orders_master,
        "tasks": order_task_execution,
        "dictionary": task_dictionary,
        "holds": hold_reasons,
        "escalations": escalation_matrix,
        "login": login_credentials 
    }

data = load_data()

# -------------------------
# LIFECYCLE → OPS TEAM ROUTING
# -------------------------
LIFECYCLE_TO_OPS_TEAM = {
    "Lead to Order": "OPS_L2O",
    "Customer Onboarding": "OPS_ONBOARDING",
    "Build to Order": "OPS_B2O",
    "Last Mile Build – Wireless": "OPS_WL_BUILD",
    "Last Mile Build – Fiber": "OPS_FIBER_BUILD",
    "Order to Activation": "OPS_INSTALL"
}


# Initialise persona
if "persona" not in st.session_state:
    st.session_state.persona = None

# -------------------------
# AUTHENTICATION STATE
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_profile" not in st.session_state:
    st.session_state.user_profile = None


# -------------------------
# LANDING PAGE (4 DOORS)
# -------------------------
def landing_page():
    st.title("Delivery Governance Control Tower")
    st.caption("End-to-end execution and governance across the delivery lifecycle")
    st.divider()

    # Mode toggle
    st.radio(
        "Select access mode",
        ["Demo", "Secure Login"],
        horizontal=True,
        key="app_mode"
    )

    st.divider()

    if st.session_state.app_mode == "Demo":
        st.subheader("🎭 Select a persona")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("🧭 Program Manager"):
                st.session_state.persona = "Program"
                st.session_state.logged_in = True
                st.session_state.user_profile = {
                    "POC_Name": "Demo Program Manager"
                }
                st.rerun()
                
        with col2:
            if st.button("🛠 Operations Team"):
                st.session_state.persona = "Operations"
                st.session_state.logged_in = True
                st.session_state.user_profile = {
                    "POC_Name": "Demo Operations User",
                    "Team_Name": "OPS_L2O"
                }
                st.rerun()
                
        with col3:
            if st.button("📊 Leadership"):
                st.session_state.persona = "Leader"
                st.session_state.logged_in = True
                st.session_state.user_profile = {
                    "POC_Name": "Demo Leadership"
                }
                st.rerun()
                
        with col4:
            if st.button("👤 Customer"):
                st.session_state.persona = "Customer"
                st.session_state.logged_in = True
                st.session_state.user_profile = {
                    "POC_Name": "Demo Customer",
                    "Order_ID": data["orders"]["Order_ID"].iloc[0]
                }
                st.rerun()
                
        st.caption("⚡ One-click access for presentations")

    else:
        login_page()


def login_page():
    st.title("🔐 Secure Login")
    st.caption("Access the Delivery Governance Control Tower")

    login_id = st.text_input("Login ID")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        creds = data["login"]

        user = creds[
            (creds["Login_ID"] == login_id) &
            (creds["Password"] == password) &
            (creds["Active_Flag"] == "Y")
        ]

        if user.empty:
            st.error("Invalid credentials or inactive account.")
        else:
            user_record = user.iloc[0].to_dict()

            st.session_state.logged_in = True
            st.session_state.user_profile = user_record

            # Auto-set persona based on Type
            st.session_state.persona = user_record["Type"]

            st.success(f"Welcome {user_record['POC_Name']}!")
            st.rerun()

def logout():
    st.session_state.logged_in = False
    st.session_state.user_profile = None
    st.session_state.persona = None
    st.rerun()

# -------------------------
# SIDEBAR (GLOBAL)
# -------------------------
if st.session_state.get("logged_in"):
    with st.sidebar:
        st.markdown("### 👤 Logged in as")
        st.write(st.session_state.user_profile["POC_Name"])
        st.write(f"Role: {st.session_state.persona}")

        st.divider()

        if st.button("🚪 Logout"):
            logout()
            
# -------------------------
# LEADERSHIP PAGE
# -------------------------
def leadership_page():
    st.title("📊 Leadership Dashboard")
    st.caption("Delivery performance, risk hotspots, and execution trends")

    orders_df = data["orders"].copy()

    # Prepare dates
    orders_df["Order_Start_Date"] = pd.to_datetime(
        orders_df["Order_Start_Date"]
    )

    # Calculate ageing
    orders_df["Order_Ageing_Days"] = (
        pd.Timestamp.today() - orders_df["Order_Start_Date"]
    ).dt.days

    # Derive RAG
    def derive_rag(row):
        if row["SLA_Breach_Flag"] == "Yes":
            return "Red"
        elif row["Overall_RAG"] == "Amber":
            return "Amber"
        else:
            return "Green"

    orders_df["Derived_RAG"] = orders_df.apply(derive_rag, axis=1)

    # -------------------------
    # KPI SUMMARY
    # -------------------------
    total_orders = len(orders_df)
    breached_orders = (orders_df["SLA_Breach_Flag"] == "Yes").sum()
    breach_pct = round((breached_orders / total_orders) * 100, 1)
    avg_ageing = round(orders_df["Order_Ageing_Days"].mean(), 1)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Orders", total_orders)
    col2.metric("SLA Breach %", f"{breach_pct}%")
    col3.metric("Avg Order Ageing (Days)", avg_ageing)

    st.divider()

    # -------------------------
    # ORDERS BY RAG
    # -------------------------
    st.subheader("Order Risk Distribution")

    rag_counts = (
        orders_df["Derived_RAG"]
        .value_counts()
        .reset_index()
    )
    rag_counts.columns = ["RAG", "Order_Count"]

    st.bar_chart(
        rag_counts.set_index("RAG")
    )

    st.divider()

    # -------------------------
    # SLA BREACHES BY LIFECYCLE
    # -------------------------
    st.subheader("SLA Breaches by Lifecycle Stage")

    breach_by_stage = (
        orders_df[orders_df["SLA_Breach_Flag"] == "Yes"]
        .groupby("Lifecycle_Stage")
        .size()
        .reset_index(name="Breach_Count")
    )

    if not breach_by_stage.empty:
        st.bar_chart(
            breach_by_stage.set_index("Lifecycle_Stage")
        )
    else:
        st.info("No SLA breaches recorded.")

    st.divider()

    # -------------------------
    # AGEING TREND
    # -------------------------
    st.subheader("Order Ageing Trend")

    ageing_trend = (
        orders_df
        .groupby("Order_Start_Date")
        ["Order_Ageing_Days"]
        .mean()
        .reset_index()
    )

    st.line_chart(
        ageing_trend.set_index("Order_Start_Date")
    )


# -------------------------
# PAGE ROUTING
# -------------------------
if not st.session_state.logged_in:
    landing_page()

elif st.session_state.persona == "Program":
    program_page(data)

elif st.session_state.persona == "Operations":
    operations_page(data)

elif st.session_state.persona == "Leader":
    leadership_page(data)

elif st.session_state.persona == "Customer":
    customer_page(data)


