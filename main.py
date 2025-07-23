#Author: Zedaine McDonald

import streamlit as st
import Analysis
from upload import upload_files
from Analysis import parse_budget, parse_expense, monthly_summary, category_summary, subcategory_summary, vendor_summary

print(dir(Analysis))
st.set_page_config(page_title="Budget App", layout="wide")

st.title("💼 Budget Analysis Dashboard")

budget_file, expense_file = upload_files()

if budget_file and expense_file:
    budget_df = parse_budget(budget_file)
    expense_df = parse_expense(expense_file)

    cat_summary = category_summary(expense_df, budget_df)
    subcat_summary = subcategory_summary(expense_df, budget_df)
    month_summary = monthly_summary(expense_df)
    vendor_sum = vendor_summary(expense_df)

    with st.expander("📊 Category Summary"):
        st.write("Total spent vs. budget by category")
        st.dataframe(cat_summary)

    with st.expander("🧩 Category Breakdown"):
        categories = sorted(cat_summary['Category'].unique())
        selected = st.selectbox("Select a category", categories)
        filtered = subcat_summary[subcat_summary['Category'] == selected]
        st.dataframe(filtered)

    with st.expander("📆 Monthly Summary"):
        st.write("Spending by month")
        st.dataframe(month_summary)
        st.bar_chart(month_summary.set_index("Month"))

    with st.expander("🏷️ Vendor Summary"):
        vendors = sorted(expense_df['Vendor'].dropna().unique())
        vendor_filter = st.selectbox("Filter by vendor", vendors)
        vendor_table = vendor_sum[vendor_sum['Vendor'] == vendor_filter]
        st.dataframe(vendor_table)
else:
    st.info("Please upload both a budget file and an expense file.")
