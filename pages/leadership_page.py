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
# LEADERSHIP PAGE
# -------------------------
def leadership_page(data):
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
    # TAB 1: CUSTOMER TICKETS
    # -------------------------

    with tab1:
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
    # TAB 2: PROGRAM ESCALATIONS
    # -------------------------
    with tab2:
        st.subheader("🚨 Program Escalations & Requests")
        st.info(
            "Escalations and action requests raised by Program Managers "
            "for delayed or at-risk orders."
        )
        st.caption("🚧 Coming next")
        
