#Author: Zedaine McDonald
#Handle the upload of files.

import streamlit as st

def upload_files():
    st.sidebar.header("Upload Files")
    budget_file = st.sidebar.file_uploader("Upload Budget File (.xlsx)", type=["xlsx"])     #Accept Budget
    expense_file = st.sidebar.file_uploader("Upload Expense File (.xlsx)", type=["xlsx"])   #Accept Expense file
    return budget_file, expense_file