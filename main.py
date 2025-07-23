import streamlit as st
from upload import upload_files
from Analysis import parse_budget, parse_expense, summarize_monthly, category_summary

st.title("📊 Budget Reporter")

budget_file, expense_file = upload_files()

if budget_file and expense_file:
    budget_df = parse_budget(budget_file)
    expense_df = parse_expense(expense_file)

    st.subheader("📅 Monthly Overview")
    monthly_summary = summarize_monthly(budget_df, expense_df)
    st.dataframe(monthly_summary)
    st.bar_chart(monthly_summary.set_index("Month")[["Budgeted", "Spent"]])

    st.subheader("📂 Category Breakdown")
    category_df = category_summary(expense_df)
    st.dataframe(category_df)

    st.subheader("🧾 Raw Expense Data")
    st.dataframe(expense_df)

    st.subheader("🗃️ Raw Budget Data")
    st.dataframe(budget_df)
else:
    st.info("Please upload both a budget and an expense file to proceed.")
