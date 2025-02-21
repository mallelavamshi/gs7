import streamlit as st
import sqlite3
import random
import time
import smtplib
import os
import logging
import re
from email.message import EmailMessage
from database import create_user, verify_user, init_db, DATABASE_NAME

def login_page():
    st.markdown("""
        <style>
            /* Reset all default margins and paddings */
            .stApp {
                background-color: #FAFBFF !important;
                padding: 0 !important;
                margin: 0 !important;
                margin-top: -2rem !important;
            }
            
            /* Remove header padding and margin */
            header[data-testid="stHeader"] {
                display: none;
            }
            
            /* Remove main container padding */
            .main .block-container {
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                padding-left: 0 !important;
                padding-right: 0 !important;
                margin: 0 !important;
                max-width: 100% !important;
            }
            
            section[data-testid="stSidebar"] {
                display: none;
            }

            /* Main container styling */
            .stApp {
                background-color: #FAFBFF;
                margin-top: -6rem !important;
            }
            
            /* Logo and title container */
            .logo-container {
                padding-top: 0.8rem;
                text-align: center;
            }
            
            .logo-container img {
                width: 40px;
                margin-right: 10px;
                vertical-align: middle;
            }
            
            .logo-container h1 {
                color: #1E2E4A;
                font-size: 26px;
                font-weight: 600;
                margin: -10px 0;
                display: inline-block;
                vertical-align: middle;
            }
            
            .logo-container p {
                color: #64748B;
                font-size: 14px;
                margin-top: 0px;
                margin-bottom: -2rem;
                line-height: 1;
            }
            
            /* Tab styling */
            .stTabs {
                margin-top: -2rem;
            }
            
            /* Input fields */
            .stTextInput input {
                background-color: white !important;
                border: 1px solid #E5E9F2;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                width: 100%;
                margin-bottom: 0.8rem;
                transition: all 0.2s ease;
            }
            
            .stTextInput input:focus {
                border-color: #4F46E5 !important;
                outline: none !important;
                box-shadow: none !important;
            }
            
            /* Remove red border on invalid inputs */
            .stTextInput input:invalid {
                border-color: #E5E9F2 !important;
                box-shadow: none !important;
            }
            
            /* Remove red border on required inputs */
            .stTextInput input[aria-invalid="true"] {
                border-color: #E5E9F2 !important;
                box-shadow: none !important;
            }
            
            /* Button styling */
            .stButton button {
                width: 100%;
                padding: 12px 20px;
                border-radius: 8px;
                background: #1E2E4A;
                color: white;
                font-weight: 500;
                border: none;
                cursor: pointer;
                transition: all 0.2s ease;
                margin-top: 0.5rem;
            }
            
            .stButton button:hover {
                background: #2A3F61;
            }
            
            /* Links */
            a {
                color: #4F46E5;
                text-decoration: none;
                font-weight: 500;
                font-size: 0.9rem;
            }
            
            a:hover {
                color: #4338CA;
            }
            
            /* Error messages */
            .stAlert {
                padding: 0.8rem;
                margin: 0.8rem 0;
                border-radius: 6px;
                border-left: 3px solid;
            }
            
            .stAlert[data-baseweb="notification"] {
                background-color: #FEF2F2;
                border-color: #DC2626;
            }
            
            /* Remove backgrounds and shadows */
            div[data-testid="stVerticalBlock"],
            div[class*="stTab"],
            div[data-testid="stFormSubmitButton"] > button {
                background: transparent !important;
                box-shadow: none !important;
            }
            
            /* Form container */
            .form-container {
                max-width: 360px;
                margin: 0 auto;
                padding: 0 1rem;
            }
            
            /* Checkbox styling */
            .stCheckbox {
                color: #64748B;
                font-size: 0.9rem;
            }
            
            /* Utility classes */
            .text-center { text-align: center; }
            .mt-2 { margin-top: 0.5rem; }
            .mb-4 { margin-bottom: 1rem; }
        </style>
    """, unsafe_allow_html=True)

    # Logo and Title
    st.markdown("""
        <div class="logo-container">
            <div>
                <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgZmlsbD0ibm9uZSI+PHBhdGggZD0iTTkuNSAxOWE4LjUgOC41IDAgMSAxIDAtMTcgOC41IDguNSAwIDAgMSAwIDE3Wm0wLTEuNWE3IDcgMCAxIDAgMC0xNCA3IDcgMCAwIDAgMCAxNFoiIGZpbGw9IiMxRTJFNEEiLz48cGF0aCBkPSJtMjEuMyAyMS41LTUuNi01LjYgMS4xLTEuMSA1LjYgNS42LTEuMSAxLjFaIiBmaWxsPSIjMUUyRTRBIi8+PC9zdmc+" alt="Search Icon"/>
                <h1>EstateGenius AI</h1>
            </div>
            <p>Intelligent Lots Analysis Platform</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Center column for form
    col1, col2, col3 = st.columns([1, 1.1, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["Sign In", "Create Account"])
        
        with tab1:
            with st.form("login_form", clear_on_submit=True):
                st.markdown('<div class="form-container">', unsafe_allow_html=True)
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                cols = st.columns([3, 2])
                with cols[0]:
                    st.checkbox("Remember me", key="remember")
                with cols[1]:
                    st.markdown('<div style="text-align: right;"><a href="#">Forgot password?</a></div>', 
                              unsafe_allow_html=True)
                
                submit = st.form_submit_button("Sign In")
                
                if submit:
                    if not username or not password:
                        st.error("Please fill in all fields")
                    else:
                        with st.spinner("Signing in..."):
                            if verify_user(username, password):
                                st.session_state.authenticated_user = username
                                st.success("Login successful!")
                                st.rerun()
                            else:
                                st.error("Invalid username or password")
                st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            with st.form("register_form", clear_on_submit=True):
                st.markdown('<div class="form-container">', unsafe_allow_html=True)
                new_username = st.text_input("Username", placeholder="Choose a username", key="reg_username")
                email = st.text_input("Email", placeholder="Enter your email", key="reg_email")
                new_password = st.text_input("Password", type="password", placeholder="Choose a password", key="reg_password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                
                st.markdown("""
                    <div style="font-size: 12px; color: #64748B; padding: 12px; margin: 8px 0; border-radius: 6px;">
                        <strong>Password requirements:</strong>
                        <ul style="margin: 4px 0 0 16px; padding: 0;">
                            <li>Minimum 8 characters</li>
                            <li>One uppercase letter</li>
                            <li>One number</li>
                            <li>One special character (!@#$%^&*)</li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
                
                register_button = st.form_submit_button("Create Account")
                
                if register_button:
                    if not all([new_username, email, new_password, confirm_password]):
                        st.error("Please fill in all fields")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 8:
                        st.error("Password must be at least 8 characters long")
                    elif not re.search(r"[A-Z]", new_password):
                        st.error("Password must contain at least one uppercase letter")
                    elif not re.search(r"\d", new_password):
                        st.error("Password must contain at least one number")
                    elif not re.search(r"[!@#$%^&*]", new_password):
                        st.error("Password must contain at least one special character")
                    elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                        st.error("Please enter a valid email address")
                    else:
                        with st.spinner("Creating your account..."):
                            verification_code = str(random.randint(100000, 999999))
                            if create_user(new_username, email, new_password, verification_code):
                                send_verification_email(email, verification_code)
                                st.success("Account created! Please check your email for verification.")
                            else:
                                st.error("Username or email already exists")
                st.markdown('</div>', unsafe_allow_html=True)

def authenticated_layout(main_app_function):
   """Authentication wrapper"""
   if "authenticated_user" in st.session_state:
       main_app_function()
   else:
       login_page()