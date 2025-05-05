import streamlit as st
from utils.user_management import authenticate_user

st.set_page_config(
    page_title="Login - Smart Meal Planning",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Hide sidebar + Add scrolling emojis
st.markdown(
    """
    <style>
    /* Hide sidebar */
    [data-testid="stSidebarNav"] {display: none;}
    [data-testid="stSidebar"] {display: none;}
    .stApp {background-color: #0e1117;}

    /* Emoji bar styles */
    .emoji-bar {
        position: fixed;
        top: 0;
        width: 200px;
        height: 100vh;
        overflow: hidden;
        z-index: 999;
        font-size: 10rem;
        line-height: 11rem;
        opacity: 0.9;
    }
    .emoji-bar.left {
        left: 250px; /* move closer to login */
        text-align: center;
    }
    .emoji-bar.right {
        right: 250px; /* move closer to login */
        text-align: center;
    }
    .emoji-content {
        display: inline-block;
        animation: scrollEmojis 40s linear infinite;
    }
    @keyframes scrollEmojis {
        0% { transform: translateY(0%); }
        100% { transform: translateY(-100%); }
    }
    </style>

    <!-- Emoji Bars -->
    <div class="emoji-bar left">
    <div class="emoji-content">
        🥑🍔🍇🍣🍕🍎🥗🍩🥥
        🥑🍔🍇🍣🍕🍎🥗🍩🥥
        🥑🍔🍇🍣🍕🍎🥗🍩🥥
        🥑🍔🍇🍣🍕🍎🥗🍩🥥
        🥑🍔🍇🍣🍕🍎🥗🍩🥥
        🥑🍔🍇🍣🍕🍎🥗🍩🥥
    </div>
    </div>

    <div class="emoji-bar right">
    <div class="emoji-content">
        🍩🍎🥗🍇🍣🍔🍕🥑🥥
        🍩🍎🥗🍇🍣🍔🍕🥑🥥
        🍩🍎🥗🍇🍣🍔🍕🥑🥥
        🍩🍎🥗🍇🍣🍔🍕🥑🥥
        🍩🍎🥗🍇🍣🍔🍕🥑🥥
        🍩🍎🥗🍇🍣🍔🍕🥑🥥
    </div>
    </div>

    """,
    unsafe_allow_html=True
)

# Title
st.markdown("<h1 style='text-align: center;'>🔐 Login</h1>", unsafe_allow_html=True)
st.write("")  # Small space

# Proper centered form layout
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    with st.form("login_form", clear_on_submit=False):
        st.markdown("### Login Details")
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        col1, col2 = st.columns([2, 1])

        with col1:
            login_button = st.form_submit_button("Login")
        with col2:
            cancel_button = st.form_submit_button("Cancel")

        # Authentication logic
        if login_button:
            success, user_id, is_admin = authenticate_user(username, password)
            if success:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["current_user"] = user_id
                st.session_state["is_admin"] = is_admin
                st.success(f"Welcome, {username}!")
                if is_admin:
                    st.switch_page("pages/99_Admin_Dashboard.py")
                else:
                    st.switch_page("pages/06_Progress_Tracking.py")
            else:
                st.error("Invalid credentials. Please try again.")

        if cancel_button:
            st.switch_page("app.py")

# Dont have account? suggestion
st.markdown("</div>", unsafe_allow_html=True)  # close the login card div

# Small separator
st.write("")
st.write("")

# Centered Sign Up suggestion
st.markdown("""
<div style='text-align: center;'>
    <p style='font-size: 1.1rem;'>Don't have an account?</p>
</div>
""", unsafe_allow_html=True)

col_a, col_b, col_c = st.columns([1,2,1])

with col_b:
    if st.button("Sign Up", use_container_width=True):
        st.switch_page("pages/01_Signup.py")
