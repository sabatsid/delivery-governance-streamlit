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
# PROGRAM MANAGER
# -------------------------
def clear_program_filters():
    st.session_state["rag_filter"] = []
    st.session_state["sla_filter"] = []
    st.session_state["lifecycle_filter"] = []


def program_manager_page():
    st.title("🧭 Program Manager")
    st.caption("End-to-end portfolio oversight and program governance")

    orders_df = data["orders"].copy()
    tasks_df = data["tasks"].copy()

    orders_df["Order_Start_Date"] = pd.to_datetime(orders_df["Order_Start_Date"])
    orders_df["Order_Ageing_Days"] = (
        pd.Timestamp.today() - orders_df["Order_Start_Date"]
    ).dt.days

    # -------------------------
    # TOP TABS
    # -------------------------
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Program Master View",
        "📁 Individual Program View",
        "🚨 Escalations",
        "👥 Resource Allocation"
    ])

    # ======================================================
    # TAB 1 — PROGRAM MASTER VIEW
    # ======================================================
    with tab1:
        st.subheader("📊 Program Master View")
        st.divider()

        # -------------------------
        # KPI SUMMARY
        # -------------------------
        total_orders = len(orders_df)
        
        breached_orders = (
            orders_df["SLA_Breach_Flag"] == "Yes"
        ).sum()
        
        at_risk_orders = (
            orders_df["Overall_RAG"] == "Amber"
        ).sum()
        
        avg_ageing = round(
            orders_df["Order_Ageing_Days"].mean(), 1
        )
        
        k1, k2, k3, k4 = st.columns(4)
        
        k1.metric("📦 Total Orders", total_orders)
        k2.metric("🔴 SLA Breaches", breached_orders)
        k3.metric("🟠 At-Risk Orders", at_risk_orders)
        k4.metric("⏱ Avg Ageing (Days)", avg_ageing)
        
        st.caption("Portfolio-wide visibility with focused order-level deep dives")
        
        st.divider()

        # -------------------------
        # ORDER SELECTION
        # -------------------------
        CUSTOMER_COL = "Client_Name"

        order_options = (
            orders_df["Order_ID"] + " | " + orders_df[CUSTOMER_COL]
        ).tolist()

        selected_option = st.selectbox(
            "Search or select an order (Order ID or Customer)",
            options=[""] + sorted(order_options)
        )

        selected_order = None
        if selected_option:
            selected_order = selected_option.split(" | ")[0]

        # -------------------------
        # ORDER SUMMARY
        # -------------------------
        if selected_order:
            order = orders_df[
                orders_df["Order_ID"] == selected_order
            ].iloc[0]

            st.divider()
            st.subheader("📄 Order Summary")

            c1, c2, c3 = st.columns(3)
            c1.metric("Customer", order["Client_Name"])
            c2.metric("Lifecycle Stage", order["Lifecycle_Stage"])
            c3.metric("Order Type", order["Order_Type"])

            c1.metric("RAG", order["Overall_RAG"])
            c2.metric("SLA Breach", order["SLA_Breach_Flag"])
            c3.metric("Order Ageing (Days)", order["Order_Ageing_Days"])

            # -------------------------
            # DEEP DIVE
            # -------------------------
            if st.button("🔍 Deep Dive into Task Execution"):
                st.subheader("🛠 Task Execution Details")

                order_tasks = tasks_df[
                    tasks_df["Order_ID"] == selected_order
                ]

                if "Task_Start_Date" in order_tasks.columns:
                    order_tasks = order_tasks.sort_values("Task_Start_Date")

                display_cols = [
                    c for c in [
                        "Task_ID",
                        "Task_Name",
                        "Task_Status",
                        "Assigned_To",
                        "Task_Start_Date",
                        "Actual_Hours",
                        "Hold_Reason_Code"
                    ]
                    if c in order_tasks.columns
                ]

                st.dataframe(order_tasks[display_cols], use_container_width=True)

        # -------------------------
        # PORTFOLIO FILTERS (ALWAYS VISIBLE)
        # -------------------------
        st.divider()
        st.subheader("📊 Portfolio Filters")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.multiselect(
                "RAG Status",
                sorted(orders_df["Overall_RAG"].dropna().unique()),
                key="rag_filter"
            )

        with col2:
            st.multiselect(
                "SLA Breach",
                ["Yes", "No"],
                key="sla_filter"
            )

        with col3:
            st.multiselect(
                "Lifecycle Stage",
                sorted(orders_df["Lifecycle_Stage"].dropna().unique()),
                key="lifecycle_filter"
            )

        c_apply, c_clear = st.columns(2)

        with c_apply:
            apply_filters = st.button("✅ Apply Filters")

        with c_clear:
            st.button("🧹 Clear Filters", on_click=clear_program_filters)

        # -------------------------
        # FILTERED RESULTS
        # -------------------------
        if apply_filters:
            filtered_orders = orders_df.copy()

            if st.session_state["rag_filter"]:
                filtered_orders = filtered_orders[
                    filtered_orders["Overall_RAG"].isin(st.session_state["rag_filter"])
                ]

            if st.session_state["sla_filter"]:
                filtered_orders = filtered_orders[
                    filtered_orders["SLA_Breach_Flag"].isin(st.session_state["sla_filter"])
                ]

            if st.session_state["lifecycle_filter"]:
                filtered_orders = filtered_orders[
                    filtered_orders["Lifecycle_Stage"].isin(
                        st.session_state["lifecycle_filter"]
                    )
                ]

            st.divider()
            st.subheader("📋 Filtered Orders")

            if filtered_orders.empty:
                st.warning("No orders match selected filters.")
            else:
                st.dataframe(
                    filtered_orders[
                        [
                            "Order_ID",
                            "Client_Name",
                            "Lifecycle_Stage",
                            "Order_Type",
                            "Overall_RAG",
                            "SLA_Breach_Flag",
                            "Order_Ageing_Days"
                        ]
                    ],
                    use_container_width=True
                )

    # ======================================================
    # TAB 2 — PLACEHOLDERS
    # ======================================================
    with tab2:
        st.info("🚧 Individual Program View — Coming soon")

    with tab3:
        st.info("🚧 Escalations — Coming soon")

    with tab4:
        st.info("🚧 Resource Allocation — Coming soon")

# -------------------------
# OPERATIONS PAGE
# -------------------------
def operations_page():
    st.title("🛠 Operations Execution Hub")
    st.caption("Task execution, customer requests, and program escalations")

    tab1, tab2, tab3 = st.tabs([
        "📋 My Task Inbox",
        "🎫 Customer Tickets",
        "🚨 Program Escalations"
    ])

    # -------------------------
    # TAB 1: MY TASK INBOX
    # -------------------------
    with tab1:
        st.subheader("📋 My Active Tasks")
        st.caption("Tasks currently in progress and assigned to you")
    
        # Logged-in user
        user = st.session_state.user_profile.get("POC_Name")
    
        tasks_df = data["tasks"].copy()
        dict_df = data["dictionary"].copy()
    
        # -------------------------
        # CLEAN TEXT FOR RELIABLE MATCHING
        # -------------------------
        tasks_df["__assigned_clean"] = (
            tasks_df["Assigned_To_POC"]
            .astype(str)
            .str.lower()
            .str.replace(".", "", regex=False)
            .str.replace(" ", "", regex=False)
        )
    
        user_clean = (
            str(user)
            .lower()
            .replace(".", "")
            .replace(" ", "")
        )
    
        tasks_df["__status_clean"] = (
            tasks_df["Task_Status"]
            .astype(str)
            .str.lower()
        )
    
        # -------------------------
        # FILTER IN-PROGRESS TASKS
        # -------------------------
        my_active_tasks = tasks_df[
            (tasks_df["__assigned_clean"] == user_clean) &
            (tasks_df["__status_clean"] == "In Progress")
        ]
    
        if my_active_tasks.empty:
            st.success("🎉 You have no tasks currently in progress.")
        else:
            for _, current_task in my_active_tasks.iterrows():
    
                order_id = current_task["Order_ID"]
                lifecycle = current_task["Lifecycle_Stage"]
                task_id = current_task["Task_ID"]
    
                st.divider()
                st.markdown(
                    f"### 📦 Order `{order_id}` — {lifecycle}"
                )
    
                col1, col2 = st.columns(2)
    
                # -------------------------
                # CURRENT TASK
                # -------------------------
                with col1:
                    st.markdown("**🔴 Current Task (In Progress)**")
                    st.write(f"**Task ID:** {task_id}")
                    st.write(f"**Task Name:** {current_task['Task_Name']}")
                    st.write(f"**Started On:** {current_task['Task_Start_Date']}")

    
                # -------------------------
                # NEXT TASK (FROM DICTIONARY)
                # -------------------------
                with col2:
                    st.markdown("**➡️ Next Task (Upcoming)**")
    
                    lifecycle_tasks = dict_df[
                        dict_df["Lifecycle_Stage"] == lifecycle
                    ].sort_values("Task_ID")
    
                    task_sequence = lifecycle_tasks["Task_ID"].tolist()
    
                    if task_id in task_sequence:
                        current_index = task_sequence.index(task_id)
    
                        if current_index + 1 < len(task_sequence):
                            next_task = lifecycle_tasks.iloc[current_index + 1]
                            st.write(f"**Task ID:** {next_task['Task_ID']}")
                            st.write(f"**Task Name:** {next_task['Task_Name']}")
                        else:
                            st.write("🎯 This is the final task in this lifecycle.")
                    else:
                        st.write("Next task not found in dictionary.")
    
                # -------------------------
                # COMPLETED TASKS (JOURNEY SO FAR)
                # -------------------------
                with st.expander("📜 View journey so far (completed tasks)"):
                    completed_tasks = tasks_df[
                        (tasks_df["Order_ID"] == order_id) &
                        (tasks_df["Task_Status"] == "Completed")
                    ]
    
                    if completed_tasks.empty:
                        st.info("No completed tasks yet.")
                    else:
                        display_cols = [
                            "Task_ID",
                            "Task_Name",
                            "Assigned_To",
                            "Task_End_Date"
                        ]
                        display_cols = [
                            c for c in display_cols
                            if c in completed_tasks.columns
                        ]
    
                        st.dataframe(
                            completed_tasks[display_cols],
                            use_container_width=True
                        )
    
    # -------------------------
    # TAB 2: CUSTOMER TICKETS
    # -------------------------
    with tab2:
        st.subheader("🎫 Customer Tickets")
        st.info(
            "Tickets raised by customers based on their current lifecycle stage. "
            "These require immediate operational action."
        )
        st.caption("🚧 Coming next")

    # -------------------------
    # TAB 3: PROGRAM ESCALATIONS
    # -------------------------
    with tab3:
        st.subheader("🚨 Program Escalations & Requests")
        st.info(
            "Escalations and action requests raised by Program Managers "
            "for delayed or at-risk orders."
        )
        st.caption("🚧 Coming next")

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

