# Author: Zedaine McDonald

import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
from io import BytesIO
import streamlit_authenticator as stauth

from Analysis import parse_budget, parse_expense
from run_report import run_report
from s3_utils import upload_to_s3, list_files_by_type, get_file_from_s3

# Load environment variables
load_dotenv()

# Use pre-hashed passwords
credentials = {
    "usernames": {
        "john": {
            "name": "John Doe",
            "password": "$2b$12$XlGpJbWkuI5NzTo5vJq9g.GYjs1vlbq5TjRXt6tT9eLptP3piM2kS"
        },
        "zedaine": {
            "name": "Zedaine McDonald",
            "password": "$2b$12$J9aDqzgjEiPi7Ym0Me1oqOCmxvh/sYZVjES.yAnLPjflxmuWkqXcu"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    cookie_name="budget_app_login",
    key="abcdef",
    cookie_expiry_days=1
)

# This must be passed with two positional arguments
name, auth_status, username = authenticator.login("Login", "main")

# --- Handle login status ---
if auth_status is False:
    st.error("❌ Incorrect username or password.")
elif auth_status is None:
    st.warning("⏳ Please enter your login credentials.")
elif auth_status:
    st.success(f"✅ Welcome {name}!")
    authenticator.logout("Logout", "sidebar")

    st.title("📊 Budget Tracker - Believe")

    # --- MAIN MENU ---
    st.subheader("What would you like to do today?")
    col1, col2, col3 = st.columns(3)

    action = None
    if col1.button("📈 Generate Report"):
        action = "report"
    elif col2.button("📤 Upload File"):
        action = "upload"
    elif col3.button("📁 View Files"):
        action = "view"

    # --- REPORT GENERATION ---
    if action == "report":
        st.subheader("Generate Report")

        report_type = st.radio("Choose data source", ["Upload New Files", "Use Existing Files"])
        if report_type == "Upload New Files":
            budget_file = st.file_uploader("Upload Budget File (.xlsx)", type="xlsx", key="bud")
            expense_file = st.file_uploader("Upload Expense File (.xlsx)", type="xlsx", key="exp")

            if budget_file and expense_file:
                budget_df = parse_budget(budget_file)
                expense_df = parse_expense(expense_file)
                run_report(expense_df, budget_df)

        else:
            budgets = list_files_by_type("budget")
            expenses = list_files_by_type("expense")

            selected_budget = st.selectbox("Select Budget File", budgets)
            selected_expense = st.selectbox("Select Expense File", expenses)

            if selected_budget and selected_expense:
                budget_bytes = get_file_from_s3(selected_budget)
                expense_bytes = get_file_from_s3(selected_expense)

                budget_df = parse_budget(BytesIO(budget_bytes))
                expense_df = parse_expense(BytesIO(expense_bytes))
                run_report(expense_df, budget_df)

    # --- UPLOAD SCREEN ---
    elif action == "upload":
        st.subheader("Upload New File")

        uploaded_file = st.file_uploader("Choose a file to upload (.xlsx)", type="xlsx", key="upload_file")
        file_type = st.selectbox("What kind of file is this?", ["budget", "expense"])
        year = st.text_input("Enter the year (for budget files)", disabled=(file_type != "budget"))

        if uploaded_file and st.button("Upload to Cloud"):
            key = upload_to_s3(
                file=uploaded_file,
                filename=uploaded_file.name,
                user=username,
                filetype=file_type,
                year=year if file_type == "budget" else None
            )
            st.success(f"✅ File uploaded to S3 as `{key}`.")

    # --- VIEW FILES SCREEN ---
    elif action == "view":
        st.subheader("Uploaded Files Viewer")

        filetype_filter = st.selectbox("Filter by Type", ["budget", "expense"])
        year_filter = st.text_input("Filter by Year (leave blank for all)", "")
        user_filter = st.text_input("Filter by Username (leave blank for all)", "")

        all_files = list_files_by_type(filetype_filter)

        filtered_files = []
        for key in all_files:
            if year_filter and year_filter not in key:
                continue
            if user_filter and user_filter not in key:
                continue
            filtered_files.append(key)

        if filtered_files:
            st.write("Filtered Files:")
            for f in filtered_files:
                st.markdown(f"- `{f}`")
        else:
            st.warning("No files match your filter.")
