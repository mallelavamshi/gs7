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
    # Custom CSS for modern styling
    st.markdown("""
        <style>
            /* Main container styling */
            .stApp {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            }
            
            /* Card container */
            .auth-container {
                max-width: 460px;
                margin: 2rem auto;
                padding: 2rem;
                background: white;
                border-radius: 20px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            }
            
            /* Input fields */
            .stTextInput input {
                border: 2px solid #e2e8f0;
                border-radius: 10px;
                padding: 12px;
                font-size: 16px;
                width: 100%;
                margin-bottom: 1rem;
                transition: all 0.3s ease;
            }
            
            .stTextInput input:focus {
                border-color: #4f46e5;
                box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
            }
            
            /* Button styling */
            .stButton button {
                width: 100%;
                padding: 12px 20px;
                border-radius: 10px;
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                color: white;
                font-weight: 600;
                border: none;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .stButton button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
            }
            
            /* Logo/branding */
            .app-logo {
                text-align: center;
                margin-bottom: 2rem;
            }
            
            .app-logo img {
                width: 80px;
                height: 80px;
            }
            
            /* Divider */
            .divider {
                display: flex;
                align-items: center;
                text-align: center;
                margin: 1.5rem 0;
            }
            
            .divider::before,
            .divider::after {
                content: "";
                flex: 1;
                border-bottom: 1px solid #e2e8f0;
            }
            
            .divider span {
                padding: 0 1rem;
                color: #64748b;
                font-size: 14px;
            }
            
            /* Error messages */
            .error-msg {
                background: #fee2e2;
                border-left: 4px solid #ef4444;
                padding: 1rem;
                margin: 1rem 0;
                border-radius: 4px;
                color: #b91c1c;
            }
            
            /* Success messages */
            .success-msg {
                background: #dcfce7;
                border-left: 4px solid #22c55e;
                padding: 1rem;
                margin: 1rem 0;
                border-radius: 4px;
                color: #15803d;
            }
        </style>
    """, unsafe_allow_html=True)

    # Center the content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # App logo and title
        st.markdown("""
            <div class="app-logo">
                <h1>🔍 EstateGenius AI</h1>
                <p style="color: #64748b; text-align: center;">Intelligent Real Estate Analysis</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Login/Register tabs
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
        
        with tab1:
            st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            
            # Login form
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                # Remember me and Forgot password
                col1, col2 = st.columns(2)
                with col1:
                    remember = st.checkbox("Remember me")
                with col2:
                    st.markdown('<div style="text-align: right;"><a href="#" style="color: #4f46e5; text-decoration: none; font-size: 14px;">Forgot password?</a></div>', unsafe_allow_html=True)
                
                submit_button = st.form_submit_button("Sign In")
                
                if submit_button:
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
            with st.form("register_form"):
                new_username = st.text_input("Username", placeholder="Choose a username", key="reg_username")
                email = st.text_input("Email", placeholder="Enter your email", key="reg_email")
                new_password = st.text_input("Password", type="password", placeholder="Choose a password", key="reg_password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                
                # Password requirements info
                st.markdown("""
                    <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
                        <p style="color: #64748b; font-size: 14px; margin-bottom: 0.5rem;">Password requirements:</p>
                        <ul style="color: #64748b; font-size: 14px; margin: 0; padding-left: 1.5rem;">
                            <li>At least 8 characters long</li>
                            <li>Contains at least one number</li>
                            <li>Contains at least one special character</li>
                            <li>Contains at least one uppercase letter</li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
                
                register_button = st.form_submit_button("Create Account")
                
                if register_button:
                    # Validation
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
                                st.success("Account created successfully! Please check your email for verification.")
                            else:
                                st.error("Username or email already exists")
            
            st.markdown('</div>', unsafe_allow_html=True)

def authenticated_layout(main_app_function):
    """Authentication wrapper"""
    if "authenticated_user" in st.session_state:
        main_app_function()
    else:
        login_page()