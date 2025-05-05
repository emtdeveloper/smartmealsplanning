import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from utils.sidebar import sidebar
from utils.data_processing import calculate_bmi, load_user_records
from utils.user_management import update_user, delete_user, get_user, update_user_progress
from utils.visualization import create_bmi_chart, create_weight_progress_chart

if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("You must log in to access this page.")
    st.switch_page("app.py")

user_id = st.session_state["current_user"]

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
    st.title("📝 User Profile")
    sidebar(current_page="📝 Profile")
    
    user_data = get_user(user_id)

    if not user_data:
        st.error(f"User not found.")
        return

    if user_data.get("profile_complete", False):
        display_existing_profile(user_data)
    else:
        create_profile(user_data)


def display_existing_profile(user_data):
    user_data = get_user(user_id)
    
    if not user_data:
        st.error(f"User ID {user_id} not found.")
        return
    
    # User information section
    st.subheader("Profile Information")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**Name:** {user_data.get('name', 'N/A')}")
        st.markdown(f"**Gender:** {user_data.get('gender', 'N/A').capitalize()}")
        st.markdown(f"**Age:** {user_data.get('age', 'N/A')}")
        st.markdown(f"**Height:** {user_data.get('height', 0)} cm")
        st.markdown(f"**Weight:** {user_data.get('weight', 0)} kg")
    
    with col2:
        st.markdown(f"**Activity Level:** {user_data.get('activity_level', 'N/A')}")
        st.markdown(f"**Diet Preference:** {user_data.get('diet', 'N/A').capitalize()}")
        st.markdown(f"**Goal:** {user_data.get('goal', 'N/A')}")
        st.markdown(f"**Health Status:** {user_data.get('health_status', 'N/A')}")
        st.markdown(f"**Health Conditions:** {user_data.get('health_conditions', 'None')}")
    
    with col3:
        # Display allergies
        allergies = user_data.get('allergies', [])
        if allergies:
            allergies_str = ", ".join(allergies)
            st.markdown(f"**Allergies:** {allergies_str}")
        else:
            st.markdown("**Allergies:** None")
        
        # Display preferred cuisines
        cuisines = user_data.get('preferred_cuisines', [])
        if cuisines:
            cuisines_str = ", ".join(cuisines)
            st.markdown(f"**Preferred Cuisines:** {cuisines_str}")
        else:
            st.markdown("**Preferred Cuisines:** None specified")
    
    # Display BMI chart
    st.subheader("Body Mass Index (BMI)")
    bmi = user_data.get('bmi', 0)
    status = user_data.get('health_status', 'Unknown')
    
    bmi_fig = create_bmi_chart(bmi, status)
    st.plotly_chart(bmi_fig, use_container_width=True)
    
    # Add info about BMI ranges
    bmi_col1, bmi_col2, bmi_col3, bmi_col4 = st.columns(4)
    
    with bmi_col1:
        st.markdown("**Underweight**")
        st.markdown("BMI < 18.5")
    
    with bmi_col2:
        st.markdown("**Healthy**")
        st.markdown("BMI 18.5-24.9")
    
    with bmi_col3:
        st.markdown("**Overweight**")
        st.markdown("BMI 25-29.9")
    
    with bmi_col4:
        st.markdown("**Obese**")
        st.markdown("BMI ≥ 30")
    
    # Progress tracking
    st.subheader("Weight Progress")
    
    progress_history = user_data.get('progress_history', [])
    if progress_history:
        progress_fig = create_weight_progress_chart(progress_history)
        st.plotly_chart(progress_fig, use_container_width=True)
        
        # Show last few entries in a table
        st.markdown("**Recent Progress Entries**")
        
        # Convert progress history to DataFrame for display
        progress_df = pd.DataFrame(progress_history[-5:])  # Show last 5 entries
        if not progress_df.empty:
            progress_df['timestamp'] = pd.to_datetime(progress_df['timestamp'])
            progress_df['timestamp'] = progress_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
            progress_df = progress_df.sort_values('timestamp', ascending=False)
            
            # Rename columns for display
            progress_df = progress_df.rename(columns={
                'timestamp': 'Date',
                'weight': 'Weight (kg)',
                'bmi': 'BMI'
            })
            
            st.dataframe(progress_df, use_container_width=True)
    else:
        st.info("No progress history available yet.")
    
    # Update weight form
    st.subheader("Update Progress")
    with st.form(key="update_progress_form"):
        new_weight = st.number_input("Current Weight (kg)", min_value=20.0, max_value=250.0, value=float(user_data.get('weight', 70)))
        
        update_button = st.form_submit_button(label="Update Progress")
        
        if update_button:
            success, message = update_user_progress(user_id, new_weight)
            if success:
                st.success(message)
                # Refresh the page to show updated progress
                st.rerun()
            else:
                st.error(message)
    
    # Edit profile section
    st.subheader("Edit Profile")
    
    with st.form(key="edit_profile_form"):
        # Split form into columns for better layout
        edit_col1, edit_col2, edit_col3 = st.columns(3)
        
        with edit_col1:
            name_parts = user_data.get('name', '').split()
            first_name = name_parts[0] if len(name_parts) > 0 else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            
            edit_first_name = st.text_input("First Name", value=first_name)
            edit_last_name = st.text_input("Last Name", value=last_name)
            
            edit_gender = st.selectbox(
                "Gender",
                options=["Male", "Female", "Other"],
                index=["male", "female", "other"].index(user_data.get('gender', 'male').lower())
            )
            
            edit_age = st.number_input(
                "Age",
                min_value=10,
                max_value=100,
                value=int(user_data.get('age', 30))
            )
            
            edit_height = st.number_input(
                "Height (cm)",
                min_value=50.0,
                max_value=250.0,
                value=float(user_data.get('height', 170))
            )
        
        with edit_col2:
            edit_weight = st.number_input(
                "Weight (kg)",
                min_value=20.0,
                max_value=250.0,
                value=float(user_data.get('weight', 70))
            )
            
            edit_activity = st.selectbox(
                "Activity Level",
                options=["Sedentary", "Lightly Active", "Moderately Active", "Very Active"],
                index=["sedentary", "lightly active", "moderately active", "very active"].index(user_data.get('activity_level', 'moderately active').lower())
                if user_data.get('activity_level', 'moderately active').lower() in ["sedentary", "lightly active", "moderately active", "very active"] else 2
            )
            
            edit_diet = st.selectbox(
                "Diet Preference",
                options=["Vegetarian", "Non-Vegetarian", "Both", "Vegan"],
                index=["vegetarian", "non-vegetarian", "both", "vegan"].index(user_data.get('diet', 'both').lower())
                if user_data.get('diet', 'both').lower() in ["vegetarian", "non-vegetarian", "both", "vegan"] else 2
            )
            
            edit_goal = st.selectbox(
                "Goal",
                options=["Weight Loss", "Weight Gain", "Maintain Weight", "Muscle Gain", "Not specified"],
                index=["weight loss", "weight gain", "maintain weight", "muscle gain", "not specified"].index(user_data.get('goal', 'not specified').lower())
                if user_data.get('goal', 'not specified').lower() in ["weight loss", "weight gain", "maintain weight", "muscle gain", "not specified"] else 4
            )
        
        with edit_col3:
            # Get current allergies and join them with commas for the text input
            current_allergies = user_data.get('allergies', [])
            allergies_str = ", ".join(current_allergies) if current_allergies else ""
            
            edit_allergies = st.text_input(
                "Food Allergies (comma-separated)",
                value=allergies_str,
                placeholder="e.g., nuts, dairy, shellfish"
            )
            
            # In a real app, you'd get these from a database or API
            cuisine_options = ["Italian", "Mexican", "Chinese", "Indian", "Japanese", 
                               "Mediterranean", "Thai", "American", "French", "Greek"]
            
            edit_cuisines = st.multiselect(
                "Preferred Cuisines (optional)",
                options=cuisine_options,
                default=user_data.get('preferred_cuisines', [])
            )
            
            edit_health = st.text_area(
                "Any health conditions? (or 'None')",
                value=user_data.get('health_conditions', 'None')
            )
        
        update_profile_button = st.form_submit_button(label="Update Profile")
        
        if update_profile_button:
            # Process allergies list
            allergies_list = [a.strip() for a in edit_allergies.split(',')] if edit_allergies else []
            
            # Create updated data dictionary
            updated_data = {
                "name": f"{edit_first_name.strip().lower()} {edit_last_name.strip().lower()}",
                "gender": edit_gender.lower(),
                "age": int(edit_age),
                "height": float(edit_height),
                "weight": float(edit_weight),
                "activity_level": edit_activity.lower(),
                "diet": edit_diet.lower(),
                "goal": edit_goal,
                "allergies": allergies_list,
                "preferred_cuisines": edit_cuisines,
                "health_conditions": edit_health
            }
            
            success, message = update_user(user_id, updated_data)
            if success:
                st.success(message)
                # Refresh the page to show updated profile
                st.rerun()
            else:
                st.error(message)
    
    # Delete profile option
    st.subheader("Delete Profile")
    st.warning("Warning: This action cannot be undone. All profile data will be permanently deleted.")
    
    if st.button("Delete Profile", key="delete_profile_button"):
        st.warning("Are you sure you want to delete your profile? This cannot be undone.")
        delete_col1, delete_col2 = st.columns(2)
        
        with delete_col1:
            if st.button("Yes, Delete", key="confirm_delete_button"):
                success, message = delete_user(user_id)
                if success:
                    st.success(message)
                    # Reset current user and redirect to home
                    st.session_state.current_user = None
                    st.rerun()
                else:
                    st.error(message)
        
        with delete_col2:
            if st.button("No, Cancel", key="cancel_delete_button"):
                st.info("Profile deletion canceled.")

def create_profile(user_data):
    st.subheader("Complete Your Profile")

    with st.form(key="create_profile_form"):
        # Split form into columns for better layout
        col1, col2, col3 = st.columns(3)
        
        with col1:
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            
            gender = st.selectbox(
                "Gender",
                options=["Male", "Female", "Other"]
            )
            
            age = st.number_input(
                "Age",
                min_value=10,
                max_value=100,
                value=30
            )
            
            height = st.number_input(
                "Height in cm",
                min_value=50.0,
                max_value=250.0,
                value=170.0
            )
        
        with col2:
            weight = st.number_input(
                "Weight in kg",
                min_value=20.0,
                max_value=250.0,
                value=70.0
            )
            
            activity_level = st.selectbox(
                "Activity Level",
                options=["Sedentary", "Lightly Active", "Moderately Active", "Very Active"],
                index=2  # Default to Moderately Active
            )
            
            diet_preference = st.selectbox(
                "Diet Preference",
                options=["Vegetarian", "Non-Vegetarian", "Both", "Vegan"]
            )
            
            goal = st.selectbox(
                "Goal",
                options=["Weight Loss", "Weight Gain", "Maintain Weight", "Muscle Gain", "Not specified"]
            )
            
        with col3:
            allergies = st.text_input(
                "Food Allergies (comma-separated)",
                placeholder="e.g., nuts, dairy, shellfish"
            )
            
            # In a real app, you'd get these from a database or API
            cuisine_options = ["Italian", "Mexican", "Chinese", "Indian", "Japanese", 
                               "Mediterranean", "Thai", "American", "French", "Greek"]
            
            preferred_cuisines = st.multiselect(
                "Preferred Cuisines (optional)",
                options=cuisine_options
            )
            
            health_conditions = st.text_area(
                "Any health conditions? (or 'None')"
            )
        
        submit_button = st.form_submit_button(label="Save Profile")

        if submit_button:
            if not first_name or not last_name:
                st.error("Please enter both first and last name.")
            else:
                allergies_list = [a.strip() for a in allergies.split(',')] if allergies else []

                updated_data = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "gender": gender.lower(),
                    "age": int(age),
                    "height": float(height),
                    "weight": float(weight),
                    "diet": diet_preference.lower(),
                    "goal": goal,
                    "activity_level": activity_level.lower(),
                    "allergies": allergies_list,
                    "preferred_cuisines": preferred_cuisines,
                    "health_conditions": health_conditions,
                    "profile_complete": True
                }

                success, message = update_user(user_id, updated_data)
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

if __name__ == "__main__":
    main()
