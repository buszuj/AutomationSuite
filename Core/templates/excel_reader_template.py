"""
Excel Data Reader Template Script
Use this template to read data from Excel files in your AutomationSuite projects.

This script demonstrates various ways to read Excel data using the Core excel_io module.
Copy and modify this template for your specific needs.
"""

import sys
from pathlib import Path

# Add Core to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Core.excel_io import excel_handler
from Core.utils.logger import get_logger
import pandas as pd

# Initialize logger
logger = get_logger(__name__)


def example_basic_read():
    """Example: Basic Excel file reading."""
    print("\n=== EXAMPLE 1: Basic Read ===")
    
    # Replace with your file path
    file_path = "your_file.xlsx"
    
    # Read entire sheet
    df = excel_handler.read_excel(file_path, sheet_name="Sheet1")
    print(f"Loaded {len(df)} rows from Sheet1")
    print(df.head())
    
    # Access data
    print(f"\nColumns: {df.columns.tolist()}")
    print(f"Shape: {df.shape}")


def example_read_all_sheets():
    """Example: Read all sheets from Excel file."""
    print("\n=== EXAMPLE 2: Read All Sheets ===")
    
    file_path = "your_file.xlsx"
    
    # Read all sheets
    all_sheets = excel_handler.read_excel(file_path, sheet_name=None)
    
    for sheet_name, df in all_sheets.items():
        print(f"\nSheet: {sheet_name}")
        print(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
        print(f"  Columns: {df.columns.tolist()}")


def example_read_specific_columns():
    """Example: Read specific columns only."""
    print("\n=== EXAMPLE 3: Read Specific Columns ===")
    
    file_path = "your_file.xlsx"
    sheet_name = "Sheet1"
    
    # Method 1: Read specific columns by name
    columns_to_read = ["Column1", "Column2", "Column3"]
    df = excel_handler.read_columns(file_path, sheet_name, columns_to_read)
    print(f"Read columns: {columns_to_read}")
    print(df.head())
    
    # Method 2: Read specific columns by index
    column_indices = [0, 1, 2]  # First three columns
    df = excel_handler.read_columns(file_path, sheet_name, column_indices)
    print(f"\nRead columns by index: {column_indices}")
    print(df.head())


def example_read_with_filter():
    """Example: Read and filter data."""
    print("\n=== EXAMPLE 4: Read with Filter ===")
    
    file_path = "your_file.xlsx"
    sheet_name = "Sheet1"
    
    # Filter by column value
    filter_column = "Status"
    filter_value = "Active"
    
    df = excel_handler.read_with_filter(
        file_path, 
        sheet_name, 
        filter_column, 
        filter_value
    )
    
    print(f"Filtered data where {filter_column} = {filter_value}")
    print(f"Found {len(df)} matching rows")
    print(df.head())


def example_read_range():
    """Example: Read specific range from Excel."""
    print("\n=== EXAMPLE 5: Read Specific Range ===")
    
    file_path = "your_file.xlsx"
    sheet_name = "Sheet1"
    
    # Read rows 10-20, columns 0-5
    df = excel_handler.read_excel_range(
        file_path,
        sheet_name,
        start_row=10,
        end_row=20,
        start_col=0,
        end_col=5
    )
    
    print(f"Read range: rows 10-20, columns 0-5")
    print(df)


def example_get_excel_info():
    """Example: Get Excel file information."""
    print("\n=== EXAMPLE 6: Get Excel Info ===")
    
    file_path = "your_file.xlsx"
    
    # Get comprehensive file info
    info = excel_handler.get_excel_info(file_path)
    
    print(f"File: {info['file_path']}")
    print(f"Size: {info['file_size']} bytes")
    print(f"Sheets: {info['sheet_names']}")
    
    for sheet_name, sheet_info in info['sheets'].items():
        print(f"\n  Sheet: {sheet_name}")
        print(f"    Rows: {sheet_info['rows']}")
        print(f"    Columns: {sheet_info['columns']}")
        print(f"    Column Names: {sheet_info['column_names']}")


def example_validate_structure():
    """Example: Validate Excel structure."""
    print("\n=== EXAMPLE 7: Validate Structure ===")
    
    file_path = "your_file.xlsx"
    sheet_name = "Sheet1"
    
    # Define required columns
    required_columns = ["ID", "Name", "Status", "Date"]
    
    is_valid, missing = excel_handler.validate_excel_structure(
        file_path,
        sheet_name,
        required_columns
    )
    
    if is_valid:
        print("✅ Excel structure is valid")
    else:
        print(f"❌ Missing columns: {missing}")


def example_find_sheets_by_prefix():
    """Example: Find sheets by prefix."""
    print("\n=== EXAMPLE 8: Find Sheets by Prefix ===")
    
    file_path = "your_file.xlsx"
    prefix = "S "  # Example: find all sheets starting with "S "
    
    matching_sheets = excel_handler.find_sheets_by_prefix(file_path, prefix)
    
    print(f"Sheets starting with '{prefix}':")
    for sheet in matching_sheets:
        print(f"  - {sheet}")


def example_process_data():
    """Example: Read and process data."""
    print("\n=== EXAMPLE 9: Read and Process Data ===")
    
    file_path = "your_file.xlsx"
    sheet_name = "Sheet1"
    
    # Read data
    df = excel_handler.read_excel(file_path, sheet_name)
    
    # Process data (example operations)
    print("Original data:")
    print(df.head())
    
    # Filter rows
    filtered_df = df[df['Status'] == 'Active']
    print(f"\nFiltered to {len(filtered_df)} active rows")
    
    # Select specific columns
    processed_df = filtered_df[['ID', 'Name', 'Value']]
    print("\nProcessed data:")
    print(processed_df.head())
    
    # Calculate statistics
    if 'Value' in processed_df.columns:
        total = processed_df['Value'].sum()
        average = processed_df['Value'].mean()
        print(f"\nTotal Value: {total}")
        print(f"Average Value: {average}")
    
    return processed_df


def example_read_multiple_files():
    """Example: Read from multiple Excel files."""
    print("\n=== EXAMPLE 10: Read Multiple Files ===")
    
    file_paths = [
        "file1.xlsx",
        "file2.xlsx",
        "file3.xlsx"
    ]
    
    all_data = []
    
    for file_path in file_paths:
        try:
            df = excel_handler.read_excel(file_path, sheet_name="Sheet1")
            all_data.append(df)
            print(f"✅ Loaded {len(df)} rows from {file_path}")
        except FileNotFoundError:
            print(f"⚠️  File not found: {file_path}")
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
    
    # Combine all data
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"\n✅ Combined {len(combined_df)} total rows from {len(all_data)} files")
        return combined_df


def example_advanced_reading():
    """Example: Advanced Excel reading with pandas options."""
    print("\n=== EXAMPLE 11: Advanced Reading ===")
    
    file_path = "your_file.xlsx"
    
    # Read with custom options
    df = excel_handler.read_excel(
        file_path,
        sheet_name="Sheet1",
        skiprows=2,          # Skip first 2 rows
        usecols="A:E",       # Read only columns A through E
        na_values=["N/A"],   # Treat "N/A" as missing
        dtype={'ID': str}    # Force ID column to string
    )
    
    print("Data with custom options:")
    print(df.head())
    print(f"Data types: {df.dtypes.to_dict()}")


def example_your_custom_logic():
    """
    YOUR CUSTOM LOGIC HERE
    
    Replace this function with your specific Excel reading needs.
    """
    print("\n=== YOUR CUSTOM LOGIC ===")
    
    # 1. Define your file path
    file_path = Path(__file__).parent / "data" / "your_excel_file.xlsx"
    
    # 2. Define which sheet to read
    sheet_name = "Sheet1"
    
    # 3. Read the data
    try:
        df = excel_handler.read_excel(file_path, sheet_name=sheet_name)
        logger.info(f"Successfully loaded {len(df)} rows from {sheet_name}")
        
        # 4. Validate data structure
        required_columns = ["Column1", "Column2", "Column3"]
        is_valid, missing = excel_handler.validate_excel_structure(
            file_path, sheet_name, required_columns
        )
        
        if not is_valid:
            logger.error(f"Missing required columns: {missing}")
            return None
        
        # 5. Process your data here
        # Example: Filter, transform, calculate, etc.
        processed_df = df.copy()
        
        # 6. Return or save processed data
        return processed_df
        
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error processing Excel file: {e}")
        return None


def main():
    """Main function - run examples or your custom logic."""
    
    print("="*60)
    print("Excel Data Reader Template")
    print("="*60)
    
    # Uncomment the examples you want to run:
    
    # example_basic_read()
    # example_read_all_sheets()
    # example_read_specific_columns()
    # example_read_with_filter()
    # example_read_range()
    # example_get_excel_info()
    # example_validate_structure()
    # example_find_sheets_by_prefix()
    # example_process_data()
    # example_read_multiple_files()
    # example_advanced_reading()
    
    # Run your custom logic
    result = example_your_custom_logic()
    
    if result is not None:
        print("\n✅ Processing complete!")
    else:
        print("\n❌ Processing failed!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
