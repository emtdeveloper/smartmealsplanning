import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from utils.db import users_collection
from utils.sidebar import sidebar
from utils.data_processing import load_food_data, load_exercise_data, load_user_records, load_optimized_meals

# Set page configuration
st.set_page_config(
    page_title="Smart Meal Planning & Health Assistant",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Initialize session state variables if they don't exist
if 'food_data' not in st.session_state:
    st.session_state.food_data = load_food_data()

if 'exercise_data' not in st.session_state:
    st.session_state.exercise_data = load_exercise_data()

if 'optimized_meals' not in st.session_state:
    st.session_state.optimized_meals = load_optimized_meals()

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False


# Main app
def main():
    st.title("🥗 Smart Meal Planning & Health Assistant")
    sidebar(current_page="🏠 Home")
    
    # App description
    st.markdown("""
    Welcome to your personalized health and nutrition assistant! 
    This application helps you create meal plans tailored to your dietary preferences and health goals,
    while providing exercise recommendations and nutritional guidance through our chatbot.
    
    ### 🌟 Key Features:
    - 📊 Profile management with health metrics tracking
    - 🍽️ AI-driven meal recommendations based on your preferences and goals
    - 🏋️ Exercise suggestions tailored to your fitness level
    - 💬 Nutritional guidance through our conversational chatbot
    - 📈 Progress tracking to keep you motivated
    
    Get started by creating or selecting your profile in the sidebar!
    """)

    # Create login / signup button
    if not st.session_state.get("logged_in", False):
        with st.container():
            # Outer container controls alignment
            left_space, main_content, right_space = st.columns([0.01, 1, 2])

            with main_content:
                st.markdown("""
                    <div style="padding: 1rem; background-color: #262730; border-radius: 10px; width: 445px;">
                        <h4 style="color: #fafafa; text-align: center;">Please log in or sign up to access features.</h4>
                    </div>
                """, unsafe_allow_html=True)

                st.write("")  # small vertical space

                # Now create two small button columns inside the main column
                button_col1, button_col2 = st.columns([1, 1])

                with button_col1:
                    if st.button("🔐 Login", use_container_width=True):
                        st.switch_page("pages/00_Login.py")

                with button_col2:
                    if st.button("🔑 Sign Up", use_container_width=True):
                        st.switch_page("pages/01_Signup.py")
    
    # Featured statistics or insights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Total Foods in Database", value=f"{len(st.session_state.food_data):,}")
    
    with col2:
        st.metric(label="Exercise Routines Available", value=f"{len(st.session_state.exercise_data):,}")
    
    with col3:
        user_count = users_collection.count_documents({})
        st.metric(label="Active User Profiles", value=user_count)
    
    # Quick actions
    st.subheader("Quick Actions")
    
    quick_action_cols = st.columns(3)
    
    with quick_action_cols[0]:
        if st.button("🏋️ Get an Exercise", use_container_width=True):
            st.switch_page("pages/04_Exercise_Recommendations.py")
    
    with quick_action_cols[1]:
        if st.button("🍽️ Plan Your Meals", use_container_width=True):
            st.switch_page("pages/03_Meal_Planner.py")
    
    with quick_action_cols[2]:
        if st.button("💬 Chat with Assistant", use_container_width=True):
            st.switch_page("pages/05_Chatbot.py")
    
    # Featured meal of the day (random selection)
    st.subheader("Featured Healthy Meal Idea")
    
    # Select a random healthy food item
    if not st.session_state.food_data.empty:
        # Filter for foods with reasonable calorie count and good nutritional value
        healthy_foods = st.session_state.food_data[
            (st.session_state.food_data['Calories'] > 0) & 
            (st.session_state.food_data['Calories'] < 500) &
            (st.session_state.food_data['Protein'] > 5)
        ]
        
        if not healthy_foods.empty:
            random_food = healthy_foods.sample(1).iloc[0]
            
            food_col1, food_col2 = st.columns([1, 2])
            
            with food_col1:
                # Food icon based on name
                st.markdown(f"### 🍲 {random_food['Food Name']}")
                st.markdown(f"**Calories:** {random_food['Calories']:.0f} kcal")
                st.markdown(f"**Protein:** {random_food['Protein']:.1f}g")
                st.markdown(f"**Carbs:** {random_food['Carbs']:.1f}g")
                st.markdown(f"**Fat:** {random_food['Total Fat']:.1f}g")
            
            with food_col2:
                # Nutritional breakdown as a bar chart
                nutrients = ['Protein', 'Carbs', 'Total Fat', 'Dietary Fiber']
                values = [random_food[nutrient] for nutrient in nutrients]
                
                # Create a simple bar chart
                chart_data = pd.DataFrame({
                    'Nutrient': nutrients,
                    'Amount (g)': values
                })
                
                st.bar_chart(chart_data.set_index('Nutrient'))
    
    # Health tip of the day
    health_tips = [
        "Stay hydrated! Aim to drink at least 8 glasses of water daily.",
        "Include a variety of colorful vegetables in your meals for a range of nutrients.",
        "Take short walking breaks throughout the day to reduce sedentary time.",
        "Practice mindful eating by savoring each bite and avoiding distractions during meals.",
        "Aim for 7-9 hours of quality sleep to support your overall health.",
        "Include protein in every meal to help maintain muscle mass and feel fuller longer.",
        "Prepare meals at home when possible to control ingredients and portion sizes.",
        "Balance your plate with 1/2 vegetables, 1/4 protein, and 1/4 whole grains.",
        "Listen to your body's hunger and fullness cues rather than strict meal timing.",
        "Small, consistent changes are more sustainable than drastic diet overhauls."
    ]
    
    st.info(f"💡 **Tip of the Day:** {np.random.choice(health_tips)}")

# Run the app
if __name__ == "__main__":
    main()