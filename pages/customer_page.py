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
# CUSTOMER PAGE
# -------------------------
def customer_page(data):
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
