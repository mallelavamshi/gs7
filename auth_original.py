import streamlit as st

import sqlite3

import random

import time

import smtplib

import os

from email.message import EmailMessage

from database import create_user, verify_user, init_db





# Initialize database

init_db()



# Session state keys

SESSION_USER_KEY = "authenticated_user"

VERIFICATION_EXPIRY = 60  # 30 minutes (previously 10 minutes)



def generate_verification_code() -> str:

    return str(random.randint(100000, 999999))



def send_verification_email(email: str, code: str):

    """Send verification email using SMTP"""

    try:

        msg = EmailMessage()

        msg['Subject'] = "Your Verification Code"

        msg['From'] = os.getenv("SMTP_USER", "hello@cognovaai.com")  # Fallback to default

        msg['To'] = email

        msg.set_content(f"Your verification code is: {code}")



        with smtplib.SMTP_SSL(os.getenv("SMTP_SERVER", "smtp.hostinger.com"),

                              int(os.getenv("SMTP_PORT", 465))) as server:

            server.login(os.getenv("SMTP_USER", "hello@cognovaai.com"),

                         os.getenv("SMTP_PASSWORD", "Tulips@143"))  # Use env var

            server.send_message(msg)

        

        print(f"✅ Verification email sent to {email}")



    except Exception as e:

        st.error(f"Failed to send email: {str(e)}")





def verify_code(email: str, code: str) -> bool:

    """Verify code against database"""

    conn = sqlite3.connect("estateai.db")

    try:

        c = conn.cursor()

        c.execute('''SELECT verification_code, code_created_at 

                     FROM users WHERE email = ?''', (email,))

        result = c.fetchone()

        

        if not result or time.time() - result[1] > VERIFICATION_EXPIRY:

            return False

        return code == result[0]

    finally:

        conn.close()



def registration_form():

    """Two-step registration form"""

    if 'reg_email' not in st.session_state:

        with st.form("Register Step 1"):

            email = st.text_input("Email")

            username = st.text_input("Username")

            password = st.text_input("Password", type="password")

            

            if st.form_submit_button("Continue"):

                code = generate_verification_code()

                if create_user(username, email, password, code):

                    send_verification_email(email, code)

                    st.session_state.reg_email = email

                    st.session_state.code_time = time.time()

                    st.rerun()

                else:

                    st.error("Username/Email already exists")

    else:

        email = st.session_state.reg_email

        elapsed = time.time() - st.session_state.code_time

        remaining = max(0, VERIFICATION_EXPIRY - int(elapsed))

        

        with st.form("Register Step 2"):

            code = st.text_input("6-digit Code", max_chars=6)

            

            if st.form_submit_button("Verify"):

                if verify_code(email, code):

                    conn = sqlite3.connect("estateai.db")

                    conn.execute("UPDATE users SET verified=1 WHERE email=?", (email,))

                    conn.commit()

                    conn.close()

                    st.success("Verification successful! Please login")

                    del st.session_state.reg_email

                    st.rerun()

                else:

                    st.error("Invalid code or expired")

        

        # ✅ Move "Resend Code" button OUTSIDE the form

        if st.button("Resend Code", disabled=remaining > 0):

            new_code = generate_verification_code()

            send_verification_email(email, new_code)

            conn = sqlite3.connect("estateai.db")

            conn.execute("UPDATE users SET verification_code=?, code_created_at=? WHERE email=?",

                        (new_code, time.time(), email))

            conn.commit()

            conn.close()

            st.session_state.code_time = time.time()

            st.rerun()

        

        if remaining > 0:

            st.caption(f"Resend available in {remaining//60}:{remaining%60:02}")





def login_form():
    """User login form with modern design"""
    with st.form("Login"):
        st.markdown("""
            <style>
                /* Your existing styles... */
            </style>
        """, unsafe_allow_html=True)

        st.markdown("<h2 style='text-align: center; margin-bottom: 2rem; color: #1f2937;'>Welcome Back 👋</h2>", 
                    unsafe_allow_html=True)
        
        username = st.text_input("Username", key="username")
        password = st.text_input("Password", type="password", key="password")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.checkbox("Remember me")
        with col2:
            st.markdown("<div style='text-align: right; margin-top: 8px;'>"
                        "<a href='#' style='color: #6366f1; text-decoration: none; font-size: 14px;'>"
                        "Forgot password?</a></div>", unsafe_allow_html=True)

        if st.form_submit_button("Sign In"):
            if verify_user(username, password):
                try:
                    conn = sqlite3.connect(DATABASE_NAME)
                    cursor = conn.cursor()
                    cursor.execute("SELECT verified FROM users WHERE username=?", (username,))
                    result = cursor.fetchone()
                    
                    if result and result[0]:
                        st.session_state[SESSION_USER_KEY] = username
                        st.rerun()
                    else:
                        st.error("Email not verified")
                except sqlite3.Error as e:
                    st.error(f"Database error: {str(e)}")
                finally:
                    if 'conn' in locals():
                        conn.close()
            else:
                st.error("Invalid credentials")



def authentication_page():

    """Authentication flow controller"""

    st.markdown("""

        <style>

            /* Center align the tabs */

            div[data-testid="stTabs"] {

                display: flex;

                flex-direction: column;

                align-items: center;

            }

            

            /* Style for tab buttons */

            button[data-baseweb="tab"] {

                padding: 12px 24px;

                margin: 0 8px;

                border-radius: 8px !important;

                transition: all 0.3s ease;

            }

            

            /* Active tab styling */

            button[data-baseweb="tab"][aria-selected="true"] {

                background: #6366f1 !important;

                color: white !important;

            }

            

            /* Form container styling */

            .main .block-container {

                max-width: 800px;

                padding: 2rem;

            }

            

            /* Center the form content */

            div[data-testid="stForm"] {

                margin: 0 auto;

                max-width: 500px;

            }

            

            /* Title styling */

            h1 {

                text-align: center !important;

                margin-bottom: 2rem !important;

            }

        </style>

    """, unsafe_allow_html=True)



    st.markdown("<h1>🔑 Authentication</h1>", unsafe_allow_html=True)

    

    login_tab, reg_tab = st.tabs(["Login", "Register"])

    with login_tab:

        login_form()

    with reg_tab:

        registration_form()



def logout():

    st.session_state.pop(SESSION_USER_KEY, None)

    st.success("Logged out successfully!")



def authenticated_layout(main_app_function):

    """Authentication wrapper"""

    if SESSION_USER_KEY in st.session_state:

        st.sidebar.button("Logout", on_click=logout, key="sidebar_logout")

        main_app_function()

    else:

        authentication_page()
