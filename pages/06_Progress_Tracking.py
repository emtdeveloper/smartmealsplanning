import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from utils.db import journal_collection
from utils.user_management import get_user, update_user_progress
from utils.visualization import create_weight_progress_chart, create_bmi_chart
from utils.sidebar import sidebar
from utils.data_processing import load_journal_entry

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
    st.title("📈 Progress Tracking")
    sidebar(current_page="📈 Progress Tracking")
    
    # Check if user is logged in
    if not st.session_state.current_user:
        st.warning("Please create or select a profile to track your progress.")
        st.info("Go to the Profile page to create or select a profile.")
        
    
    
    # Get user data
    user_id = st.session_state["current_user"]
    user_data = get_user(user_id)

    
    if not user_data:
        st.error(f"User profile not found. Please create a new profile.")
        return
    
    # Display user info
    st.subheader(f"🌞 Greetings, {user_data.get('username', 'User').title()}")
    
    # Overview metrics
    display_overview_metrics(user_data)
    
    # Progress charts
    display_progress_charts(user_data)
    
    # Quick update form
    st.subheader("Quick Update")
    
    with st.form(key="quick_update_form"):
        update_col1, update_col2 = st.columns(2)
        
        with update_col1:
            current_weight = st.number_input(
                "Current Weight (kg)",
                min_value=20.0,
                max_value=250.0,
                value=float(user_data.get('weight', 70.0))
            )
        
        with update_col2:
            # Calculate days since last update
            last_update = "No previous updates"
            if user_data.get('progress_history') and len(user_data['progress_history']) > 0:
                last_entry = user_data['progress_history'][-1]
                if 'timestamp' in last_entry:
                    last_update_time = datetime.strptime(last_entry['timestamp'], "%Y-%m-%d %H:%M:%S")
                    days_since = (datetime.now() - last_update_time).days
                    last_update = f"{days_since} days ago" if days_since > 0 else "Today"
            
            st.markdown(f"**Last Update:** {last_update}")
            st.markdown(f"**Current Weight:** {user_data.get('weight', 'N/A')} kg")
            st.markdown(f"**Current BMI:** {user_data.get('bmi', 'N/A')}")
        
        update_button = st.form_submit_button(label="Update Progress")
        
        if update_button:
            success, message = update_user_progress(user_id, current_weight)
            if success:
                st.success(message)
                # Refresh the page to show updated data
                st.rerun()
            else:
                st.error(message)
    
    # Goal tracking
    display_goal_tracking(user_data)
    
    # Progress journal
    st.subheader("Progress Journal")
    
    journal_entry = st.text_area(
        "Record your thoughts, challenges, or achievements",
        placeholder="e.g., Feeling stronger today! Completed my workout and stayed within my calorie goal."
    )
    
    if st.button("Save Journal Entry"):
        success, msg = load_journal_entry(user_id, journal_entry)
        if success:
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    # Display recent journal entries
    st.subheader("Journal History")

    journal_entries = journal_collection.find({"user_id": user_id}).sort("_id", -1)

    for entry in journal_entries:
        st.markdown(f"""
        **🕒 {entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}**
        
        {entry['entry']}
        """)

    
    # Full progress history
    display_full_history(user_data)

def display_overview_metrics(user_data):
    """
    Display overview metrics for the user
    """
    # Create columns for metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Current Weight",
            value=f"{user_data.get('weight', 0):.1f} kg"
        )
    
    with col2:
        st.metric(
            label="Current BMI",
            value=f"{user_data.get('bmi', 0):.1f}",
            delta=get_bmi_delta(user_data)
        )
    
    with col3:
        st.metric(
            label="Health Status",
            value=user_data.get('health_status', 'N/A')
        )

def get_bmi_delta(user_data):
    """
    Calculate BMI change from previous entry
    """
    progress_history = user_data.get('progress_history', [])
    
    if len(progress_history) > 1:
        current_bmi = progress_history[-1].get('bmi', 0)
        previous_bmi = progress_history[-2].get('bmi', 0)
        
        delta = current_bmi - previous_bmi
        return f"{delta:.2f}"
    
    return None

def display_progress_charts(user_data):
    """
    Display progress charts for the user
    """
    st.subheader("Progress Visualization")
    
    # Create tabs for different charts
    chart_tabs = st.tabs(["Weight History", "BMI", "Trends"])
    
    with chart_tabs[0]:
        progress_history = user_data.get('progress_history', [])
        if progress_history:
            weight_fig = create_weight_progress_chart(progress_history)
            st.plotly_chart(weight_fig, use_container_width=True, key="weight_chart_progress_tab")
            
            # Add insight about weight change
            if len(progress_history) > 1:
                first_weight = progress_history[0].get('weight', 0)
                current_weight = progress_history[-1].get('weight', 0)
                total_change = current_weight - first_weight
                
                if abs(total_change) > 0.1:  # Only show if there's a meaningful change
                    change_text = "lost" if total_change < 0 else "gained"
                    st.info(f"You have {change_text} {abs(total_change):.1f} kg since you started tracking.")
        else:
            st.info("No weight history available. Update your progress to see charts.")
    
    with chart_tabs[1]:
        bmi = user_data.get('bmi', 0)
        status = user_data.get('health_status', 'Unknown')
        
        bmi_fig = create_bmi_chart(bmi, status)
        st.plotly_chart(bmi_fig, use_container_width=True)
        
        # Add BMI category information
        st.markdown("""
        **BMI Categories:**
        - Underweight: BMI < 18.5
        - Healthy: BMI 18.5-24.9
        - Overweight: BMI 25-29.9
        - Obese: BMI ≥ 30
        
        Note: BMI is just one health indicator and doesn't account for muscle mass, body composition, or other individual factors.
        """)
    
    with chart_tabs[2]:
        progress_history = user_data.get('progress_history', [])
        if progress_history and len(progress_history) > 2:
            # Create a weekly average chart to show trend
            df = pd.DataFrame(progress_history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Create a 7-day moving average
            df['weight_ma'] = df['weight'].rolling(window=min(7, len(df)), min_periods=1).mean()
            
            # Create the trend chart
            trend_fig = px.line(
                df, 
                x='timestamp', 
                y=['weight', 'weight_ma'],
                labels={'timestamp': 'Date', 'value': 'Weight (kg)', 'variable': 'Metric'},
                title='Weight Trend with 7-Day Moving Average',
                color_discrete_map={'weight': 'blue', 'weight_ma': 'red'}
            )
            
            trend_fig.update_layout(
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                height=400
            )
            
            st.plotly_chart(trend_fig, use_container_width=True)
            
            # Calculate rate of change per week
            if len(df) > 7:
                weekly_change = calculate_weekly_change(df)
                
                if weekly_change is not None:
                    if weekly_change < 0:
                        st.success(f"You're losing an average of {abs(weekly_change):.2f} kg per week.")
                    elif weekly_change > 0:
                        st.info(f"You're gaining an average of {weekly_change:.2f} kg per week.")
                    else:
                        st.info("Your weight is staying relatively stable.")
                    
                    # Add recommendation based on goal and weekly change
                    goal = user_data.get('goal', '').lower()
                    provide_trend_recommendation(goal, weekly_change)
        else:
            st.info("Need more data points to analyze trends. Continue updating your progress regularly.")

def calculate_weekly_change(df):
    """
    Calculate average weekly weight change
    """
    try:
        # Get first and last entries
        first_entry = df.iloc[0]
        last_entry = df.iloc[-1]
        
        # Calculate total days
        days_diff = (last_entry['timestamp'] - first_entry['timestamp']).days
        
        if days_diff < 1:
            return None
        
        # Calculate weight change
        weight_diff = last_entry['weight'] - first_entry['weight']
        
        # Calculate weekly change
        weekly_change = weight_diff * 7 / days_diff
        
        return weekly_change
    except:
        return None

def provide_trend_recommendation(goal, weekly_change):
    """
    Provide recommendations based on goal and weekly weight change
    """
    if 'weight loss' in goal:
        if weekly_change < -1:
            st.warning("You're losing weight faster than the recommended 0.5-1kg per week. Consider moderating your deficit for sustainable results.")
        elif weekly_change < 0 and weekly_change >= -1:
            st.success("You're losing weight at a healthy, sustainable rate. Keep up the good work!")
        else:
            st.info("To achieve your weight loss goal, consider adjusting your calorie intake or increasing activity.")
    
    elif 'weight gain' in goal:
        if weekly_change > 1:
            st.warning("You're gaining weight faster than the recommended 0.5-1kg per week. Consider moderating your surplus for quality gains.")
        elif weekly_change > 0 and weekly_change <= 1:
            st.success("You're gaining weight at a healthy, sustainable rate. Keep up the good work!")
        else:
            st.info("To achieve your weight gain goal, consider increasing your calorie intake.")
    
    elif 'muscle gain' in goal:
        if weekly_change > 0.5:
            st.info("You're gaining weight, which could support muscle growth. Ensure you're strength training consistently for optimal results.")
        elif weekly_change < 0:
            st.warning("You're losing weight, which may make muscle gain more challenging. Consider increasing your calorie intake.")
        else:
            st.success("Your weight is relatively stable, which can work for muscle gain if you're new to training (recomposition).")
    
    elif 'maintain weight' in goal:
        if abs(weekly_change) < 0.2:
            st.success("You're successfully maintaining your weight. Great job!")
        else:
            st.info("Your weight is changing slightly. If maintenance is your goal, small adjustments to diet or activity may help.")

def display_goal_tracking(user_data):
    """
    Display goal tracking section
    """
    st.subheader("Goal Tracking")
    
    goal = user_data.get('goal', 'Not specified')
    progress_history = user_data.get('progress_history', [])
    
    st.markdown(f"**Current Goal:** {goal}")
    
    if 'weight loss' in goal.lower():
        display_weight_loss_goal(progress_history)
    elif 'weight gain' in goal.lower():
        display_weight_gain_goal(progress_history)
    elif 'muscle gain' in goal.lower():
        display_muscle_gain_goal(progress_history)
    else:
        st.info("Set a specific weight or fitness goal in your profile to track progress toward that goal.")

def display_weight_loss_goal(progress_history):
    """
    Display weight loss goal tracking
    """
    if not progress_history or len(progress_history) < 2:
        st.info("Need more data to track weight loss progress. Update your weight regularly.")
        return
    
    # Create goal setting section
    col1, col2 = st.columns(2)
    
    with col1:
        # Get starting weight
        starting_weight = progress_history[0].get('weight', 0)
        current_weight = progress_history[-1].get('weight', 0)
        
        weight_lost = starting_weight - current_weight
        
        if 'target_weight' not in st.session_state:
            st.session_state.target_weight = current_weight - 5  # Default 5kg below current
        
        target_weight = st.number_input(
            "Target Weight (kg)",
            min_value=25.0,
            max_value=starting_weight - 0.1,
            value=st.session_state.target_weight
        )
        st.session_state.target_weight = target_weight
    
    with col2:
        # Calculate progress percentage
        total_to_lose = starting_weight - target_weight
        if total_to_lose > 0:
            progress_pct = min(100, (weight_lost / total_to_lose) * 100)
        else:
            progress_pct = 0
        
        st.metric("Weight Lost", f"{weight_lost:.1f} kg")
        st.progress(progress_pct / 100)
        st.markdown(f"**{progress_pct:.1f}% of goal achieved**")
    
    # Calculate estimated completion
    if len(progress_history) > 2 and weight_lost > 0:
        # Create a dataframe of progress history
        df = pd.DataFrame(progress_history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Calculate weekly rate of loss
        weekly_change = calculate_weekly_change(df)
        
        if weekly_change and weekly_change < 0:
            # Calculate remaining weight to lose
            remaining = current_weight - target_weight
            
            # Estimate weeks remaining
            weeks_remaining = remaining / abs(weekly_change)
            
            # Calculate target date
            target_date = datetime.now() + timedelta(weeks=weeks_remaining)
            
            st.info(f"At your current rate of {abs(weekly_change):.2f} kg/week, you will reach your target weight of {target_weight} kg by approximately {target_date.strftime('%B %d, %Y')}.")
        else:
            st.warning("Your weight isn't currently decreasing. Adjust your calorie intake or activity level to create a deficit.")

def display_weight_gain_goal(progress_history):
    """
    Display weight gain goal tracking
    """
    if not progress_history or len(progress_history) < 2:
        st.info("Need more data to track weight gain progress. Update your weight regularly.")
        return
    
    # Create goal setting section
    col1, col2 = st.columns(2)
    
    with col1:
        # Get starting weight
        starting_weight = progress_history[0].get('weight', 0)
        current_weight = progress_history[-1].get('weight', 0)
        
        weight_gained = current_weight - starting_weight
        
        if 'target_weight_gain' not in st.session_state:
            st.session_state.target_weight_gain = current_weight + 5  # Default 5kg above current
        
        target_weight = st.number_input(
            "Target Weight (kg)",
            min_value=starting_weight + 0.1,
            max_value=250.0,
            value=st.session_state.target_weight_gain
        )
        st.session_state.target_weight_gain = target_weight
    
    with col2:
        # Calculate progress percentage
        total_to_gain = target_weight - starting_weight
        if total_to_gain > 0:
            progress_pct = min(100, (weight_gained / total_to_gain) * 100)
        else:
            progress_pct = 0
        
        st.metric("Weight Gained", f"{weight_gained:.1f} kg")
        st.progress(progress_pct / 100)
        st.markdown(f"**{progress_pct:.1f}% of goal achieved**")
    
    # Calculate estimated completion
    if len(progress_history) > 2 and weight_gained > 0:
        # Create a dataframe of progress history
        df = pd.DataFrame(progress_history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Calculate weekly rate of gain
        weekly_change = calculate_weekly_change(df)
        
        if weekly_change and weekly_change > 0:
            # Calculate remaining weight to gain
            remaining = target_weight - current_weight
            
            # Estimate weeks remaining
            weeks_remaining = remaining / weekly_change
            
            # Calculate target date
            target_date = datetime.now() + timedelta(weeks=weeks_remaining)
            
            st.info(f"At your current rate of {weekly_change:.2f} kg/week, you will reach your target weight of {target_weight} kg by approximately {target_date.strftime('%B %d, %Y')}.")
        else:
            st.warning("Your weight isn't currently increasing. Consider increasing your calorie intake to create a surplus.")

def display_muscle_gain_goal(progress_history):
    """
    Display muscle gain goal information
    """
    st.markdown("""
    **Muscle Gain Tracking Tips:**
    
    While weight is one metric, for muscle gain consider tracking:
    
    1. **Strength Progress** - Track key lifts (e.g., squat, bench press)
    2. **Body Measurements** - Chest, arms, thighs, etc.
    3. **Body Composition** - If possible, monitor body fat percentage
    4. **Progress Photos** - Visual changes are often more telling than weight
    
    For optimal muscle gain:
    - Aim for 0.25-0.5kg/week weight increase (anything faster is likely more fat)
    - Ensure adequate protein (1.6-2.2g per kg of bodyweight)
    - Focus on progressive overload in your workouts
    - Prioritize recovery and sleep
    """)
    
    # Show weight chart as supplementary data
    if progress_history:
        weight_fig = create_weight_progress_chart(progress_history)
        st.plotly_chart(weight_fig, use_container_width=True, key="weight_chart_muscle_goal")

def display_full_history(user_data):
    """
    Display full progress history
    """
    st.subheader("Full Progress History")
    
    progress_history = user_data.get('progress_history', [])
    
    if not progress_history:
        st.info("No progress history available yet.")
        return
    
    # Convert to DataFrame for display
    df = pd.DataFrame(progress_history)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp', ascending=False)
    
    # Format for display
    display_df = df.copy()
    display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
    display_df = display_df.rename(columns={
        'timestamp': 'Date',
        'weight': 'Weight (kg)',
        'bmi': 'BMI'
    })
    
    # Show in a data table
    st.dataframe(display_df, use_container_width=True)
    
    # Option to download history
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Progress History",
        data=csv,
        file_name="progress_history.csv",
        mime="text/csv"
    )


if __name__ == "__main__":
    main()
