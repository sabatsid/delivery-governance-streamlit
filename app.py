import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Delivery Governance Control Tower",
    layout="wide"
)

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
    st.write(
        "Order-level visibility across the delivery lifecycle to track ageing, "
        "identify bottlenecks, and trigger escalations."
    )

    st.info("This page will show: Orders, lifecycle stage, ageing, SLA breaches, and escalation actions.")
    
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
