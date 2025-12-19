import streamlit as st
import pandas as pd

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


    if st.session_state.get("escalations_log"):
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

        selected_order_id = selected_instance.split(" | ")[0]
        selected_task_id = selected_instance.split(" | ")[1]

        escalate_to = st.selectbox(
            "Escalate to",
            options=["Operations Manager", "Delivery Head", "Program Leadership"]
        )

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
                f"Escalation triggered for "
                f"Order {selected_order_id}, Task {selected_task_id}"
            )


    if st.session_state.get("escalations_log"):

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
    st.caption("Prioritised task execution with escalation visibility")

    # -------------------------
# CUSTOMER TICKETS (OPS VIEW)
# -------------------------
tickets_df = pd.DataFrame(
    st.session_state.get("customer_tickets", [])
)

# Logged-in ops team
# Logged-in ops team (safe access)
user_profile = st.session_state.get("user_profile")

if not isinstance(user_profile, dict):
    user_profile = {}

ops_team = user_profile.get("Team_Name")


if not tickets_df.empty:
    ops_tickets = tickets_df[
        tickets_df["Assigned_Team"] == ops_team
    ]
else:
    ops_tickets = pd.DataFrame()

# 🔔 Notification Bell
ticket_count = len(ops_tickets)

col1, col2 = st.columns([1, 6])

with col1:
    if ticket_count > 0:
        st.markdown(
            f"<h2 style='color:red'>🔔 {ticket_count}</h2>",
            unsafe_allow_html=True
        )
    else:
        st.markdown("<h2>🔔</h2>", unsafe_allow_html=True)

with col2:
    if ticket_count > 0:
        st.error(f"{ticket_count} customer ticket(s) require attention")
    else:
        st.caption("No new customer tickets")

    tasks_df = data["tasks"].copy()

    # Prepare dates
    tasks_df["Task_Start_Date"] = pd.to_datetime(
        tasks_df["Task_Start_Date"]
    )

    tasks_df["Task_Ageing_Hours"] = (
        pd.Timestamp.today() - tasks_df["Task_Start_Date"]
    ).dt.total_seconds() / 3600

    # -------------------------
    # MERGE ESCALATIONS
    # -------------------------
    escalation_log = pd.DataFrame(
        st.session_state.get("escalations_log", [])
    )

    if not escalation_log.empty:
        escalation_log["Is_Escalated"] = "Yes"

        tasks_df = tasks_df.merge(
            escalation_log[[
                "Order_ID",
                "Task_ID",
                "Escalated_To",
                "Reason"
            ]],
            on=["Order_ID", "Task_ID"],
            how="left"
        )

        tasks_df["Is_Escalated"] = tasks_df["Escalated_To"].notna().map(
            {True: "Yes", False: "No"}
        )
    else:
        tasks_df["Is_Escalated"] = "No"
        tasks_df["Escalated_To"] = ""
        tasks_df["Reason"] = ""

    # -------------------------
    # FILTERS
    # -------------------------
    st.subheader("Filters")

    col1, col2, col3 = st.columns(3)

    with col1:
        escalation_filter = st.multiselect(
            "Escalation Status",
            options=["Yes", "No"],
            default=["Yes", "No"]
        )

    with col2:
        status_filter = st.multiselect(
            "Task Status",
            options=sorted(tasks_df["Task_Status"].unique()),
            default=sorted(tasks_df["Task_Status"].unique())
        )

    with col3:
        lifecycle_filter = st.multiselect(
            "Lifecycle Stage",
            options=sorted(tasks_df["Lifecycle_Stage"].unique()),
            default=sorted(tasks_df["Lifecycle_Stage"].unique())
        )

    filtered_tasks = tasks_df[
        (tasks_df["Is_Escalated"].isin(escalation_filter)) &
        (tasks_df["Task_Status"].isin(status_filter)) &
        (tasks_df["Lifecycle_Stage"].isin(lifecycle_filter))
    ]

    st.divider()

    # -------------------------
    # INBOX TABLE
    # -------------------------
    st.subheader("My Task Inbox")


    # -------------------------
# CUSTOMER RAISED TICKETS
# -------------------------
if not ops_tickets.empty:
    st.divider()
    st.subheader("📩 Customer Raised Tickets")

    st.dataframe(
        ops_tickets[
            ["Order_ID", "Lifecycle_Stage", "Issue", "Timestamp"]
        ],
        use_container_width=True
    )

    

    def highlight_escalation(row):
        if row["Is_Escalated"] == "Yes":
            return ["background-color: #ffe6e6"] * len(row)
        return [""] * len(row)

    # Sort BEFORE styling
    sorted_tasks = filtered_tasks.sort_values(
        ["Is_Escalated", "Task_Ageing_Hours"],
        ascending=[False, False]
    )
    
    # Apply styling AFTER sorting
    styled_tasks = sorted_tasks.style.apply(
        highlight_escalation,
        axis=1
    )
    
    st.dataframe(
        styled_tasks,
        use_container_width=True
    )

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
# CUSTOMER PAGE
# -------------------------
def customer_page():
    st.title("📦 Track Your Order")
    st.caption("Real-time visibility into your order and support")

    user = st.session_state.user_profile
    customer_order_id = user["Order_ID"]

    orders_df = data["orders"].copy()
    tasks_df = data["tasks"].copy()

    # -------------------------
    # FETCH CUSTOMER ORDER ONLY
    # -------------------------
    order = orders_df[
        orders_df["Order_ID"] == customer_order_id
    ].iloc[0]

    lifecycle = order["Lifecycle_Stage"]

    st.divider()

    # -------------------------
    # ORDER STATUS
    # -------------------------
    st.subheader("Current Order Status")
    st.metric("Order ID", customer_order_id)
    st.metric("Current Stage", lifecycle)
    st.metric("Status", order["Order_Status"])

    st.divider()

    # -------------------------
    # ORDER PROGRESS (SIMPLE)
    # -------------------------
    milestones = [
        "Order Confirmed",
        "Build in Progress",
        "Installation",
        "Activation",
        "Completed"
    ]

    lifecycle_to_milestone = {
        "Lead to Order": 0,
        "Customer Onboarding": 0,
        "Build to Order": 1,
        "Last Mile Build – Wireless": 1,
        "Last Mile Build – Fiber": 1,
        "Order to Activation": 3,
        "Completed": 4
    }

    current_index = lifecycle_to_milestone.get(lifecycle, 1)

    st.subheader("Order Progress")

    for i, milestone in enumerate(milestones):
        if i < current_index:
            st.success(f"✅ {milestone}")
        elif i == current_index:
            st.warning(f"⏳ {milestone}")
        else:
            st.write(f"⬜ {milestone}")

    # -------------------------
    # RAISE SUPPORT TICKET
    # -------------------------
    st.divider()
    st.subheader("🎫 Raise a Support Ticket")

    ticket_reason = st.selectbox(
        "Issue category",
        [
            "Delay in current stage",
            "No update received",
            "Incorrect order details",
            "Site readiness issue",
            "Other"
        ]
    )

    ticket_description = st.text_area(
        "Describe the issue",
        placeholder="Briefly describe the problem you are facing"
    )

    routed_team = LIFECYCLE_TO_OPS_TEAM.get(
        lifecycle, "OPS_GENERAL"
    )

    st.info(
        f"📍 This ticket will be routed to **{routed_team}** based on your current stage."
    )

    if st.button("🚨 Submit Ticket"):
        st.session_state.customer_tickets.append({
            "Order_ID": customer_order_id,
            "Customer_Name": user["POC_Name"],
            "Lifecycle_Stage": lifecycle,
            "Routed_Team": routed_team,
            "Category": ticket_reason,
            "Description": ticket_description,
            "Timestamp": pd.Timestamp.now()
        })

        st.success("✅ Ticket raised successfully. Our team will contact you shortly.")

    # -------------------------
    # VIEW PREVIOUS TICKETS
    # -------------------------
    my_tickets = [
        t for t in st.session_state.customer_tickets
        if t["Order_ID"] == customer_order_id
    ]

    if my_tickets:
        st.divider()
        st.subheader("📂 Your Tickets")

        st.dataframe(
            pd.DataFrame(my_tickets),
            use_container_width=True
        )

# -------------------------
# PAGE ROUTING
# -------------------------
if not st.session_state.logged_in:
    landing_page()

elif st.session_state.persona == "Program":
    program_manager_page()

elif st.session_state.persona == "Operations":
    operations_page()

elif st.session_state.persona == "Leader":
    leadership_page()

elif st.session_state.persona == "Customer":
    customer_page()

