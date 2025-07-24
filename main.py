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


