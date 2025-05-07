import streamlit as st
import pandas as pd
import numpy as np
from utils.recommendations import recommend_exercises, load_user_ratings, save_user_ratings
from utils.user_management import get_user
from utils.visualization import create_exercise_distribution_chart
from utils.data_processing import load_exercise_data
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
    sidebar(current_page="🍽️ Meal Planner")
    # Check if user is logged in
    if not st.session_state.current_user:
        st.warning("Please create or select a profile to get personalized exercise recommendations.")
        st.info("Go to the Profile page to create or select a profile.")
        
        # Show demo version with limited functionality
        st.subheader("Demo Version")
        st.markdown("Try out the exercise recommendations with default settings:")
        
        # Create a default user profile for demo
        default_user = {
            "user_id": "demo_user",
            "name": "Demo User",
            "gender": "male",
            "height": 170,
            "weight": 70,
            "age": 30,
            "activity_level": "Moderately Active",
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
    
    # Initialize exercise_data in session state if not already present
    if 'exercise_data' not in st.session_state:
        st.session_state.exercise_data = load_exercise_data()
    
    # Display user info
    st.subheader(f"Exercise Recommendations for {user_data.get('name', 'User').title()}")
    
    user_col1, user_col2, user_col3 = st.columns(3)
    
    with user_col1:
        st.markdown(f"**Age:** {user_data.get('age', 30)}")
    
    with user_col2:
        st.markdown(f"**Gender:** {user_data.get('gender', 'male')}")
    
    with user_col3:
        st.markdown(f"**Goal:** {user_data.get('goal', 'Not specified')}")
    
    with user_col1:
        st.markdown(f"**Health Status:** {user_data.get('health_status', 'Not specified')}")
    
    with user_col2:
        st.markdown(f"**Health Conditions:** {user_data.get('health_conditions', 'None')}")
    
    # Main content area
    tab1, tab2 = st.tabs(["Personalized Program", "Exercise Library"])
    
    with tab1:
        # Display personalized recommendations
        display_exercise_recommendations(user_data)
    
    with tab2:
        # Exercise library search and filters
        st.markdown("### Exercise Library")
        
        # Search and filters
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_term = st.text_input("Search exercises", "")
        with col2:
            filter_type = st.selectbox(
                "Exercise Type",
                ["All"] + list(st.session_state.exercise_data['Type'].unique())
            )
        with col3:
            filter_level = st.selectbox(
                "Difficulty Level",
                ["All"] + list(st.session_state.exercise_data['Level'].unique())
            )
        
        # Add search button
        search_button = st.button("Search Exercises")
        
        # Display filtered exercises only if search button is clicked
        if search_button:
            # Filter exercises
            filtered_df = filter_exercises(
                st.session_state.exercise_data,
                search_term,
                filter_type,
                filter_level
            )
            
            # Display filtered exercises
            if not filtered_df.empty:
                # Sort by rating
                filtered_df = filtered_df.sort_values('Rating', ascending=False)
                
                # Group by body part
                body_parts = filtered_df['BodyPart'].unique()
                
                for body_part in body_parts:
                    with st.expander(f"{body_part} Exercises"):
                        body_part_exercises = filtered_df[filtered_df['BodyPart'] == body_part]
                        
                        for _, exercise in body_part_exercises.iterrows():
                            with st.container():
                                st.markdown(
                                    f"**{exercise['Title']} - {exercise['Level']} "
                                    f"({exercise['Rating']}/10 Rating)**"
                                )
                                display_exercise_details(exercise.to_dict(), user_data=user_data)
                                st.markdown("---")  # Divider for visual separation
            else:
                st.info("No exercises found matching your criteria.")

def filter_exercises(exercise_data, search_term, filter_type, filter_level):
    """
    Filter exercises based on search term, type, and level
    """
    if exercise_data.empty:
        return pd.DataFrame()
    
    # Start with all exercises
    filtered_df = exercise_data.copy()
    
    # Apply type filter
    if filter_type != "All":
        filtered_df = filtered_df[filtered_df['Type'] == filter_type]
    
    # Apply level filter
    if filter_level != "All":
        filtered_df = filtered_df[filtered_df['Level'] == filter_level]
    
    # Apply search filter
    if search_term:
        search_mask = (
            filtered_df['Title'].str.contains(search_term, case=False, na=False) |
            filtered_df['BodyPart'].str.contains(search_term, case=False, na=False) |
            filtered_df['Equipment'].str.contains(search_term, case=False, na=False) |
            filtered_df['Desc'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[search_mask]
    
    return filtered_df

def display_exercise_content(exercise, context_id, user_data=None):
    """
    Display detailed content for a single exercise with enhanced UI and information
    """
    if not exercise:
        st.warning("Exercise details not available")
        return
    
    # Create two columns for layout
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Main exercise information
        st.markdown(f"#### {exercise.get('name', exercise.get('Title', 'Unknown'))}")
        st.markdown(f"**Type:** {exercise.get('type', exercise.get('Type', 'Unknown'))}")
        st.markdown(f"**Body Part:** {exercise.get('main_muscle', exercise.get('BodyPart', 'Unknown'))}")
        st.markdown(f"**Equipment:** {exercise.get('equipment', exercise.get('Equipment', 'None'))}")
        st.markdown(f"**Level:** {exercise.get('level', exercise.get('Level', 'Unknown'))}")
        
        # Description
        if exercise.get('description', exercise.get('Desc')):
            st.markdown("**Exercise Description**")
            with st.container():
                st.markdown(exercise.get('description', exercise.get('Desc', '')))
    
    with col2:
        # Rating and parameters
        if exercise.get('rating', exercise.get('Rating')):
            st.metric("Exercise Rating", f"{exercise.get('rating', exercise.get('Rating', 'N/A'))}")
        if exercise.get('rating_desc', exercise.get('RatingDesc')):
            st.info(exercise.get('rating_desc', exercise.get('RatingDesc', '')))
        
        # Display exercise parameters based on level
        level = exercise.get('level', exercise.get('Level', '')).lower()
        st.markdown("### Exercise Parameters")
        
        if 'beginner' in level:
            display_level_parameters('low')
        elif 'expert' in level:
            display_level_parameters('high')
        else:
            display_level_parameters('moderate')
    
    # Exercise tips and form guidance
    st.markdown("---")
    st.markdown("**Form & Safety Tips**")
    with st.container():
        display_exercise_tips(exercise)

    # Store and manage rating in session state
    exercise_name = exercise.get('name', exercise.get('Title', 'Unknown'))
    rating_key = f"rating_{exercise_name}_{context_id}"
    saved_rating_key = f"saved_rating_{exercise_name}_{context_id}"

    # Initialize saved rating in session state if not present
    if saved_rating_key not in st.session_state:
        ratings_df = load_user_ratings()
        existing_rating = ratings_df[(ratings_df['user_id'] == st.session_state.get('current_user', 'demo_user')) & 
                                    (ratings_df['exercise_title'] == exercise_name)]['rating']
        st.session_state[saved_rating_key] = int(existing_rating.iloc[0]) if not existing_rating.empty else 3

    # Rating slider using the saved rating as the initial value
    current_rating = st.slider(f"Rate {exercise_name}", 1, 5, st.session_state[saved_rating_key], key=rating_key)
    
    # Save button to commit rating
    if st.button("Save Rating", key=f"save_{rating_key}"):
        user_id = st.session_state.get('current_user', 'demo_user')
        ratings_df = load_user_ratings()
        # Check if rating already exists for this user and exercise
        mask = (ratings_df['user_id'] == user_id) & (ratings_df['exercise_title'] == exercise_name)
        if mask.any():
            ratings_df.loc[mask, 'rating'] = current_rating
        else:
            new_rating = pd.DataFrame([{'user_id': user_id, 'exercise_title': exercise_name, 'rating': current_rating}])
            ratings_df = pd.concat([ratings_df, new_rating], ignore_index=True)
        ratings_df = ratings_df.drop_duplicates(subset=['user_id', 'exercise_title'], keep='last')
        save_user_ratings(ratings_df)
        # Update the saved rating in session state
        st.session_state[saved_rating_key] = current_rating
        st.success(f"Rating saved for {exercise_name}!")

def display_exercise_details(exercise, user_data=None):
    """
    Display comprehensive exercise details with enhanced visualization and instructions
    """
    if not exercise or not isinstance(exercise, dict) or not exercise.get('Title'):
        st.warning("Exercise details not available")
        return
    
    # Create tabs for different aspects of the exercise
    tabs = st.tabs(["Overview", "Instructions", "Form & Technique", "Variations"])
    
    with tabs[0]:  # Overview
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"### {exercise['Title']}")
            st.markdown(f"**Type:** {exercise['Type']}")
            # Add appropriate icons based on exercise type
            if 'Stretching' in exercise['Type']:
                st.markdown("🧘‍♂️ **Flexibility & Mobility**")
            elif any(x in exercise['Type'] for x in ['Cardio', 'HIIT']):
                st.markdown("🏃‍♂️ **Cardiovascular Exercise**")
            elif any(x in exercise['Type'] for x in ['Strength', 'Olympic Weightlifting', 'Plyometrics', 'Powerlifting', 'Strongman']):
                st.markdown("💪 **Strength Training**")
            st.markdown(f"**Body Part:** {exercise['BodyPart']}")
            st.markdown(f"**Equipment:** {exercise['Equipment']}")
            st.markdown(f"**Level:** {exercise['Level']}")
            
            if pd.notna(exercise['Rating']):
                st.metric("Rating", f"{exercise['Rating']}/10")
            if pd.notna(exercise['RatingDesc']):
                st.info(exercise['RatingDesc'])
        
        with col2:
            # Display exercise parameters based on level
            st.markdown("### Parameters")
            level = exercise['Level'].lower()
            display_level_parameters('high' if 'Expert' in level else 'low' if 'Beginner' in level else 'moderate')
    
    with tabs[1]:  # Instructions
        st.markdown("### Exercise Instructions")
        
        # Description
        if pd.notna(exercise['Desc']):
            with st.container():
                st.markdown(exercise['Desc'])
        
        # Common mistakes and corrections (removed expander, displayed directly)
        st.markdown("**Common Mistakes & Corrections:**")
        display_common_mistakes(exercise['Type'])
    
    with tabs[2]:  # Form & Technique
        st.markdown("### Proper Form & Technique")
        display_form_technique(exercise, user_data)
    
    with tabs[3]:  # Variations
        st.markdown("### Exercise Variations")
        display_exercise_variations(exercise)

def display_level_parameters(intensity):
    """Display exercise parameters based on intensity level"""
    if intensity == 'low':
        st.markdown("""
        - Sets: 2-3
        - Reps: 12-15
        - Rest: 60-90 seconds
        - Intensity: 50-60% of max
        """)
    elif intensity == 'high':
        st.markdown("""
        - Sets: 4-5
        - Reps: 8-10
        - Rest: 90-120 seconds
        - Intensity: 70-85% of max
        """)
    else:  # moderate
        st.markdown("""
        - Sets: 3-4
        - Reps: 10-12
        - Rest: 60-90 seconds
        - Intensity: 60-70% of max
        """)

def display_exercise_tips(exercise):
    """Display exercise-specific tips and form guidance"""
    st.markdown("**Key Points to Remember:**")
    
    # General tips
    general_tips = [
        "Maintain proper breathing throughout",
        "Keep core engaged for stability",
        "Stop if you feel sharp or sudden pain"
    ]
    
    # Exercise-specific tips based on type
    specific_tips = get_exercise_specific_tips(exercise.get('type', exercise.get('Type', '')))
    
    # Display all tips
    for tip in general_tips + specific_tips:
        st.markdown(f"- {tip}")

def get_exercise_specific_tips(exercise_type):
    """Get tips specific to exercise type"""
    if 'Strength' in exercise_type:
        return [
            "Control the movement in both directions",
            "Keep proper alignment throughout",
            "Focus on mind-muscle connection"
        ]
    elif 'Cardio' in exercise_type:
        return [
            "Stay hydrated",
            "Monitor your heart rate",
            "Maintain good posture"
        ]
    else:  # Flexibility
        return [
            "Don't bounce in stretches",
            "Breathe deeply and regularly",
            "Hold stretches for recommended duration"
        ]

def display_common_mistakes(exercise_type):
    """Display common mistakes and corrections based on exercise type"""
    common_mistakes = {
        'Strength': [
            "Using momentum instead of controlled movement",
            "Poor form to lift heavier weights",
            "Incomplete range of motion"
        ],
        'Cardio': [
            "Moving too fast with poor form",
            "Not maintaining proper posture",
            "Inconsistent breathing pattern"
        ],
        'Flexibility': [
            "Bouncing during stretches",
            "Pushing too hard too fast",
            "Holding breath during stretches"
        ]
    }
    
    # Get relevant mistakes based on exercise type
    mistakes = common_mistakes.get(
        next((k for k in common_mistakes.keys() if k in exercise_type), 'Strength')
    )
    
    for mistake in mistakes:
        st.markdown(f"- {mistake}")

def display_form_technique(exercise, user_data=None):
    """Display form and technique guidance"""
    # Key form points
    st.markdown("**Key Form Points:**")
    exercise_type = exercise.get('type', exercise.get('Type', ''))
    form_points = get_form_points_by_type(exercise_type)  # Use local helper function
    for point in form_points:
        st.markdown(f"- {point}")
    
    # Breathing pattern
    st.markdown("**Breathing Pattern:**")
    if 'Strength' in exercise_type:
        st.markdown("""
        - Exhale during exertion
        - Inhale during the easier phase
        - Maintain consistent rhythm
        """)
    elif 'Cardio' in exercise_type:
        st.markdown("""
        - Maintain steady breathing
        - Match breath to movement
        - Focus on deep breaths
        """)
    else:  # Flexibility
        st.markdown("""
        - Deep, slow breaths
        - Exhale as you stretch
        - Never hold your breath
        """)

def get_form_points_by_type(exercise_type):
    """Get form points based on exercise type"""
    if 'Strength' in exercise_type:
        return [
            "Maintain a neutral spine",
            "Keep joints aligned",
            "Engage the target muscle group"
        ]
    elif 'Cardio' in exercise_type:
        return [
            "Land softly to reduce impact",
            "Keep movements controlled",
            "Avoid overstriding"
        ]
    else:  # Flexibility
        return [
            "Move into stretches slowly",
            "Avoid forcing the stretch",
            "Focus on the target area"
        ]

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
        if st.session_state.exercise_data.empty:
            st.error("No exercise data available to generate recommendations.")
            return
        exercise_recommendations = recommend_exercises(user_data, st.session_state.exercise_data, num_recommendations=10)
    
    if "error" in exercise_recommendations:
        st.error(exercise_recommendations["error"])
        return
    
    # Apply filters from user_data
    filtered_recommendations = {
        'Strength': [],
        'Cardio': [],
        'Flexibility': []
    }
    
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
            main_muscle = exercise.get('main_muscle', '').lower()
            
            if any(muscle in main_muscle for muscle in ['shoulders', 'chest', 'upper back', 'lats', 'biceps', 'triceps', 'forearms', 'trapezius']):
                upper_body_exercises.append(exercise)
            elif any(muscle in main_muscle for muscle in ['quadriceps', 'hamstrings', 'glutes', 'calves', 'adductors', 'abductors']):
                lower_body_exercises.append(exercise)
            elif any(muscle in main_muscle for muscle in ['abdominals', 'obliques', 'lower back', 'core']):
                core_exercises.append(exercise)
            else:
                upper_body_exercises.append(exercise)
    
    # Assign different exercise types to different days based on user goal
    with day_tabs[0]:  # Monday - Upper Body
        st.markdown("### Upper Body Strength")
        if upper_body_exercises:
            # Limit to 3 exercises for the day
            display_exercises = upper_body_exercises[:3]
            for i, exercise in enumerate(display_exercises):
                with st.expander(f"{i+1}. {exercise['name']} - {exercise['main_muscle']}"):
                    display_exercise_content(exercise, context_id=f"monday_{i}", user_data=user_data)
        else:
            st.info("No upper body exercises available.")
    
    with day_tabs[1]:  # Tuesday - Cardio
        st.markdown("### Cardio Focus")
        if 'Cardio' in exercise_recommendations and exercise_recommendations['Cardio']:
            for i, exercise in enumerate(exercise_recommendations['Cardio'][:3]):
                with st.expander(f"{i+1}. {exercise['name']} - {exercise['main_muscle']}"):
                    display_exercise_content(exercise, context_id=f"tuesday_{i}", user_data=user_data)
        else:
            st.info("No cardio exercises available.")
    
    with day_tabs[2]:  # Wednesday - Core
        st.markdown("### Core Strength & Flexibility")
        
        # First display core exercises
        core_display_count = min(2, len(core_exercises))
        if core_display_count > 0:
            for i, exercise in enumerate(core_exercises[:core_display_count]):
                with st.expander(f"{i+1}. {exercise['name']} - {exercise['main_muscle']}"):
                    display_exercise_content(exercise, context_id=f"wednesday_core_{i}", user_data=user_data)
        
        # Then add some flexibility exercises
        flex_display_count = 3 - core_display_count
        if 'Flexibility' in exercise_recommendations and exercise_recommendations['Flexibility'] and flex_display_count > 0:
            for i, exercise in enumerate(exercise_recommendations['Flexibility'][:flex_display_count]):
                with st.expander(f"{i+1 + core_display_count}. {exercise['name']} - {exercise['main_muscle']}"):
                    display_exercise_content(exercise, context_id=f"wednesday_flex_{i}", user_data=user_data)
        
        if core_display_count == 0 and flex_display_count == 0:
            st.info("No core or flexibility exercises available.")
    
    with day_tabs[3]:  # Thursday - Lower Body
        st.markdown("### Lower Body Strength")
        if lower_body_exercises:
            # Limit to 3 exercises for the day
            display_exercises = lower_body_exercises[:3]
            for i, exercise in enumerate(display_exercises):
                with st.expander(f"{i+1}. {exercise['name']} - {exercise['main_muscle']}"):
                    display_exercise_content(exercise, context_id=f"thursday_{i}", user_data=user_data)
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
                display_exercise_content(exercise, context_id=f"friday_{i}", user_data=user_data)
        
        if not exercises:
            st.info("No exercises available.")
    
    with day_tabs[5]:  # Saturday
        st.markdown("### Active Recovery")
        if 'Flexibility' in exercise_recommendations and exercise_recommendations['Flexibility']:
            for i, exercise in enumerate(exercise_recommendations['Flexibility'][3:6]):
                with st.expander(f"{i+1}. {exercise['name']} - {exercise['main_muscle']}"):
                    display_exercise_content(exercise, context_id=f"saturday_{i}", user_data=user_data)
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
                    display_exercise_content(exercise, context_id=f"strength_{i}", user_data=user_data)
        else:
            st.info("No strength exercises available.")
    
    with category_tabs[1]:  # Cardio
        if 'Cardio' in exercise_recommendations and exercise_recommendations['Cardio']:
            for i, exercise in enumerate(exercise_recommendations['Cardio']):
                with st.expander(f"{i+1}. {exercise['name']} - {exercise['main_muscle']}"):
                    display_exercise_content(exercise, context_id=f"cardio_{i}", user_data=user_data)
        else:
            st.info("No cardio exercises available.")
    
    with category_tabs[2]:  # Flexibility
        if 'Flexibility' in exercise_recommendations and exercise_recommendations['Flexibility']:
            for i, exercise in enumerate(exercise_recommendations['Flexibility']):
                with st.expander(f"{i+1}. {exercise['name']} - {exercise['main_muscle']}"):
                    display_exercise_content(exercise, context_id=f"flexibility_{i}", user_data=user_data)
        else:
            st.info("No flexibility exercises available.")

def display_exercise_variations(exercise):
    """Display exercise variations based on type and equipment"""
    st.markdown("**Exercise Variations:**")
    
    # Basic progression levels
    st.markdown("Progression Levels:")
    
    variations = {
        'Beginner': [
            "Reduced range of motion",
            "Assisted version",
            "Lower intensity/weight"
        ],
        'Intermediate': [
            "Full range of motion",
            "Standard version",
            "Moderate intensity/weight"
        ],
        'Expert': [
            "Increased time under tension",
            "Added complexity",
            "Higher intensity/weight"
        ]
    }
    
    for level, points in variations.items():
        st.markdown(f"**{level}:**")
        for point in points:
            st.markdown(f"- {point}")
        st.markdown("")  # Add spacing between levels
    
    # Equipment variations
    st.markdown("\n**Equipment Variations:**")
    exercise_type = exercise.get('type', exercise.get('Type', ''))
    if 'Strength' in exercise_type:
        st.markdown("""
        - Bodyweight version
        - Dumbbell variation
        - Resistance band option
        - Barbell variation (if applicable)
        - Cable machine alternative
        """)
    elif 'Cardio' in exercise_type:
        st.markdown("""
        - No equipment version
        - With resistance bands
        - Using cardio machines
        - With weights for added challenge
        """)
    else:  # Flexibility
        st.markdown("""
        - Without equipment
        - Using resistance bands
        - With foam roller
        - Using yoga props
        """)

if __name__ == "__main__":
    main()
