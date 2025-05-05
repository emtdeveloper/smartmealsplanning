import streamlit as st
import pandas as pd
import os
from bson.objectid import ObjectId
from utils.sidebar import sidebar
from utils.data_processing import log_event, load_system_logs
from utils.db import users_collection

# ================= Helper Functions =================

def load_user_records(path):
    """Load user records from JSON"""
    try:
        return pd.read_json(path)
    except Exception as e:
        st.error(f"Error loading user records: {e}")
        return None

def load_meal_plans(path):
    """Load meal plans from Parquet"""
    try:
        return pd.read_parquet(path)
    except Exception as e:
        st.error(f"Error loading meal plans: {e}")
        return None

def load_exercise_data(path):
    """Load exercise recommendations from CSV"""
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"Error loading exercise data: {e}")
        return None

def show_user_overview(records_df):
    """Display user overview section"""
    st.subheader("👥 Registered Users Summary")

    if records_df is not None:
        st.metric("Total Users", len(records_df))
        st.dataframe(records_df, use_container_width=True)
    else:
        st.warning("No user data available.")

def show_meal_plan_overview(meal_df):
    """Display meal plan overview"""
    st.subheader("🍽️ Optimized Meals Overview")

    if meal_df is not None:
        st.metric("Total Meals Available", len(meal_df))
        st.dataframe(meal_df[['name', 'calories', 'protein', 'carbs', 'fat']], use_container_width=True)
    else:
        st.warning("No meal plan data available.")

def show_exercise_plan_overview(exercise_df):
    """Display exercise recommendations"""
    st.subheader("🏋️ Exercise Recommendations Overview")

    if exercise_df is not None:
        st.metric("Exercises Available", len(exercise_df))
        st.dataframe(exercise_df, use_container_width=True)
    else:
        st.warning("No exercise data available.")

def show_assets_listing(path):
    """List available assets"""
    st.subheader("🗂️ Available Data Assets")

    try:
        files = os.listdir(path)
        if files:
            for file in files:
                st.write(f"📄 {file}")
        else:
            st.info("No assets found.")
    except Exception as e:
        st.error(f"Failed to list attached assets: {e}")

def user_management():
    st.subheader("User Management")

    users = list(users_collection.find({}))

    if not users:
        st.info("No users found in the database.")
        return
    
    for user in users:
        username = user.get("username", "N/A")
        email = user.get("email", "N/A")
        is_admin = user.get("is_admin", False)
        user_id = str(user["_id"])

        # Display user info
        col1, col2, col3, col4 = st.columns([2, 3, 2, 3])

        with col1:
            st.write(username)
        with col2:
            st.write(email)
        with col3:
            if is_admin:
                st.success("✅ Admin")
            else:
                st.error("❌ Not Admin")
        with col4:
            if not is_admin:
                promote_col, delete_col = st.columns(2)

                with promote_col:
                    if st.button(f"Promote", key=f"promote_{user_id}"):
                        st.session_state[f"pending_promote_{user_id}"] = True

                with delete_col:
                    if st.button(f"Delete", key=f"delete_{user_id}"):
                        st.session_state[f"pending_delete_{user_id}"] = True

        # handle pending actions outside buttons
        if st.session_state.get(f"pending_promote_{user_id}", False):
            st.warning(f"Are you sure you want to promote {username} to Admin?")

            confirm_col, cancel_col = st.columns(2)

            with confirm_col:
                if st.button(f"✅ Confirm", key=f"confirm_promote_{user_id}"):
                    users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"is_admin": True}})
                    log_event("action", f"User {username} promoted to Admin.", user_id)
                    st.success(f"{username} has been promoted to Admin!")
                    st.session_state.pop(f"pending_promote_{user_id}", None)
                    del st.session_state[f"pending_promote_{user_id}"]
                    st.rerun()

            with cancel_col:
                if st.button(f"❌ Cancel", key=f"cancel_promote_{user_id}"):
                    del st.session_state[f"pending_promote_{user_id}"]
                    st.rerun()

        if st.session_state.get(f"pending_delete_{user_id}", False):
            st.error(f"⚠️ Are you sure you want to delete {username}? This cannot be undone.")

            confirm_col, cancel_col = st.columns(2)

            with confirm_col:
                if st.button(f"✅ Confirm", key=f"confirm_delete_{user_id}"):
                    users_collection.delete_one({"_id": ObjectId(user_id)})
                    log_event("action", f"User {username} deleted.", user_id)
                    st.success(f"{username} deleted successfully.")
                    del st.session_state[f"pending_delete_{user_id}"]
                    st.rerun()

            with cancel_col:
                if st.button(f"❌ Cancel", key=f"cancel_delete_{user_id}"):
                    del st.session_state[f"pending_delete_{user_id}"]
                    st.rerun()

    st.divider()

def view_system_logs():
    st.subheader("System Logs")
    
    # Filters
    log_type_filter = st.selectbox("Filter by Type", ["All", "Login", "Action"])
    search_keyword = st.text_input("Search logs...")
    limit = st.slider("Number of recent entries", key="system log slider", min_value=10, max_value=500, value=100)

    # Load logs from DB
    logs = load_system_logs()

    # Filter logs
    if log_type_filter != "All":
        logs = [log for log in logs if log["type"] == log_type_filter.lower()]
    if search_keyword:
        logs = [log for log in logs if search_keyword.lower() in log["message"].lower()]

    logs = logs[-limit:]  # Last N entries

    # Display
    for log in reversed(logs):
        st.markdown(f"""
        - **{log['timestamp']}**  
        {log['type'].upper()} ➔ {log['message']}
        """)

# ================ Main Admin Dashboard =================

if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("You must log in to access this page.")
    st.switch_page("app.py")

# Hide default sidebar elements
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            [data-testid="stSidebarNav"] {display: none;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def main():
    st.title("🛠️ Admin Dashboard")
    sidebar(current_page="🛠️ Admin Dashboard")
    st.caption("Manage users, meals, exercises, and system assets from here.")
    st.divider()

    # Sidebar Navigation
    st.sidebar.header("Admin Menu")
    selected_page = st.sidebar.selectbox("Select Section", 
                                         ["User Overview", "Manage Users", "Meal Plans", "Exercise Plans", "Manage Assets", "View System Logs"])

    # Asset Paths
    assets_dir = os.path.join(os.getcwd(), "attached_assets")
    records_path = os.path.join(assets_dir, "records.json")
    meals_path = os.path.join(assets_dir, "optimized_meals.parquet")
    exercise_path = os.path.join(assets_dir, "cleaned_exercise_data_refined.csv")

    # Load Data
    records_df = load_user_records(records_path)
    meals_df = load_meal_plans(meals_path)
    exercise_df = load_exercise_data(exercise_path)

    # Routing Pages
    if selected_page == "User Overview":
        show_user_overview(records_df)

    elif selected_page == "Manage Users":
        user_management()

    elif selected_page == "Meal Plans":
        show_meal_plan_overview(meals_df)

    elif selected_page == "Exercise Plans":
        show_exercise_plan_overview(exercise_df)

    elif selected_page == "Manage Assets":
        show_assets_listing(assets_dir)

    elif selected_page == "View System Logs":
        view_system_logs()

if __name__ == "__main__":
    main()
