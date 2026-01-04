import streamlit as st
import pandas as pd

# -------------------------
# OPERATIONS PAGE
# -------------------------
def operations_view(data):
    st.title("🛠 Operations Execution Hub")
    st.caption("Task execution, customer requests, and program escalations")

    tab1, tab2, tab3 = st.tabs([
        "📋 My Task Inbox",
        "🎫 Customer Tickets",
        "🚨 Program Escalations"
    ])

    # =====================================================
    # TAB 1: MY TASK INBOX
    # =====================================================
    with tab1:
        st.subheader("📋 My Active Tasks")
        st.caption("Tasks currently in progress and assigned to you")

        user_email = (
            st.session_state.user_profile
            .get("Login_ID", "")
            .strip()
            .lower()
        )

        # -------------------------
        # LOAD + ENRICH TASK DATA
        # -------------------------
        tasks_df = data["tasks"].copy()
        dict_df = data["dictionary"].copy()

        # Normalize for matching
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

        # 🔑 ENRICH TASKS WITH TASK NAME
        tasks_enriched = tasks_df.merge(
            dict_df[["Task_ID", "Task_Name", "Lifecycle_Stage"]],
            on="Task_ID",
            how="left",
            suffixes=("", "_dict")
        )

        # -------------------------
        # FILTER MY ACTIVE TASKS
        # -------------------------
        my_active_tasks = tasks_enriched[
            (tasks_enriched["assigned_clean"] == user_email) &
            (tasks_enriched["status_clean"] == "in progress")
        ]

        st.write(f"👤 Logged in as: {st.session_state.user_profile['POC_Name']}")

        if my_active_tasks.empty:
            st.success("🎉 You have no tasks currently in progress.")
        else:
            for _, current_task in my_active_tasks.iterrows():

                order_id = current_task["Order_ID"]
                lifecycle = current_task["Lifecycle_Stage"]
                task_id = current_task["Task_ID"]

                st.divider()
                st.markdown(f"### 📦 Order `{order_id}` — {lifecycle}")

                col1, col2 = st.columns(2)

                # -------------------------
                # CURRENT TASK
                # -------------------------
                with col1:
                    st.markdown("**🔴 Current Task (In Progress)**")
                    st.write(f"**Task ID:** {task_id}")
                    st.write(f"**Task Name:** {current_task.get('Task_Name', 'N/A')}")
                    st.write(f"**Started On:** {current_task.get('Task_Start_Date', 'N/A')}")

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
                # COMPLETED TASKS
                # -------------------------
                with st.expander("📜 View journey so far (completed tasks)"):
                    completed_tasks = tasks_enriched[
                        (tasks_enriched["Order_ID"] == order_id) &
                        (tasks_enriched["Task_Status"] == "Completed")
                    ]

                    if completed_tasks.empty:
                        st.info("No completed tasks yet.")
                    else:
                        st.dataframe(
                            completed_tasks[
                                ["Task_ID", "Task_Name", "Assigned_To_POC"]
                            ],
                            use_container_width=True
                        )

    # =====================================================
    # TAB 2: CUSTOMER TICKETS
    # =====================================================
    with tab2:
        st.subheader("🎫 Customer Tickets")
        st.caption("Customer-raised issues assigned to you")
    
        # -------------------------
        # AUTO-CLOSE RESOLVED TICKETS
        # -------------------------
        now = pd.Timestamp.now()
    
        for t in st.session_state.customer_tickets:
            if t.get("Status") == "Resolved":
                resolved_at = t.get("Status_Updated_On")
    
                if resolved_at and now - resolved_at > pd.Timedelta(hours=2):
                    t["Status"] = "Closed"
                    t["Status_Updated_On"] = now
    
        user_email = (
            st.session_state.user_profile
            .get("Login_ID", "")
            .strip()
            .lower()
        )
    
        tickets = st.session_state.get("customer_tickets", [])
    
        if not tickets:
            st.info("No customer tickets raised yet.")
        else:
            tickets_df = pd.DataFrame(tickets)
    
            tickets_df["assigned_poc_clean"] = (
                tickets_df["Assigned_To_POC"]
                .astype(str)
                .str.strip()
                .str.lower()
            )
    
            my_tickets = tickets_df[
                tickets_df["assigned_poc_clean"] == user_email
            ]
    
            if my_tickets.empty:
                st.success("🎉 No customer tickets assigned to you.")
            else:
                for _, t in my_tickets.iterrows():
                    st.divider()
    
                    st.markdown(
                        f"""
                        **🎫 Ticket ID:** `{t['Ticket_ID']}`  
                        **📦 Order ID:** `{t['Order_ID']}`  
                        **🛠 Task ID:** `{t['Task_ID']}`  
                        **👤 Customer:** {t['Customer_Name']}  
                        **📂 Category:** {t['Category']}  
                        **📝 Description:** {t['Description']}  
                        **📌 Status:** {t['Status']}  
                        **⏱ Raised On:** {t['Raised_On']}
                        """
                    )
    
                    _, col2 = st.columns(2)
    
                    with col2:
    
                        if t["Status"] == "Open":
                            if st.button("✅ Acknowledge", key=f"ack_{t['Ticket_ID']}"):
                                tickets_df.loc[
                                    tickets_df["Ticket_ID"] == t["Ticket_ID"],
                                    ["Status", "Status_Updated_On"]
                                ] = ["Acknowledged", pd.Timestamp.now()]
                                st.session_state.customer_tickets = tickets_df.to_dict("records")
                                st.success("Ticket acknowledged")
                                st.rerun()
    
                        elif t["Status"] == "Acknowledged":
                            if st.button("🔧 Start Work", key=f"progress_{t['Ticket_ID']}"):
                                tickets_df.loc[
                                    tickets_df["Ticket_ID"] == t["Ticket_ID"],
                                    ["Status", "Status_Updated_On"]
                                ] = ["In Progress", pd.Timestamp.now()]
                                st.session_state.customer_tickets = tickets_df.to_dict("records")
                                st.info("Work started on ticket")
                                st.rerun()
    
                        elif t["Status"] == "In Progress":
                            if st.button("✅ Mark Resolved", key=f"resolve_{t['Ticket_ID']}"):
                                tickets_df.loc[
                                    tickets_df["Ticket_ID"] == t["Ticket_ID"],
                                    ["Status", "Status_Updated_On", "Customer_Notified"]
                                ] = ["Resolved", pd.Timestamp.now(), True]
                                st.session_state.customer_tickets = tickets_df.to_dict("records")
                                st.success("Ticket resolved. Customer notified.")
                                st.rerun()
    
                        elif t["Status"] == "Resolved":
                            st.warning("⏳ Ticket will auto-close after 2 hours")




    # =====================================================
    # TAB 3: PROGRAM ESCALATIONS
    # =====================================================
    with tab3:
        st.subheader("🚨 Program Escalations & Requests")
        st.info(
            "Escalations and action requests raised by Program Managers "
            "for delayed or at-risk orders."
        )
        st.caption("🚧 Coming next")
