import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Delivery Governance Control Tower",
    layout="wide"
)

# Title
st.title("Delivery Governance Control Tower")
st.caption("End-to-end execution and governance across the delivery lifecycle")

st.divider()

# Initialise persona selection
if "persona" not in st.session_state:
    st.session_state.persona = None

st.subheader("Select your role to continue")

# Create four columns for persona doors
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

st.divider()

# Show selected persona
if st.session_state.persona:
    st.success(f"Persona selected: {st.session_state.persona}")
    st.info("Next: loading role-specific view...")
else:
    st.info("Please select a role to proceed.")
