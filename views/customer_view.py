import streamlit as st
import pandas as pd

def customer_view(data):
    st.title("📦 Track your order")
    st.caption("Real-time visibility into your order and support")

    # -------------------------
    # USER CONTEXT
    # -------------------------
    user = st.session_state.user_profile
    customer_order_id = user["Order_ID"]

    orders_df = data["orders"].copy()

    order = orders_df[
        orders_df["Order_ID"] == customer_order_id
    ].iloc[0]

    lifecycle = order["Lifecycle_Stage"]

    # -------------------------
    # ORDER STATUS
    # -------------------------
    st.subheader("Current Order Status")
    st.metric("Order ID", customer_order_id)
    st.metric("Current Stage", lifecycle)
    st.metric("Status", order["Order_Status"])

    st.divider()

    # -------------------------
    # ORDER PROGRESS
    # -------------------------
    milestones = [
        "Customer Onboarded",
        "Order Confirmed",
        "Installation",
        "Activation",
        "Completed"
    ]

    lifecycle_to_milestone = {
        # Customer onboarding & order creation
        "Lead to Order": 0,              # Customer Onboarded
        "Customer Onboarding": 1,        # Order Confirmed
    
        # Build & installation phases
        "Build to Order": 2,             # Installation
        "Last Mile Build – Wireless": 2, # Installation
        "Last Mile Build – Fiber": 2,    # Installation
    
        # Activation phase
        "Order to Activation": 3,        # Activation
    
        # Closure
        "Completed": 4                  # Completed
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

    routed_team = st.session_state.get(
        "LIFECYCLE_TO_OPS_TEAM", {}
    ).get(lifecycle, "OPS_GENERAL")


    if st.button("🚨 Submit Ticket"):
        ticket_id = f"TCKT_{len(st.session_state.customer_tickets) + 1:04d}"

        st.session_state.customer_tickets.append({
            "Ticket_ID": ticket_id,
            "Order_ID": customer_order_id,
            "Customer_Name": user["POC_Name"],
            "Lifecycle_Stage": lifecycle,
            "Routed_Team": routed_team,
            "Category": ticket_reason,
            "Description": ticket_description,
            "Status": "Open",
            "Raised_On": pd.Timestamp.now()
        })

        st.success(
            f"✅ Ticket **{ticket_id}** raised successfully. "
            "Our team will contact you shortly."
        )

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
        st.dataframe(pd.DataFrame(my_tickets), use_container_width=True)
