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

    with st.expander("📅 Monthly Summary"):
        monthly_df = monthly_summary(expense_df)
        st.dataframe(clean_columns(monthly_df))

        fig_month, ax_month = plt.subplots()
        sns.barplot(data=monthly_df, x="Month", y="Total_Spent", ax=ax_month)
        ax_month.set_title("Monthly Spending")
        st.pyplot(fig_month)

    with st.expander("📁 Category Breakdown"):
        category_df = category_summary(expense_df, budget_df)
        st.dataframe(clean_columns(category_df))

        fig_cat, ax_cat = plt.subplots()
        category_df.rename(columns=lambda x: x.replace("_", " "), inplace=True)
        category_df[["Category", "Actual Spend"]] = category_df[["Category", "Total Spent"]]
        category_df[["Budget Amount"]] = category_df[["Budgeted Amount"]]
        category_df.set_index("Category")[["Actual Spend", "Budget Amount"]].plot(kind="bar", ax=ax_cat)
        ax_cat.set_title("Actual vs Budget by Category")
        st.pyplot(fig_cat)

    with st.expander("📂 Subcategory Breakdown"):
        if category_df is not None and expense_df is not None:
            selected = st.selectbox("Select a Category", category_df["Category"].unique())
            sub_exp = expense_df[expense_df["Category"] == selected]
            sub_bud = budget_df[budget_df["Category"] == selected]

            subcat_exp = sub_exp.groupby("Sub-Category")["Amount"].sum().reset_index()
            subcat_exp.rename(columns={"Amount": "Actual_Spend"}, inplace=True)

            subcat_bud = sub_bud.groupby("Subcategory")["Total"].sum().reset_index()
            subcat_bud.rename(columns={"Total": "Budget_Amount"}, inplace=True)

            merged_sub = pd.merge(
                subcat_bud,
                subcat_exp,
                left_on="Subcategory",
                right_on="Sub-Category",
                how="left"
            ).fillna(0)

            merged_sub["Label"] = merged_sub["Subcategory"]
            merged_sub["Actual_Spend"] = merged_sub["Actual_Spend"].astype(float)
            merged_sub["Budget_Amount"] = merged_sub["Budget_Amount"].astype(float)

            fig_subcat, ax_subcat = plt.subplots()
            merged_sub.set_index("Label")[["Actual_Spend", "Budget_Amount"]].plot(kind="bar", ax=ax_subcat)
            ax_subcat.set_title(f"{selected} - Actual vs Budget")
            ax_subcat.set_ylabel("Amount")
            st.pyplot(fig_subcat)

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

    with st.expander("📊 Variance Heatmap"):
        variance_df = category_summary(expense_df, budget_df)
        pivot = variance_df.pivot_table(index="Category", values="Variance")
        fig_heat, ax_heat = plt.subplots()
        sns.heatmap(pivot, cmap="coolwarm", annot=True, fmt=".0f", ax=ax_heat)
        ax_heat.set_title("Budget Variance Heatmap")
        st.pyplot(fig_heat)
