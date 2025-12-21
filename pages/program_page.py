import streamlit as st
import pandas as pd

# ---------------------------------
# LIFECYCLE → OPS TEAM ROUTING
# ---------------------------------
LIFECYCLE_TO_OPS_TEAM = {
    "Lead to Order": "OPS_L2O",
    "Customer Onboarding": "OPS_ONBOARDING",
    "Build to Order": "OPS_B2O",
    "Last Mile Build – Wireless": "OPS_LMB_WIRELESS",
    "Last Mile Build – Fiber": "OPS_LMB_FIBER",
    "Order to Activation": "OPS_O2A"
}

# -------------------------
# PROGRAM MANAGER
# -------------------------
def clear_program_filters():
    st.session_state["rag_filter"] = []
    st.session_state["sla_filter"] = []
    st.session_state["lifecycle_filter"] = []


def program_page(data):
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
