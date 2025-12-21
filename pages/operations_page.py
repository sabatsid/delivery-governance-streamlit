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
# OPERATIONS PAGE
# -------------------------
def operations_page(data):
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
    
        user_email = st.session_state.user_profile.get("Login_ID")
    
        tasks_df = data["tasks"].copy()
        dict_df = data["dictionary"].copy()
    
        # -------------------------
        # NORMALISE DATA (VERY IMPORTANT)
        # -------------------------
        tasks_df["assigned_clean"] = (
            tasks_df["Assigned_To_POC"]
            .astype(str)
            .str.strip()
            .str.lower()
        )
    
        tasks_df["status_clean"] = (
            tasks_df["Task_Status"]
            .astype(str)
            .str.strip()
            .str.lower()
        )
 
        # -------------------------
        # ALWAYS DEFINE THIS
        # -------------------------
        my_active_tasks = tasks_df[
            (tasks_df["Assigned_To_POC"].str.strip().str.lower()
             == user_email.strip().lower()) &
            (tasks_df["Task_Status"].str.strip().str.lower()
             == "In Progress")
        ]

        st.write(f"👤 Logged in as: {st.session_state.user_profile['POC_Name']}")
     
        # -------------------------
        # DISPLAY LOGIC
        # -------------------------
        if my_active_tasks.empty:
            st.success("🎉 You have no tasks currently in progress.")
        else:
            for _, current_task in my_active_tasks.iterrows():
    
                order_id = current_task["Order_ID"]
                lifecycle = current_task["Lifecycle_Stage"]
    
                st.divider()
                st.markdown(f"### 📦 Order `{order_id}` — {lifecycle}")
    
                col1, col2 = st.columns(2)
    
                # -------------------------
                # CURRENT TASK
                # -------------------------
                with col1:
                    st.markdown("**🔴 Current Task (In Progress)**")
                    st.write(f"**Task ID:** {current_task['Task_ID']}")
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
        st.subheader("🚨 Customer Tickets")
        st.info(
            "Tickets raised by customers "
            "for delayed or at-risk orders."
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
