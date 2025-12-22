import streamlit as st
import pandas as pd


# -------------------------
# LEADERSHIP PAGE
# -------------------------
def leadership_page(data):
    st.title("📊 Leadership Dashboard")
    st.caption("Executive view of delivery health, risk trends, and customer impact")

    orders_df = data["orders"].copy()

    # -------------------------
    # DATA PREP
    # -------------------------
    orders_df["Order_Start_Date"] = pd.to_datetime(
        orders_df["Order_Start_Date"], errors="coerce"
    )

    orders_df["Order_Ageing_Days"] = (
        pd.Timestamp.today() - orders_df["Order_Start_Date"]
    ).dt.days

    def derive_rag(row):
        if row.get("SLA_Breach_Flag") == "Yes":
            return "Red"
        elif row.get("Overall_RAG") == "Amber":
            return "Amber"
        else:
            return "Green"

    orders_df["Derived_RAG"] = orders_df.apply(derive_rag, axis=1)

    # -------------------------
    # TABS
    # -------------------------
    tab1, tab2, tab3 = st.tabs([
        "📊 KPIs",
        "📈 Trends",
        "🎯 CX Dashboard"
    ])

    # ======================================================
    # TAB 1 — KPIs (DELIVERY HEALTH)
    # ======================================================
    with tab1:
        st.subheader("📊 Delivery Health Overview")

        total_orders = len(orders_df)
        breached_orders = (orders_df["SLA_Breach_Flag"] == "Yes").sum()
        breach_pct = round((breached_orders / total_orders) * 100, 1) if total_orders else 0
        avg_ageing = round(orders_df["Order_Ageing_Days"].mean(), 1)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Orders", total_orders)
        col2.metric("SLA Breach %", f"{breach_pct}%")
        col3.metric("Avg Order Ageing (Days)", avg_ageing)
        col4.metric("Red Orders", (orders_df["Derived_RAG"] == "Red").sum())

        st.divider()

        st.subheader("Order Risk Distribution (RAG)")

        rag_counts = (
            orders_df["Derived_RAG"]
            .value_counts()
            .reset_index()
        )
        rag_counts.columns = ["RAG", "Order_Count"]

        st.bar_chart(rag_counts.set_index("RAG"))

        st.divider()

        st.subheader("SLA Breaches by Lifecycle Stage")

        breach_by_stage = (
            orders_df[orders_df["SLA_Breach_Flag"] == "Yes"]
            .groupby("Lifecycle_Stage")
            .size()
            .reset_index(name="Breach_Count")
        )

        if breach_by_stage.empty:
            st.info("No SLA breaches recorded.")
        else:
            st.bar_chart(breach_by_stage.set_index("Lifecycle_Stage"))

    # ======================================================
    # TAB 2 — TRENDS
    # ======================================================
    with tab2:
        st.subheader("📈 Delivery Performance Trends")

        st.markdown("**Average Order Ageing Trend**")

        ageing_trend = (
            orders_df
            .dropna(subset=["Order_Start_Date"])
            .groupby("Order_Start_Date")["Order_Ageing_Days"]
            .mean()
            .reset_index()
        )

        if ageing_trend.empty:
            st.info("Not enough data to display trends.")
        else:
            st.line_chart(ageing_trend.set_index("Order_Start_Date"))

        st.divider()

        st.markdown("**SLA Breach Trend**")

        sla_trend = (
            orders_df
            .assign(SLA_Breach=lambda x: x["SLA_Breach_Flag"] == "Yes")
            .groupby("Order_Start_Date")["SLA_Breach"]
            .mean()
            .reset_index()
        )

        if not sla_trend.empty:
            st.line_chart(sla_trend.set_index("Order_Start_Date"))

    # ======================================================
    # TAB 3 — CX DASHBOARD
    # ======================================================
    with tab3:
        st.subheader("🎯 Customer Experience Proxy")

        st.caption(
            "Operational signals used as a proxy for customer experience "
            "(without relying on surveys)."
        )

        # % Orders on Hold (proxy)
        if "Hold_Reason_Code" in orders_df.columns:
            hold_pct = round(
                orders_df["Hold_Reason_Code"].notna().mean() * 100, 1
            )
        else:
            hold_pct = 0

        col1, col2 = st.columns(2)
        col1.metric("Orders with HOLD (%)", f"{hold_pct}%")
        col2.metric("Avg Order Ageing (Days)", avg_ageing)

        st.divider()

        if "Hold_Reason_Code" in orders_df.columns:
            st.subheader("Top Hold Reasons")

            hold_reasons = (
                orders_df["Hold_Reason_Code"]
                .dropna()
                .value_counts()
                .head(5)
            )

            if hold_reasons.empty:
                st.info("No hold reasons captured.")
            else:
                st.bar_chart(hold_reasons)

        st.info(
            "📌 This view highlights where customers are likely experiencing "
            "delays or dissatisfaction due to operational constraints."
        )
