import streamlit as st

def sidebar(current_page):
    st.sidebar.title("Navigation")
    
    # Check login status
    if st.session_state.get("logged_in", False):
        st.sidebar.success(f"Logged in as {st.session_state.get('username', 'Unknown')}")
        
        if st.sidebar.button("Log Out"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.switch_page("app.py")
            st.rerun()
    else:
        st.sidebar.info("Please log in or sign up to use features.")
    
    st.sidebar.subheader("Features")

    features = {
        "🏠 Home": "app.py",
        "📝 Profile": "pages/02_Profile.py",
        "🍽️ Meal Planner": "pages/03_Meal_Planner.py",
        "🏋️ Exercise Recommendations": "pages/04_Exercise_Recommendations.py",
        "💬 Chatbot Assistant": "pages/05_Chatbot.py",
        "📈 Progress Tracking": "pages/06_Progress_Tracking.py"
    }

    for feature_name, feature_page in features.items():
        # Highlight current page
        if feature_name.startswith(current_page):
            st.sidebar.button(feature_name, use_container_width=True, disabled=True)
        else:
            if st.sidebar.button(feature_name, use_container_width=True):
                if st.session_state.get("logged_in", False):
                    st.session_state["sidebar_state"] = "collapsed"
                    st.switch_page(feature_page)
                else:
                    st.error("Please log in to access this feature.")

    # Admin Dashboard if user is admin
    if st.session_state.get("is_admin", False):
        st.sidebar.subheader("Admin")
        if current_page == "🛠️ Admin Dashboard":
            st.sidebar.button("🛠️ Admin Dashboard", use_container_width=True, disabled=True)
        else:
            if st.sidebar.button("🛠️ Admin Dashboard", use_container_width=True):
                st.switch_page("pages/99_Admin_Dashboard.py")
    
    st.sidebar.markdown("---")
    st.sidebar.info(
        "Smart Meal Planning & Health Assistant\n\n"
        "An AI-powered application for personalized nutrition and exercise guidance."
    )
