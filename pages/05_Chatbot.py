import os
from openai import OpenAI
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from utils.user_management import get_user
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

# Load API key
client = OpenAI(api_key=st.secrets["OPENAI_KEY"])

# Load data
food_data = pd.read_csv("attached_assets/cleaned_food_data_refined.csv")
exercise_data = pd.read_csv("attached_assets/cleaned_exercise_data_refined.csv")

def main():
    st.title("💬 Chat with Sma Bot")
    sidebar(current_page="💬 Chatbot Assistant")

    # Get user data
    user_id = st.session_state.current_user
    user_data = get_user(user_id)

    # Get chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": f"Hi {user_data.get('name', 'there')}, how can I help you today?"}
        ]

    # Display chat history
    for msg in st.session_state.chat_history:
        st.chat_message("user" if msg["role"] == "user" else "assistant").markdown(msg["content"])

    # Check input
    user_input = st.chat_input("Ask me something like 'give me a meal plan' or 'show a workout'")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # Get AI response
        response = get_chatbot_response(user_input, user_data, food_data, exercise_data)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.chat_message("assistant").markdown(response)


# Response function to get chatbot response
def get_chatbot_response(user_input, user_data, food_data, exercise_data):
    try:
        # Add sample meal and exercise to the context
        sample_meal = food_data.sample(1).iloc[0]
        sample_ex = exercise_data.sample(1).iloc[0]

        meal_info = f"""
        Here's a sample meal:
        - {sample_meal['Food Name']}: {sample_meal['Calories']} kcal, {sample_meal['Protein']}g protein, {sample_meal['Carbs']}g carbs, {sample_meal['Total Fat']}g fat
        """

        exercise_info = f"""
        Here's a sample exercise:
        - {sample_ex['Exercise']}: Equipment - {sample_ex['Equipment Type']}
        Preparation: {sample_ex['Preparation']}
        Execution: {sample_ex['Execution']}
        """

        context = f"""
        The user is a {user_data.get('age', 'N/A')}-year-old {user_data.get('gender', 'N/A')} 
        with the goal of {user_data.get('goal', 'N/A')}, following a {user_data.get('diet', 'N/A')} diet.
        Their current weight is {user_data.get('weight', 'N/A')}kg, height {user_data.get('height', 'N/A')}cm, and BMI is {user_data.get('bmi', 'N/A')}.
        Respond as a supportive AI coach called Sma Bot.
        {meal_info}
        {exercise_info}
        """

        messages = [
            {"role": "system", "content": context},
            {"role": "user", "content": user_input},
        ]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return response.choices[0].message.content
    
    except Exception as e:
        return f"⚠️ An error occurred: {e}"
    
if __name__ == "__main__":
    main()
