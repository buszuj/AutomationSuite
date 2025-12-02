"""
Quick Start Excel Reader
Simple template for common Excel reading tasks.
Copy this file and modify for your needs.
"""

import sys
from pathlib import Path

# Add Core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Core.excel_io import excel_handler


def main():
    """
    QUICK START TEMPLATE
    
    1. Set your file path below
    2. Choose which example to use (uncomment one)
    3. Run the script
    """
    
    # ========================================
    # STEP 1: SET YOUR FILE PATH
    # ========================================
    file_path = "your_file.xlsx"  # <-- CHANGE THIS
    sheet_name = "Sheet1"         # <-- CHANGE THIS
    
    
    # ========================================
    # STEP 2: UNCOMMENT YOUR USE CASE
    # ========================================
    
    # --- USE CASE 1: Read entire sheet ---
    df = excel_handler.read_excel(file_path, sheet_name=sheet_name)
    print(f"Loaded {len(df)} rows")
    print(df.head())
    
    
    # --- USE CASE 2: Read specific columns ---
    # columns = ["Column1", "Column2", "Column3"]  # <-- CHANGE THESE
    # df = excel_handler.read_columns(file_path, sheet_name, columns)
    # print(df.head())
    
    
    # --- USE CASE 3: Filter data ---
    # filter_col = "Status"      # <-- CHANGE THIS
    # filter_val = "Active"      # <-- CHANGE THIS
    # df = excel_handler.read_with_filter(file_path, sheet_name, filter_col, filter_val)
    # print(f"Found {len(df)} rows where {filter_col} = {filter_val}")
    # print(df.head())
    
    
    # --- USE CASE 4: Get all sheet names ---
    # sheets = excel_handler.read_sheet_names(file_path)
    # print(f"Available sheets: {sheets}")
    
    
    # --- USE CASE 5: Read all sheets ---
    # all_sheets = excel_handler.read_excel(file_path, sheet_name=None)
    # for name, df in all_sheets.items():
    #     print(f"\nSheet: {name} - {len(df)} rows")
    
    
    # ========================================
    # STEP 3: PROCESS YOUR DATA
    # ========================================
    
    # Example: Filter rows
    # df_filtered = df[df['Status'] == 'Active']
    
    # Example: Select columns
    # df_selected = df[['Column1', 'Column2']]
    
    # Example: Calculate
    # total = df['Value'].sum()
    # average = df['Value'].mean()
    # print(f"Total: {total}, Average: {average}")
    
    
    # ========================================
    # STEP 4: EXPORT RESULTS (OPTIONAL)
    # ========================================
    
    # output_file = "output.xlsx"
    # excel_handler.write_excel(df, output_file, sheet_name="Results")
    # print(f"Saved to {output_file}")


if __name__ == "__main__":
    main()
