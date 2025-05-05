import streamlit as st
import pandas as pd
import numpy as np
from utils.recommendations import recommend_exercises
from utils.user_management import get_user
from utils.visualization import create_exercise_distribution_chart
from utils.sidebar import sidebar

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
    st.title("🏋️ Exercise Recommendations")
    sidebar(current_page="🏋️ Exercise Recommendations")
    
    # Check if user is logged in
    if not st.session_state.current_user:
        st.warning("Please create or select a profile to get personalized exercise recommendations.")
        st.info("Go to the Profile page to create or select a profile.")
        
        # Show demo version with limited functionality
        st.subheader("Demo Version")
        st.markdown("Try out the exercise recommendations with default settings:")
        
        # Create a default user profile for demo
        default_user = {
            "name": "Demo User",
            "gender": "male",
            "height": 170,
            "weight": 70,
            "goal": "Weight Loss",
            "health_status": "Healthy",
            "health_conditions": "None"
        }
        
        # Display exercise recommendations for demo user
        display_exercise_recommendations(default_user)
        return
    
    # Get user data
    user_id = st.session_state.current_user
    user_data = get_user(user_id)
    
    if not user_data:
        st.error(f"User profile not found. Please create a new profile.")
        return
    
    # Display user info
    st.subheader(f"Exercise Recommendations for {user_data.get('name', 'User').title()}")
    
    user_col1, user_col2, user_col3 = st.columns(3)
    
    with user_col1:
        st.markdown(f"**Goal:** {user_data.get('goal', 'Not specified')}")
    
    with user_col2:
        st.markdown(f"**Health Status:** {user_data.get('health_status', 'Not specified')}")
    
    with user_col3:
        st.markdown(f"**Health Conditions:** {user_data.get('health_conditions', 'None')}")
    
    # Display exercise recommendations
    display_exercise_recommendations(user_data)
    
    # Exercise search and details
    st.subheader("Exercise Database Search")
    
    search_query = st.text_input("Search for an exercise:", placeholder="e.g., squat, bench press, stretch")
    
    if search_query:
        # Filter exercises based on query
        query_lower = search_query.lower()
        filtered_exercises = st.session_state.exercise_data[
            st.session_state.exercise_data["Exercise"].str.lower().str.contains(query_lower, na=False)
        ]
        
        if filtered_exercises.empty:
            st.info(f"No exercises found matching '{search_query}'.")
        else:
            # Display results
            st.markdown(f"Found {len(filtered_exercises)} results for '{search_query}':")
            
            # Display each exercise
            for index, exercise in filtered_exercises.iterrows():
                with st.expander(f"{exercise['Exercise']} - {exercise['Main Muscle']}"):
                    display_exercise_details(exercise)

def display_exercise_recommendations(user_data):
    """
    Display personalized exercise recommendations based on user profile
    """
    # Goal-specific recommendations
    st.markdown("### Recommended Exercise Plan")
    
    goal = user_data.get('goal', '').lower()
    
    if 'weight loss' in goal:
        st.markdown("""
        For **weight loss**, focus on a combination of:
        - Moderate to high-intensity cardio (3-5 days/week)
        - Full-body resistance training (2-3 days/week)
        - Active recovery and flexibility work (1-2 days/week)
        
        This combination helps create a calorie deficit while preserving muscle mass.
        """)
    elif 'muscle gain' in goal:
        st.markdown("""
        For **muscle gain**, focus on:
        - Progressive overload resistance training (4-5 days/week)
        - Moderate cardio for heart health (2-3 days/week)
        - Adequate recovery between muscle group training (48 hours)
        - Stretching and mobility work to prevent injury
        
        Combined with sufficient protein intake and calorie surplus for optimal results.
        """)
    elif 'weight gain' in goal:
        st.markdown("""
        For **weight gain**, focus on:
        - Heavy compound exercises (3-4 days/week)
        - Limited cardio to avoid excessive calorie burn
        - Progressive overload to stimulate muscle growth
        - Adequate recovery between workouts
        
        Remember that nutrition (calorie surplus) is especially important for this goal.
        """)
    else:
        st.markdown("""
        For **general health** and **maintenance**, focus on:
        - Balanced combination of cardio and strength training
        - Variety in exercise selection to engage different muscle groups
        - Consistent activity throughout the week (aim for 30+ minutes daily)
        - Flexibility and mobility work for functional movement
        
        This balanced approach supports overall health and fitness maintenance.
        """)
    
    # Get personalized exercise recommendations
    with st.spinner("Generating exercise recommendations..."):
        exercise_recommendations = recommend_exercises(user_data, st.session_state.exercise_data)
    
    if "error" in exercise_recommendations:
        st.error(exercise_recommendations["error"])
        return
    
    # Display distribution chart
    dist_fig = create_exercise_distribution_chart(exercise_recommendations)
    st.plotly_chart(dist_fig, use_container_width=True)
    
    # Display weekly schedule suggestion
    st.subheader("Suggested Weekly Schedule")
    
    # Create tabs for days of the week
    day_tabs = st.tabs(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    
    # Organize strength exercises by muscle group first to ensure diversity
    upper_body_exercises = []
    core_exercises = []
    lower_body_exercises = []
    
    if 'Strength' in exercise_recommendations and exercise_recommendations['Strength']:
        for exercise in exercise_recommendations['Strength']:
            main_muscle = exercise['main_muscle'].lower() if exercise['main_muscle'] else ''
            
            if any(muscle in main_muscle for muscle in ['shoulder', 'chest', 'back', 'arm', 'deltoid', 'pectoralis', 'trapezius', 'bicep', 'tricep']):
                upper_body_exercises.append(exercise)
            elif any(muscle in main_muscle for muscle in ['hip', 'thigh', 'leg', 'glute', 'calf', 'quadricep', 'hamstring']):
                lower_body_exercises.append(exercise)
            elif any(muscle in main_muscle for muscle in ['abs', 'core', 'waist', 'erector']):
                core_exercises.append(exercise)
            else:
                # Default to upper body if unsure
                upper_body_exercises.append(exercise)
    
    # Assign different exercise types to different days based on user goal
    with day_tabs[0]:  # Monday - Upper Body
        st.markdown("### Upper Body Strength")
        if upper_body_exercises:
            # Limit to 3 exercises for the day
            display_exercises = upper_body_exercises[:3]
            for i, exercise in enumerate(display_exercises):
                with st.expander(f"{i+1}. {exercise['name']} - {exercise['main_muscle']}"):
                    display_exercise_content(exercise)
        else:
            st.info("No upper body exercises available.")
    
    with day_tabs[1]:  # Tuesday - Cardio
        st.markdown("### Cardio Focus")
        if 'Cardio' in exercise_recommendations and exercise_recommendations['Cardio']:
            for i, exercise in enumerate(exercise_recommendations['Cardio'][:3]):
                with st.expander(f"{i+1}. {exercise['name']} - {exercise['main_muscle']}"):
                    display_exercise_content(exercise)
        else:
            st.info("No cardio exercises available.")
    
    with day_tabs[2]:  # Wednesday - Core
        st.markdown("### Core Strength & Flexibility")
        
        # First display core exercises
        core_display_count = min(2, len(core_exercises))
        if core_display_count > 0:
            for i, exercise in enumerate(core_exercises[:core_display_count]):
                with st.expander(f"{i+1}. {exercise['name']} - {exercise['main_muscle']}"):
                    display_exercise_content(exercise)
        
        # Then add some flexibility exercises
        flex_display_count = 3 - core_display_count
        if 'Flexibility' in exercise_recommendations and exercise_recommendations['Flexibility'] and flex_display_count > 0:
            for i, exercise in enumerate(exercise_recommendations['Flexibility'][:flex_display_count]):
                with st.expander(f"{i+1 + core_display_count}. {exercise['name']} - {exercise['main_muscle']}"):
                    display_exercise_content(exercise)
        
        if core_display_count == 0 and flex_display_count == 0:
            st.info("No core or flexibility exercises available.")
    
    with day_tabs[3]:  # Thursday - Lower Body
        st.markdown("### Lower Body Strength")
        if lower_body_exercises:
            # Limit to 3 exercises for the day
            display_exercises = lower_body_exercises[:3]
            for i, exercise in enumerate(display_exercises):
                with st.expander(f"{i+1}. {exercise['name']} - {exercise['main_muscle']}"):
                    display_exercise_content(exercise)
        else:
            st.info("No lower body exercises available.")
    
    with day_tabs[4]:  # Friday - Full Body Circuit
        st.markdown("### Full Body Circuit")
        exercises = []
        
        # Try to get one from each category (upper, lower, core, cardio)
        if upper_body_exercises:
            exercises.append(upper_body_exercises[0])
        if lower_body_exercises:
            exercises.append(lower_body_exercises[0])
        if core_exercises:
            exercises.append(core_exercises[0])
        if 'Cardio' in exercise_recommendations and exercise_recommendations['Cardio']:
            exercises.append(exercise_recommendations['Cardio'][0])
        
        # Limit to 4 max exercises
        exercises = exercises[:4]
        
        for i, exercise in enumerate(exercises):
            with st.expander(f"{i+1}. {exercise['name']} - {exercise['main_muscle']}"):
                display_exercise_content(exercise)
        
        if not exercises:
            st.info("No exercises available.")
    
    with day_tabs[5]:  # Saturday
        st.markdown("### Active Recovery")
        if 'Flexibility' in exercise_recommendations and exercise_recommendations['Flexibility']:
            for i, exercise in enumerate(exercise_recommendations['Flexibility'][3:6]):
                with st.expander(f"{i+1}. {exercise['name']} - {exercise['main_muscle']}"):
                    display_exercise_content(exercise)
        else:
            st.info("No flexibility exercises available.")
    
    with day_tabs[6]:  # Sunday
        st.markdown("### Rest Day")
        st.markdown("""
        Today is your rest day! Rest is crucial for:
        - Muscle recovery and growth
        - Preventing overtraining and injury
        - Mental refreshment
        
        Consider these light activities:
        - Gentle walking
        - Light stretching
        - Yoga or meditation
        - Foam rolling
        """)
    
    # Detailed exercise plan
    st.subheader("Detailed Exercise Recommendations")
    
    # Create tabs for exercise categories
    category_tabs = st.tabs(["Strength Training", "Cardio", "Flexibility & Mobility"])
    
    with category_tabs[0]:  # Strength
        if 'Strength' in exercise_recommendations and exercise_recommendations['Strength']:
            for i, exercise in enumerate(exercise_recommendations['Strength']):
                with st.expander(f"{i+1}. {exercise['name']} - {exercise['main_muscle']}"):
                    display_exercise_content(exercise)
        else:
            st.info("No strength exercises available.")
    
    with category_tabs[1]:  # Cardio
        if 'Cardio' in exercise_recommendations and exercise_recommendations['Cardio']:
            for i, exercise in enumerate(exercise_recommendations['Cardio']):
                with st.expander(f"{i+1}. {exercise['name']} - {exercise['main_muscle']}"):
                    display_exercise_content(exercise)
        else:
            st.info("No cardio exercises available.")
    
    with category_tabs[2]:  # Flexibility
        if 'Flexibility' in exercise_recommendations and exercise_recommendations['Flexibility']:
            for i, exercise in enumerate(exercise_recommendations['Flexibility']):
                with st.expander(f"{i+1}. {exercise['name']} - {exercise['main_muscle']}"):
                    display_exercise_content(exercise)
        else:
            st.info("No flexibility exercises available.")

def display_exercise_content(exercise):
    """
    Display content for a recommended exercise
    """
    st.markdown(f"**Type:** {exercise['type']}")
    st.markdown(f"**Main Muscle:** {exercise['main_muscle']}")
    
    if exercise['target_muscles']:
        st.markdown(f"**Target Muscles:** {exercise['target_muscles']}")
        
    if exercise['synergist_muscles']:
        st.markdown(f"**Synergist Muscles:** {exercise['synergist_muscles']}")
    
    if exercise['preparation'] and exercise['preparation'] != '0':
        st.markdown("**Preparation:**")
        st.markdown(exercise['preparation'])
    
    if exercise['execution'] and exercise['execution'] != '0':
        st.markdown("**Execution:**")
        st.markdown(exercise['execution'])
    
    # Add tips based on exercise type
    if 'Stretch' in exercise['type']:
        st.info("Hold this stretch for 20-30 seconds, breathing deeply. Repeat 2-3 times on each side if applicable.")
    elif 'Cardio' in exercise['type'] or 'HIIT' in exercise['type']:
        st.info("Adjust intensity based on your fitness level. Start with shorter durations and gradually increase.")
    elif 'Strength' in exercise['type'] or 'Weight' in exercise['type']:
        st.info("Focus on proper form before increasing weight. Aim for 8-12 reps for hypertrophy, 4-6 reps for strength.")

def display_exercise_details(exercise):
    """
    Display detailed information about an exercise
    """
    st.markdown(f"**Equipment Type:** {exercise['Equipment Type']}")
    st.markdown(f"**Main Muscle:** {exercise['Main Muscle']}")
    
    if not pd.isna(exercise['Target Muscles']):
        st.markdown(f"**Target Muscles:** {exercise['Target Muscles']}")
        
    if not pd.isna(exercise['Synergist Muscles']):
        st.markdown(f"**Synergist Muscles:** {exercise['Synergist Muscles']}")
    
    if not pd.isna(exercise['Preparation']) and exercise['Preparation'] != '0':
        st.markdown("**Preparation:**")
        st.markdown(exercise['Preparation'])
    
    if not pd.isna(exercise['Execution']) and exercise['Execution'] != '0':
        st.markdown("**Execution:**")
        st.markdown(exercise['Execution'])
    
    # Add appropriate icons based on exercise type
    if 'Stretch' in exercise['Equipment Type']:
        st.markdown("🧘‍♂️ **Flexibility & Mobility**")
    elif any(x in exercise['Equipment Type'] for x in ['Cardio', 'HIIT']):
        st.markdown("🏃‍♂️ **Cardiovascular Exercise**")
    elif any(x in exercise['Equipment Type'] for x in ['Strength', 'Weight', 'Resistance']):
        st.markdown("💪 **Strength Training**")

if __name__ == "__main__":
    main()
