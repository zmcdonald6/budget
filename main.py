import streamlit as st
import openpyxl
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from upload import upload_files
from Analysis import (
    parse_budget,
    parse_expense,
    category_summary,
    subcategory_summary,
    monthly_summary,
    vendor_summary
)

def clean_columns(df):
    return df.rename(columns=lambda x: x.replace("_", " "))

st.set_page_config(page_title="Department Budget Reporter", layout="wide")

st.title("📊 Department Budget Reporter")
st.markdown("Upload your budget and expense Excel files below to generate reports.")

# File upload section
budget_file, expense_file = upload_files()

if budget_file and expense_file:
    budget_df = parse_budget(budget_file)
    expense_df = parse_expense(expense_file)

    st.success("Files successfully uploaded and parsed.")

    # Category Summary
    with st.expander("📊 Category Summary", expanded=False):
        cat_summary = category_summary(expense_df, budget_df)
        st.dataframe(clean_columns(cat_summary))

    # Category Breakdown
    with st.expander("🧩 Category Breakdown", expanded=False):
        subcat_summary = subcategory_summary(expense_df, budget_df)
        selected = st.selectbox("Select a category to expand", subcat_summary["Category"].unique())
        filtered = subcat_summary[subcat_summary["Category"] == selected].copy()
        if "Category" in filtered.columns:
            filtered.drop(columns="Category", inplace=True)
        st.dataframe(clean_columns(filtered))

        st.markdown("#### Subcategory Actual vs Budget Comparison")
        subcat_exp = expense_df[expense_df["Category"] == selected].groupby("Sub-Category").agg(
            Actual_Spend=("Amount", "sum")).reset_index()

        subcat_bud = budget_df[budget_df["Category"] == selected].groupby("Subcategory").agg(
            Budget_Amount=("Total", "sum")).reset_index()

        merged_sub = pd.merge(subcat_exp, subcat_bud, left_on="Sub-Category", right_on="Subcategory", how="outer").fillna(0)

        fig_subcat, ax_subcat = plt.subplots()
        merged_sub.set_index("Sub-Category")[["Actual_Spend", "Budget_Amount"]].plot(kind="bar", ax=ax_subcat)
        ax_subcat.set_title(f"{selected} - Actual vs Budget")
        st.pyplot(fig_subcat)

    # Monthly Summary
    with st.expander("📆 Monthly Summary", expanded=False):
        st.dataframe(clean_columns(monthly_summary(expense_df)))

    # Vendor Summary
    with st.expander("🏷️ Vendor Summary", expanded=False):
        vendors = vendor_summary(expense_df)
        search = st.text_input("Search for a vendor")
        if search:
            vendors = vendors[vendors["Vendor"].str.contains(search, case=False)]
        vendors.rename(columns=lambda x: x.replace("_", " "), inplace = True)
        
        st.dataframe(vendors)

        st.markdown("#### Top Vendors by Spend")
        fig_vendor, ax_vendor = plt.subplots()
        sns.barplot(data=vendors, x="Total Spent", y="Vendor", ax=ax_vendor)
        ax_vendor.set_title("Top Vendors by Spend")
        st.pyplot(fig_vendor)

    # Variance Heatmap
    with st.expander("🔥 Variance Heatmap", expanded=False):
        st.markdown("#### Budget vs Actual Variance by Category/Subcategory")

        expense_grouped = expense_df.groupby(["Category", "Sub-Category"]).agg(Total_Spent=("Amount", "sum")).reset_index()

        variance_df = pd.merge(
            budget_df,
            expense_grouped,
            left_on=["Category", "Subcategory"],
            right_on=["Category", "Sub-Category"],
            how="left"
        ).fillna(0)

        variance_df["Variance"] = variance_df["Total"] - variance_df["Total_Spent"]
        heatmap_data = variance_df.pivot_table(index="Category", columns="Subcategory", values="Variance", fill_value=0)

        fig_heatmap, ax_heatmap = plt.subplots(figsize=(10, 4))
        sns.heatmap(heatmap_data, annot=True, fmt=".0f", cmap="RdYlGn", center=0, ax=ax_heatmap)
        ax_heatmap.set_title("Variance Heatmap (Budget - Actual)")
        st.pyplot(fig_heatmap)
