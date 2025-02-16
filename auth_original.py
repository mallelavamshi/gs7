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
    # Custom CSS with modern, elegant colors and refined positioning
    st.markdown("""
        <style>
            /* Main container styling */
            .stApp {
                background-color: #FAFBFF;  /* Very light blue-tinted background */
            }
            
            /* Adjust vertical positioning */
            section.main > div:first-child {
                padding-top: 0 !important;
            }
            
            /* Block container adjustment */
            .block-container {
                padding-top: 2rem !important;
                max-width: 100%;
            }
            
            /* Card container - reduced width */
            .auth-container {
                max-width: 400px;  /* Reduced from 460px */
                margin: 0 auto;
                padding: 2rem;
                background: white;
                border-radius: 16px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
                border: 1px solid rgba(0, 0, 0, 0.05);
            }
            
            /* Input fields */
            .stTextInput input {
                background-color: #F8FAFC;
                border: 1px solid #E5E9F2;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 15px;
                width: 100%;
                margin-bottom: 0.8rem;
                transition: all 0.2s ease;
            }
            
            .stTextInput input:focus {
                border-color: #4F46E5;
                box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
                background-color: white;
            }
            
            /* Button styling */
            .stButton button {
                width: 100%;
                padding: 12px 20px;
                border-radius: 10px;
                background: #1E2E4A;  /* Elegant navy blue */
                color: white;
                font-weight: 500;
                border: none;
                cursor: pointer;
                transition: all 0.2s ease;
                margin-top: 0.5rem;
            }
            
            .stButton button:hover {
                background: #2A3F61;
                box-shadow: 0 4px 12px rgba(30, 46, 74, 0.15);
            }
            
            /* App title styling */
            .app-header {
                text-align: center;
                margin-bottom: 1.5rem;
                padding-top: 1rem;
            }
            
            .app-header h1 {
                color: #1E2E4A;  /* Navy blue */
                font-size: 2.2rem;
                font-weight: 700;
                margin-bottom: 0.3rem;
            }
            
            .app-header p {
                color: #64748B;
                font-size: 1rem;
                font-weight: 400;
            }
            
            /* Tabs styling */
            .stTabs {
                background: transparent;
            }
            
            /* Error messages */
            .stAlert {
                background-color: #FEF2F2;
                border-left: 3px solid #DC2626;
                padding: 0.8rem;
                margin: 0.8rem 0;
                border-radius: 6px;
                color: #991B1B;
            }
            
            /* Success messages */
            .stSuccess {
                background-color: #F0FDF4;
                border-left: 3px solid #16A34A;
                padding: 0.8rem;
                margin: 0.8rem 0;
                border-radius: 6px;
                color: #166534;
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
            
            /* Checkbox styling */
            .stCheckbox {
                color: #64748B;
                font-size: 0.9rem;
            }
            
            /* Password requirements box */
            .password-requirements {
                background: #F8FAFC;
                padding: 1rem;
                border-radius: 8px;
                margin: 0.8rem 0;
                border: 1px solid #E5E9F2;
            }
            
            .password-requirements p {
                color: #64748B;
                font-size: 0.9rem;
                margin-bottom: 0.5rem;
            }
            
            .password-requirements ul {
                color: #64748B;
                font-size: 0.9rem;
                margin: 0;
                padding-left: 1.2rem;
            }
            
            /* Tab content wrapper */
            .stTabs > div > div:nth-child(2) {
                padding: 0;
            }
        </style>
    """, unsafe_allow_html=True)

    # App header with logo and title
    st.markdown("""
        <div class="app-header">
            <h1>🔍 EstateGenius AI</h1>
            <p>Intelligent Lots Analysis Platform</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Adjust vertical spacing
    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
    
    # Center the content
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        # Login/Register tabs
        tab1, tab2 = st.tabs(["Sign In", "Create Account"])
        
        with tab1:
            st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            
            # Login form
            with st.form("login_form", clear_on_submit=True):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                # Remember me and Forgot password in two columns
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
            st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            
            # Registration form
            with st.form("register_form", clear_on_submit=True):
                new_username = st.text_input("Username", placeholder="Choose a username", key="reg_username")
                email = st.text_input("Email", placeholder="Enter your email", key="reg_email")
                new_password = st.text_input("Password", type="password", placeholder="Choose a password", key="reg_password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                
                # Password requirements info
                st.markdown("""
                    <div class="password-requirements">
                        <p><strong>Password requirements:</strong></p>
                        <ul>
                            <li>At least 8 characters</li>
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