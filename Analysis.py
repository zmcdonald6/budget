#Author: Zedaine McDonald

from openpyxl import load_workbook
from io import BytesIO
import pandas as pd

# Parse Budget File
def parse_budget(file):
    wb = load_workbook(filename=BytesIO(file.read()), data_only=True)   #Load excel file
    sheet = wb.active
    month_headers = [cell.value for cell in sheet[1][1:14]]  # B1 to N1, Month headers.

    data = []   #Parsed Data stored here
    current_category = None #Stores main categories(indicated by yellow fill)

    for row in sheet.iter_rows(min_row=2):  
        name_cell = row[0]
        name = name_cell.value
        if name is None:
            continue

        fill = name_cell.fill
        is_category = (
            fill and fill.start_color and fill.start_color.type == "rgb" and
            fill.start_color.rgb in ["FFFFFF00", "FFFF00", "FFFFFF99"]
        )

        if is_category:
            current_category = name
            continue

        months = [cell.value for cell in row[1:13]]  # Month 1–12
        total = row[13].value  # Total column

        row_data = {
            "Category": current_category,
            "Subcategory": name,
            **{month_headers[i]: months[i] for i in range(len(months))},
            "Total": total
        }
        data.append(row_data)

    return pd.DataFrame(data)

# Parse Expense File
def parse_expense(file):
    wb = load_workbook(filename=BytesIO(file.read()), data_only=True)
    sheet = wb.active

    headers = [cell.value for cell in sheet[1]]
    data = []

    for row in sheet.iter_rows(min_row=2, values_only=True):
        if any(row):
            data.append(dict(zip(headers, row)))

    df = pd.DataFrame(data)
    df["Month"] = pd.to_datetime(df["Date"]).dt.month
    return df

# Summarize Monthly
def summarize_monthly(budget_df, expense_df):
    summary = []
    for month in range(1, 13):
        col = f"Month {month}"
        budget_total = budget_df.get(col, pd.Series()).sum()
        spent_total = expense_df[expense_df["Month"] == month]["Amount"].sum()
        summary.append({
            "Month": col,
            "Budgeted": budget_total,
            "Spent": spent_total,
            "Variance": budget_total - spent_total
        })
    return pd.DataFrame(summary)

# Summarize by Category, Subcategory, Vendor
def category_summary(expense_df):
    return expense_df.groupby(["Category", "Sub-Category", "Vendor"]).agg(
        Total_Spent=("Amount", "sum")
    ).reset_index()
