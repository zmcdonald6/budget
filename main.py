# Author: Zedaine McDonald

import streamlit as st
import pandas as pd
from Analysis import (
    parse_budget,
    parse_expense,
    category_summary,
    subcategory_summary,
    monthly_summary,
    vendor_summary,
)
from upload import upload_files
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit_authenticator

# Define users and credentials
names = ["Zedaine McDonald", "Finance Manager"]
usernames = ["zedaine", "manager"]
passwords = ["budget123", "manager456"]

# Hashed passwords (safe for production use)
hashed_pw = stauth.Hasher(passwords).generate()

# Create authenticator instance
authenticator = stauth.Authenticate(
    names, usernames, hashed_pw,
    "budget_app", "auth_cookie_secret", cookie_expiry_days=1
)

# Login UI
name, auth_status, username = authenticator.login("Login", "sidebar")

if auth_status is False:
    st.error("❌ Incorrect username or password.")
elif auth_status is None:
    st.warning("Please enter your credentials.")
elif auth_status:
    # Success — let the app continue
    st.success(f"✅ Welcome, {name}!")
if auth_status:
    st.set_page_config(layout="wide")
    st.title("📊 MSGIT Budget Reporter")
    
    
    def clean_columns(df):
        df.columns = df.columns.str.replace("_", " ")
        return df
    
    
    budget_file, expense_file = upload_files()
    
    if budget_file and expense_file:
        budget_df = parse_budget(budget_file)
        expense_df = parse_expense(expense_file)
    
        # MONTHLY SUMMARY
        with st.expander("📅 Monthly Summary"):
            monthly_df = monthly_summary(expense_df)
            monthly_df.rename(columns=lambda x: x.replace("_", " "), inplace=True)
            st.dataframe(monthly_df)
    
            st.markdown("#### Spending by Month")
            fig_month, ax_month = plt.subplots()
            sns.barplot(data=monthly_df, x="Month", y="Total Spent", ax=ax_month)
            ax_month.set_title("Monthly Spending")
            st.pyplot(fig_month)
    
        # CATEGORY BREAKDOWN
        with st.expander("📁 Category Breakdown"):
            category_df = category_summary(expense_df, budget_df)
            category_df.rename(columns=lambda x: x.replace("_", " "), inplace=True)
            st.dataframe(category_df)
    
            fig_cat, ax_cat = plt.subplots()
            category_df.set_index("Category")[["Total Spent", "Budgeted Amount"]].plot(kind="bar", ax=ax_cat)
            ax_cat.set_title("Actual vs Budget by Category")
            ax_cat.set_ylabel("Amount")
            st.pyplot(fig_cat)
    
       
        # SUBCATEGORY BREAKDOWN
        with st.expander("📂 Subcategory Breakdown"):
            if expense_df is not None and budget_df is not None:
                all_categories = sorted(budget_df["Category"].dropna().unique())
        
                if "selected_categories" not in st.session_state:
                    st.session_state.selected_categories = set(all_categories)
        
                with st.expander("🗂️ Select Categories to Display"):
                    # Select All Toggle
                    def toggle_all_categories():
                        if st.session_state.select_all:
                            st.session_state.selected_categories = set(all_categories)
                        else:
                            st.session_state.selected_categories = set()
        
                    st.checkbox("Select All", key="select_all", on_change=toggle_all_categories)
        
                    # Category checkboxes
                    updated_selection = set()
                    for cat in all_categories:
                        key = f"cat_{cat}"
                        checked = st.checkbox(cat, key=key, value=cat in st.session_state.selected_categories)
                        if checked:
                            updated_selection.add(cat)
        
                    st.session_state.selected_categories = updated_selection
        
                # Filter dataframes
                filtered_exp = expense_df[expense_df["Category"].isin(st.session_state.selected_categories)]
                filtered_bud = budget_df[budget_df["Category"].isin(st.session_state.selected_categories)]
        
                # Group and merge
                subcat_exp = filtered_exp.groupby(["Category", "Sub-Category"])["Amount"].sum().reset_index()
                subcat_exp.rename(columns={"Amount": "Actual_Spend"}, inplace=True)
        
                subcat_bud = filtered_bud.groupby(["Category", "Subcategory"])["Total"].sum().reset_index()
                subcat_bud.rename(columns={"Total": "Budget_Amount"}, inplace=True)
        
                merged_sub = pd.merge(
                    subcat_bud,
                    subcat_exp,
                    left_on=["Category", "Subcategory"],
                    right_on=["Category", "Sub-Category"],
                    how="left"
                ).fillna(0)
        
                merged_sub["Actual_Spend"] = merged_sub["Actual_Spend"].astype(float)
                merged_sub["Budget_Amount"] = merged_sub["Budget_Amount"].astype(float)
                merged_sub["Variance"] = merged_sub["Budget_Amount"] - merged_sub["Actual_Spend"]
        
                reordered = merged_sub[["Category", "Subcategory", "Budget_Amount", "Actual_Spend", "Variance"]]
        
                st.dataframe(clean_columns(reordered))
        
                st.markdown("#### Subcategory Budget Comparison Chart")
                if not reordered.empty:
                    fig_subcat, ax_subcat = plt.subplots(figsize=(10, 6))
                    cleaned = clean_columns(reordered.copy())
                    cleaned.set_index("Subcategory")[["Budget Amount", "Actual Spend"]].plot(kind="bar", ax=ax_subcat)
                    ax_subcat.set_title("Subcategory Budget vs Actual")
                    ax_subcat.set_ylabel("Amount")
                    st.pyplot(fig_subcat)
                else:
                    st.info("No data to display. Please select one or more categories.")
    
    
        
        # VENDOR SUMMARY
        with st.expander("💼 Vendor Summary"):
            vendors = vendor_summary(expense_df)
            search = st.text_input("Search for a vendor")
            if search:
                vendors = vendors[vendors["Vendor"].str.contains(search, case=False)]
    
            vendors.rename(columns=lambda x: x.replace("_", " "), inplace=True)
            st.dataframe(vendors)
    
            st.markdown("#### Top Vendors by Spend")
            fig_vendor, ax_vendor = plt.subplots()
            sns.barplot(data=vendors, x="Total Spent", y="Vendor", ax=ax_vendor)
            ax_vendor.set_title("Top Vendors by Spend")
            st.pyplot(fig_vendor)
    
        # VARIANCE HEATMAP
        with st.expander("📊 Variance Heatmap"):
            variance_df = category_summary(expense_df, budget_df)
            variance_df.rename(columns=lambda x: x.replace("_", " "), inplace=True)
            pivot = variance_df.pivot_table(index="Category", values="Variance")
            fig_heat, ax_heat = plt.subplots()
            sns.heatmap(pivot, cmap="coolwarm", annot=True, fmt=".0f", ax=ax_heat)
            ax_heat.set_title("Budget Variance Heatmap")
            st.pyplot(fig_heat)

