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

# Initialise escalation log
if "escalations_log" not in st.session_state:
    st.session_state.escalations_log = []

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


    if st.session_state.escalations_log:
        st.divider()
        st.subheader("Escalation Log")

        escalation_df = pd.DataFrame(
            st.session_state.escalations_log
        )

        st.dataframe(escalation_df, use_container_width=True)


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

      # Decode hold reason details inline
    order_tasks["Hold_Reason_Details"] = (
        order_tasks["Hold_Reason_Code"]
        .map(hold_lookup)
        .fillna("No hold applied")
    )

    st.dataframe(
        order_tasks,
        use_container_width=True
    )

    st.divider()

    if st.button("⬅ Back to Role Selection"):
        st.session_state.persona = None

    st.dataframe(
        order_tasks,
        use_container_width=True
    )
    
     # -------------------------
    # ESCALATION ACTIONS
    # -------------------------
    st.divider()
    st.subheader("Escalation Actions")

    risky_tasks = order_tasks[
        (order_tasks["Task_Status"].isin(["In Risk", "In Progress"])) |
        (order_tasks["Escalation_Triggered"] == "Yes")
    ]

    if risky_tasks.empty:
        st.success("No tasks currently require escalation.")
    else:
        risky_tasks["Escalation_Key"] = (
            risky_tasks["Order_ID"] + " | " +
            risky_tasks["Task_ID"] + " | " +
            risky_tasks["Task_Status"]
        )
    
        selected_instance = st.selectbox(
            "Select task instance to escalate",
            options=risky_tasks["Escalation_Key"].unique()
        )

    # Parse selection
    selected_order_id = selected_instance.split(" | ")[0]
    selected_task_id = selected_instance.split(" | ")[1]


        escalation_reason = st.text_area(
            "Escalation reason",
            placeholder="Briefly describe why this escalation is required"
        )

        if st.button("🚨 Trigger Escalation"):
            st.session_state.escalations_log.append({
               "Order_ID": selected_order_id,
                "Task_ID": selected_task_id,
                "Escalated_To": escalate_to,
                "Reason": escalation_reason,
                "Timestamp": pd.Timestamp.now()
            })

            st.error(
                f"Escalation triggered for Task {selected_task} "
                f"and routed to {escalate_to}."
            )

    if st.session_state.escalations_log:
        st.divider()
        st.subheader("Escalation Log")

        escalation_df = pd.DataFrame(
            st.session_state.escalations_log
        )

        st.dataframe(escalation_df, use_container_width=True)    

# -------------------------
# OPERATIONS PAGE
# -------------------------
def operations_page():
    st.title("🛠 Operations Task Inbox")
    st.caption("Task-level execution view for day-to-day operations")

    tasks_df = data["tasks"].copy()
    hold_df = data["holds"].copy()

    # Convert Task_Start_Date to datetime
    tasks_df["Task_Start_Date"] = pd.to_datetime(
        tasks_df["Task_Start_Date"]
    )

    # Calculate task ageing (hours)
    tasks_df["Task_Ageing_Hours"] = (
        pd.Timestamp.today() - tasks_df["Task_Start_Date"]
    ).dt.total_seconds() / 3600

    # Decode hold reasons
    hold_lookup = {
        row["Hold_Code"]: (
            f"{row['Hold_Reason']} | "
            f"Owner: {row['Responsibility']} | "
            f"Category: {row['Category']}"
        )
        for _, row in hold_df.iterrows()
    }

    tasks_df["Hold_Reason_Details"] = (
        tasks_df["Hold_Reason_Code"]
        .map(hold_lookup)
        .fillna("No hold applied")
    )

    # -------------------------
    # FILTERS (OPS RELEVANT)
    # -------------------------
    st.subheader("Filters")

    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.multiselect(
            "Task Status",
            options=sorted(tasks_df["Task_Status"].unique()),
            default=sorted(tasks_df["Task_Status"].unique())
        )

    with col2:
        lifecycle_filter = st.multiselect(
            "Lifecycle Stage",
            options=sorted(tasks_df["Lifecycle_Stage"].unique()),
            default=sorted(tasks_df["Lifecycle_Stage"].unique())
        )

    with col3:
        assigned_filter = st.multiselect(
            "Assigned To",
            options=sorted(tasks_df["Assigned_To"].unique()),
            default=sorted(tasks_df["Assigned_To"].unique())
        )

    filtered_tasks = tasks_df[
        (tasks_df["Task_Status"].isin(status_filter)) &
        (tasks_df["Lifecycle_Stage"].isin(lifecycle_filter)) &
        (tasks_df["Assigned_To"].isin(assigned_filter))
    ]

    st.divider()

    # -------------------------
    # TASK INBOX
    # -------------------------
    st.subheader("My Task Inbox")

    st.dataframe(
        filtered_tasks.sort_values("Task_Ageing_Hours", ascending=False),
        use_container_width=True
    )

    st.divider()

    if st.button("⬅ Back to Role Selection"):
        st.session_state.persona = None


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

    st.divider()

    if st.button("⬅ Back to Role Selection"):
        st.session_state.persona = None


# -------------------------
# CUSTOMER PAGE
# -------------------------
def customer_page():
    st.title("📦 Track Your Order")
    st.caption("Simple, real-time visibility into your order status")

    orders_df = data["orders"].copy()

    # Select customer order
    selected_order = st.selectbox(
        "Select your Order ID",
        options=orders_df["Order_ID"].unique()
    )

    order = orders_df[
        orders_df["Order_ID"] == selected_order
    ].iloc[0]

    st.divider()

    # High-level status
    st.subheader("Current Order Status")
    st.metric(
        label="Status",
        value=order["Order_Status"]
    )

    st.divider()

    # Define simplified milestones
    milestones = [
        "Order Confirmed",
        "Build in Progress",
        "Installation",
        "Activation",
        "Completed"
    ]

    # Map lifecycle to milestone index
    lifecycle_to_milestone = {
        "Lead to Order": 0,
        "Customer Onboarding": 0,
        "Build to Order": 1,
        "Last Mile Build – Wireless": 1,
        "Last Mile Build – Fiber": 1,
        "Order to Activation": 3,
        "Completed": 4
    }

    current_stage_index = lifecycle_to_milestone.get(
        order["Lifecycle_Stage"], 1
    )

    st.subheader("Order Progress")

    for i, milestone in enumerate(milestones):
        if i < current_stage_index:
            st.success(f"✅ {milestone}")
        elif i == current_stage_index:
            st.warning(f"⏳ {milestone}")
        else:
            st.write(f"⬜ {milestone}")

    st.divider()

    st.info(
        "You will be notified once the next milestone is completed."
    )

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
