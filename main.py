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

st.set_page_config(layout="wide")
st.title("📊 Department Budget Tracker")


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
            category_df = category_summary(expense_df, budget_df)
            subcategory_map = budget_df.groupby("Category")["Subcategory"].unique().to_dict()
    
            selected_subcategories = {}
    
            for category, subcategories in subcategory_map.items():
                with st.expander(f"{category}"):
                    select_all_key = f"select_all_{category}"
                    if select_all_key not in st.session_state:
                        st.session_state[select_all_key] = False
    
                    def toggle_all(cat=category, subs=subcategories):
                        for sub in subs:
                            st.session_state[f"{cat}_{sub}"] = st.session_state[select_all_key]
    
                    st.checkbox("Select All", key=select_all_key, on_change=toggle_all)
    
                    selected_subcategories[category] = []
                    for sub in subcategories:
                        checkbox_key = f"{category}_{sub}"
                        if checkbox_key not in st.session_state:
                            st.session_state[checkbox_key] = False
                        checked = st.checkbox(sub, key=checkbox_key)
                        if checked:
                            selected_subcategories[category].append(sub)
    
            # Build filter for selected subcategories
            filter_rows = []
            for cat, subs in selected_subcategories.items():
                for sub in subs:
                    filter_rows.append((cat, sub))
    
            # Prepare subcategory dataframes
            sub_exp = expense_df.copy()
            sub_bud = budget_df.copy()
    
            subcat_exp = sub_exp.groupby(["Category", "Sub-Category"])["Amount"].sum().reset_index()
            subcat_exp.rename(columns={"Amount": "Actual_Spend"}, inplace=True)
    
            subcat_bud = sub_bud.groupby(["Category", "Subcategory"])["Total"].sum().reset_index()
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
    
            if filter_rows:
                filter_df = pd.DataFrame(filter_rows, columns=["Category", "Subcategory"])
                reordered = pd.merge(reordered, filter_df, on=["Category", "Subcategory"])
    
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
                st.info("No subcategories selected.")
    
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

