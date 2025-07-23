import streamlit as st
import pandas as pd
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

st.set_page_config(page_title="Group IT Budget Reporter", layout="wide")

st.title("📊 Department Budget Reporter")
st.markdown("Upload your budget and expense Excel files below to generate reports.")

# File upload section
budget_file, expense_file = upload_files()

if budget_file and expense_file:
    budget_df = parse_budget(budget_file)
    expense_df = parse_expense(expense_file)

    st.success("Files successfully uploaded and parsed.")

    with st.expander("📊 Category Summary", expanded=False):
        cat_summary = category_summary(expense_df, budget_df)
        st.dataframe(clean_columns(cat_summary))

    with st.expander("🧩 Category Breakdown", expanded=False):
        subcat_summary = subcategory_summary(expense_df, budget_df)
        selected = st.selectbox("Select a category to expand", subcat_summary["Category"].unique())
        filtered = subcat_summary[subcat_summary["Category"] == selected].copy()
        if "Subcategory" in filtered.columns:
            filtered.drop(columns="Subcategory", inplace=True)
        st.dataframe(clean_columns(filtered))

    with st.expander("📆 Monthly Summary", expanded=False):
        st.dataframe(clean_columns(monthly_summary(expense_df)))

    with st.expander("🏷️ Vendor Summary", expanded=False):
        vendors = vendor_summary(expense_df)
        search = st.text_input("Search for a vendor")
        if search:
            vendors = vendors[vendors["Vendor"].str.contains(search, case=False)]
        st.dataframe(clean_columns(vendors))
