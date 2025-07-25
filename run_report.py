# Author: Zedaine McDonald

import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from Analysis import category_summary, subcategory_summary, monthly_summary, vendor_summary

def run_report(expense_df, budget_df):
    st.markdown("## 📈 Full Budget Report")

    # Monthly Summary
    with st.expander("📅 Monthly Summary"):
        monthly_df = monthly_summary(expense_df)
        monthly_df.rename(columns=lambda x: x.replace("_", " "), inplace=True)
        st.dataframe(monthly_df)

        fig_month, ax_month = plt.subplots()
        sns.barplot(data=monthly_df, x="Month", y="Total Spent", ax=ax_month)
        ax_month.set_title("Monthly Spending")
        st.pyplot(fig_month)

    # Category Breakdown
    with st.expander("📁 Category Breakdown"):
        category_df = category_summary(expense_df, budget_df)
        category_df.rename(columns=lambda x: x.replace("_", " "), inplace=True)
        st.dataframe(category_df)

        fig_cat, ax_cat = plt.subplots()
        category_df.set_index("Category")[["Total Spent", "Budgeted Amount"]].plot(kind="bar", ax=ax_cat)
        ax_cat.set_title("Actual vs Budget by Category")
        st.pyplot(fig_cat)

    # Subcategory Breakdown
    with st.expander("📂 Subcategory Breakdown"):
        all_categories = sorted(budget_df["Category"].dropna().unique())
        selected_categories = st.multiselect("Select Categories", all_categories, default=all_categories)

        filtered_exp = expense_df[expense_df["Category"].isin(selected_categories)]
        filtered_bud = budget_df[budget_df["Category"].isin(selected_categories)]

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
        st.dataframe(reordered.rename(columns=lambda x: x.replace("_", " ")))

        fig_subcat, ax_subcat = plt.subplots(figsize=(10, 6))
        cleaned = reordered.rename(columns=lambda x: x.replace("_", " "))
        cleaned.set_index("Subcategory")[["Budget Amount", "Actual Spend"]].plot(kind="bar", ax=ax_subcat)
        ax_subcat.set_title("Subcategory Budget vs Actual")
        st.pyplot(fig_subcat)

    # Vendor Summary
    with st.expander("💼 Vendor Summary"):
        vendors = vendor_summary(expense_df)
        search = st.text_input("Search for a vendor")
        if search:
            vendors = vendors[vendors["Vendor"].str.contains(search, case=False)]

        vendors.rename(columns=lambda x: x.replace("_", " "), inplace=True)
        st.dataframe(vendors)

        fig_vendor, ax_vendor = plt.subplots()
        sns.barplot(data=vendors, x="Total Spent", y="Vendor", ax=ax_vendor)
        ax_vendor.set_title("Top Vendors by Spend")
        st.pyplot(fig_vendor)

    # Variance Heatmap
    with st.expander("📊 Variance Heatmap"):
        variance_df = category_summary(expense_df, budget_df)
        variance_df.rename(columns=lambda x: x.replace("_", " "), inplace=True)
        pivot = variance_df.pivot_table(index="Category", values="Variance")
        fig_heat, ax_heat = plt.subplots()
        sns.heatmap(pivot, cmap="coolwarm", annot=True, fmt=".0f", ax=ax_heat)
        ax_heat.set_title("Budget Variance Heatmap")
        st.pyplot(fig_heat)
