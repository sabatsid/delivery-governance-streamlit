import streamlit as st
import pandas as pd

# -------------------------
# PAGE CONFIG (MUST BE FIRST)
# -------------------------
st.set_page_config(
    page_title="Delivery Governance Control Tower",
    layout="wide"
)

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

    return {
        "orders": orders_master,
        "tasks": order_task_execution,
        "dictionary": task_dictionary,
        "holds": hold_reasons,
        "escalations": escalation_matrix
    }

data = load_data()

# Initialise persona
if "persona" not in st.session_state:
    st.session_state.persona = None


# -------------------------
# LANDING PAGE (4 DOORS)
# -------------------------
def landing_page():
    st.title("Delivery Governance Control Tower")
    st.caption("End-to-end execution and governance across the delivery lifecycle")
    st.divider()
    
    st.subheader("Select your role to continue")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🧭 Program Manager", use_container_width=True):
            st.session_state.persona = "Program Manager"

    with col2:
        if st.button("🛠 Operations Team", use_container_width=True):
            st.session_state.persona = "Operations"

    with col3:
        if st.button("📊 Leadership", use_container_width=True):
            st.session_state.persona = "Leadership"

    with col4:
        if st.button("👤 Customer", use_container_width=True):
            st.session_state.persona = "Customer"

# -------------------------
# PROGRAM MANAGER PAGE
# -------------------------
def program_manager_page():
    st.title("🧭 Program Manager View")
    st.caption("Order-level visibility across the delivery lifecycle")

    # -------------------------
    # PREPARE ORDERS DATA
    # -------------------------
    orders_df = data["orders"].copy()
    tasks_df = data["tasks"].copy()

    orders_df["Order_Start_Date"] = pd.to_datetime(
        orders_df["Order_Start_Date"]
    )

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
    # FILTERS
    # -------------------------
    st.subheader("Filters")

    col1, col2, col3 = st.columns(3)

    with col1:
        lifecycle_filter = st.multiselect(
            "Lifecycle Stage",
            options=sorted(orders_df["Lifecycle_Stage"].unique()),
            default=sorted(orders_df["Lifecycle_Stage"].unique())
        )

    with col2:
        rag_filter = st.multiselect(
            "RAG Status",
            options=["Red", "Amber", "Green"],
            default=["Red", "Amber", "Green"]
        )

    with col3:
        order_type_filter = st.multiselect(
            "Order Type",
            options=sorted(orders_df["Order_Type"].unique()),
            default=sorted(orders_df["Order_Type"].unique())
        )

    filtered_orders = orders_df[
        (orders_df["Lifecycle_Stage"].isin(lifecycle_filter)) &
        (orders_df["Derived_RAG"].isin(rag_filter)) &
        (orders_df["Order_Type"].isin(order_type_filter))
    ]

    st.divider()

    # -------------------------
    # KPI SUMMARY
    # -------------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("🔴 Red Orders", (filtered_orders["Derived_RAG"] == "Red").sum())
    col2.metric("🟠 Amber Orders", (filtered_orders["Derived_RAG"] == "Amber").sum())
    col3.metric("🟢 Green Orders", (filtered_orders["Derived_RAG"] == "Green").sum())

    st.divider()

    # -------------------------
    # ORDER TABLE
    # -------------------------
    st.subheader("Order Overview")

    def highlight_rag(val):
        if val == "Red":
            return "background-color: #ffcccc"
        elif val == "Amber":
            return "background-color: #fff2cc"
        elif val == "Green":
            return "background-color: #d9ead3"
        return ""

    styled_orders = filtered_orders.style.applymap(
        highlight_rag,
        subset=["Derived_RAG"]
    )

    st.dataframe(styled_orders, use_container_width=True)

    # -------------------------
    # HOLD REASON LOOKUP
    # -------------------------
    hold_df = data["holds"].copy()

    hold_lookup = {
        row["Hold_Code"]: (
            f"{row['Hold_Reason']} | "
            f"Owner: {row['Responsibility']} | "
            f"Category: {row['Category']} | "
            f"Delay: {row['Delayed_TAT']}"
        )
        for _, row in hold_df.iterrows()
    }

    # -------------------------
    # DRILL-DOWN SECTION
    # -------------------------
    st.divider()
    st.subheader("Order Drill-Down: Task Execution History")

    selected_order = st.selectbox(
        "Select an Order ID to view task details",
        options=filtered_orders["Order_ID"].unique()
    )

    order_tasks = tasks_df[
        tasks_df["Order_ID"] == selected_order
    ].sort_values("Task_Start_Date")

    st.dataframe(
        order_tasks,
        use_container_width=True,
        column_config={
            "Hold_Reason_Code": st.column_config.TextColumn(
                "Hold Reason Code",
                help="Hover to view hold reason details",
                tooltip=order_tasks["Hold_Reason_Code"]
                .map(hold_lookup)
                .fillna("No hold applied")
            )
        }
    )


    st.divider()

    if st.button("⬅ Back to Role Selection"):
        st.session_state.persona = None


# -------------------------
# OPERATIONS PAGE
# -------------------------
def operations_page():
    st.title("🛠 Operations Team View")
    st.write(
        "Task-level execution inbox to manage assigned work, SLAs, "
        "HOLD reasons, and reassignment requests."
    )

    st.info("This page will show: Task inbox, SLAs, RAG status, HOLD reasons, and task actions.")

    if st.button("⬅ Back to Role Selection"):
        st.session_state.persona = None

# -------------------------
# LEADERSHIP PAGE
# -------------------------
def leadership_page():
    st.title("📊 Leadership View")
    st.write(
        "Performance and governance insights to identify systemic issues, "
        "delivery trends, and recurring bottlenecks."
    )

    st.info("This page will show: KPIs, trends, breach hotspots, and drill-down analytics.")

    if st.button("⬅ Back to Role Selection"):
        st.session_state.persona = None


# -------------------------
# CUSTOMER PAGE
# -------------------------
def customer_page():
    st.title("👤 Customer View")
    st.write(
        "Simple, high-level order tracking view providing clear delivery status "
        "and progress milestones."
    )

    st.info("This page will show: Order status timeline and current delivery stage.")

    if st.button("⬅ Back to Role Selection"):
        st.session_state.persona = None


# -------------------------
# PAGE ROUTING
# -------------------------
if st.session_state.persona is None:
    landing_page()

elif st.session_state.persona == "Program Manager":
    program_manager_page()

elif st.session_state.persona == "Operations":
    operations_page()

elif st.session_state.persona == "Leadership":
    leadership_page()

elif st.session_state.persona == "Customer":
    customer_page()
