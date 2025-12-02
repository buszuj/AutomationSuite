# Core Excel I/O Module - Usage Guide

## Overview

The `Core/excel_io.py` module provides a centralized, reusable interface for all Excel operations across AutomationSuite projects.

## Features

✅ Read entire Excel files or specific sheets  
✅ Read specific columns, rows, or ranges  
✅ Filter data while reading  
✅ Validate Excel structure  
✅ Get comprehensive file information  
✅ Write DataFrames to Excel  
✅ Append to existing sheets  
✅ Find sheets by prefix  
✅ Multi-sheet operations  

---

## Quick Start

### 1. Basic Reading

```python
from Core.excel_io import excel_handler

# Read entire sheet
df = excel_handler.read_excel("file.xlsx", sheet_name="Sheet1")
print(df.head())
```

### 2. Read Specific Columns

```python
# By name
columns = ["ID", "Name", "Status"]
df = excel_handler.read_columns("file.xlsx", "Sheet1", columns)

# By index (first 3 columns)
df = excel_handler.read_columns("file.xlsx", "Sheet1", [0, 1, 2])
```

### 3. Filter While Reading

```python
# Get only active records
df = excel_handler.read_with_filter(
    "file.xlsx",
    "Sheet1",
    filter_column="Status",
    filter_value="Active"
)
```

### 4. Read All Sheets

```python
all_sheets = excel_handler.read_excel("file.xlsx", sheet_name=None)

for sheet_name, df in all_sheets.items():
    print(f"{sheet_name}: {len(df)} rows")
```

---

## Complete API Reference

### Reading Methods

#### `read_excel(file_path, sheet_name=None, **kwargs)`
Read Excel file and return DataFrame(s).

```python
# Single sheet
df = excel_handler.read_excel("file.xlsx", sheet_name="Sheet1")

# All sheets
all_sheets = excel_handler.read_excel("file.xlsx", sheet_name=None)

# With pandas options
df = excel_handler.read_excel(
    "file.xlsx",
    sheet_name="Sheet1",
    skiprows=2,
    usecols="A:E",
    na_values=["N/A"]
)
```

#### `read_sheet_names(file_path)`
Get list of all sheet names.

```python
sheets = excel_handler.read_sheet_names("file.xlsx")
print(sheets)  # ['Sheet1', 'Sheet2', 'Data']
```

#### `read_excel_range(file_path, sheet_name, start_row, end_row, start_col, end_col)`
Read specific range from sheet.

```python
# Read rows 10-20, columns 0-5
df = excel_handler.read_excel_range(
    "file.xlsx",
    "Sheet1",
    start_row=10,
    end_row=20,
    start_col=0,
    end_col=5
)
```

#### `read_column(file_path, sheet_name, column)`
Read single column.

```python
# By name
series = excel_handler.read_column("file.xlsx", "Sheet1", "Name")

# By index
series = excel_handler.read_column("file.xlsx", "Sheet1", 0)
```

#### `read_columns(file_path, sheet_name, columns)`
Read multiple columns.

```python
# By names
df = excel_handler.read_columns(
    "file.xlsx", "Sheet1",
    ["ID", "Name", "Status"]
)

# By indices
df = excel_handler.read_columns(
    "file.xlsx", "Sheet1",
    [0, 1, 2]
)
```

#### `read_with_filter(file_path, sheet_name, filter_column, filter_value)`
Read and filter data.

```python
df = excel_handler.read_with_filter(
    "file.xlsx",
    "Sheet1",
    filter_column="Department",
    filter_value="Sales"
)
```

#### `get_cell_value(file_path, sheet_name, row, column)`
Get single cell value.

```python
# By column name
value = excel_handler.get_cell_value("file.xlsx", "Sheet1", 5, "Name")

# By column index
value = excel_handler.get_cell_value("file.xlsx", "Sheet1", 5, 1)
```

#### `find_sheets_by_prefix(file_path, prefix)`
Find sheets starting with prefix.

```python
# Find all sheets starting with "S "
sheets = excel_handler.find_sheets_by_prefix("file.xlsx", "S ")
print(sheets)  # ['S IQVIA', 'S PFM', 'S Pfizer']
```

#### `read_multiple_sheets(file_path, sheet_names)`
Read specific sheets.

```python
sheets_to_read = ["Sheet1", "Sheet2", "Data"]
result = excel_handler.read_multiple_sheets("file.xlsx", sheets_to_read)

for name, df in result.items():
    print(f"{name}: {len(df)} rows")
```

---

### Writing Methods

#### `write_excel(data, file_path, sheet_name='Sheet1', **kwargs)`
Write DataFrame(s) to Excel.

```python
# Single sheet
excel_handler.write_excel(df, "output.xlsx", sheet_name="Results")

# Multiple sheets
data_dict = {
    'Sheet1': df1,
    'Sheet2': df2,
    'Summary': df3
}
excel_handler.write_excel(data_dict, "output.xlsx")
```

#### `append_to_sheet(data, file_path, sheet_name='Sheet1')`
Append DataFrame to existing sheet.

```python
# Append new data to existing file
excel_handler.append_to_sheet(new_df, "existing.xlsx", sheet_name="Data")
```

---

### Information Methods

#### `get_excel_info(file_path)`
Get comprehensive file information.

```python
info = excel_handler.get_excel_info("file.xlsx")

print(f"File: {info['file_path']}")
print(f"Size: {info['file_size']} bytes")
print(f"Sheets: {info['sheet_names']}")

for sheet_name, details in info['sheets'].items():
    print(f"\n{sheet_name}:")
    print(f"  Rows: {details['rows']}")
    print(f"  Columns: {details['columns']}")
    print(f"  Column Names: {details['column_names']}")
    print(f"  Data Types: {details['dtypes']}")
```

#### `validate_excel_structure(file_path, sheet_name, required_columns)`
Validate sheet has required columns.

```python
required = ["ID", "Name", "Status", "Date"]
is_valid, missing = excel_handler.validate_excel_structure(
    "file.xlsx",
    "Sheet1",
    required
)

if not is_valid:
    print(f"Missing columns: {missing}")
else:
    print("Structure valid!")
```

---

## Template Scripts

Use these templates as starting points for your projects:

### 1. Quick Start Template
**File:** `Core/templates/quickstart_excel.py`

Simple template for common tasks. Best for beginners.

```python
from Core.excel_io import excel_handler

file_path = "your_file.xlsx"
df = excel_handler.read_excel(file_path, sheet_name="Sheet1")
print(df.head())
```

### 2. Reader Template
**File:** `Core/templates/excel_reader_template.py`

Comprehensive template with 11+ examples:
- Basic reading
- Read all sheets
- Specific columns
- Filtering
- Ranges
- Validation
- Multiple files
- Advanced options

### 3. Processor Template
**File:** `Core/templates/excel_processor_template.py`

Full data processing pipeline with class structure:
- Load data
- Validate structure
- Clean data
- Transform data
- Analyze data
- Export results

**Usage:**
```python
from excel_processor_template import ExcelDataProcessor

processor = ExcelDataProcessor("input.xlsx", sheet_name="Data")
if processor.process():
    processor.export_results("output.xlsx")
```

---

## Common Patterns

### Pattern 1: Load, Process, Export

```python
from Core.excel_io import excel_handler

# Load
df = excel_handler.read_excel("input.xlsx", sheet_name="Data")

# Process
df_filtered = df[df['Status'] == 'Active']
df_processed = df_filtered[['ID', 'Name', 'Value']]
df_processed['Total'] = df_processed['Value'] * 1.1

# Export
excel_handler.write_excel(df_processed, "output.xlsx", sheet_name="Results")
```

### Pattern 2: Multiple Sheets Processing

```python
# Read all sheets
all_sheets = excel_handler.read_excel("file.xlsx", sheet_name=None)

# Process each
results = {}
for name, df in all_sheets.items():
    # Process
    processed = df[df['Value'] > 100]
    results[f"{name}_Processed"] = processed

# Write all results
excel_handler.write_excel(results, "all_results.xlsx")
```

### Pattern 3: Validation Before Processing

```python
file_path = "data.xlsx"
sheet_name = "Sheet1"
required_cols = ["ID", "Name", "Value"]

# Validate
is_valid, missing = excel_handler.validate_excel_structure(
    file_path, sheet_name, required_cols
)

if not is_valid:
    raise ValueError(f"Missing columns: {missing}")

# Process
df = excel_handler.read_excel(file_path, sheet_name)
# ... rest of processing
```

### Pattern 4: Incremental Data Collection

```python
import pandas as pd

files = ["file1.xlsx", "file2.xlsx", "file3.xlsx"]
all_data = []

for file in files:
    df = excel_handler.read_excel(file, sheet_name="Data")
    all_data.append(df)

# Combine
combined = pd.concat(all_data, ignore_index=True)
excel_handler.write_excel(combined, "combined.xlsx")
```

---

## Integration Examples

### Example 1: CEVA Launcher Integration

```python
# In CEVA_Launcher project
from Core.excel_io import excel_handler

# Read CEVA configuration
config_df = excel_handler.read_excel(
    "CEVA_config.xlsx",
    sheet_name="Languages"
)

# Process language pairs
for _, row in config_df.iterrows():
    source = row['Source']
    target = row['Target']
    process_language_pair(source, target)
```

### Example 2: One_Stop_Shop Integration

```python
# In One_Stop_Shop
from Core.excel_io import excel_handler

# Read rate sheet
ratesheet_df = excel_handler.read_excel(
    "One_BP_IQ fixed.01.xlsx",
    sheet_name="S IQVIA"
)

# Get rates for specific language pair
rates = excel_handler.read_with_filter(
    "One_BP_IQ fixed.01.xlsx",
    "S IQVIA",
    filter_column="Source Language",
    filter_value="English (GB)"
)
```

### Example 3: KP_Validator Integration

```python
# In KP_Validator
from Core.excel_io import excel_handler

# Validate input file structure
required = ["Project_ID", "Status", "Language"]
is_valid, missing = excel_handler.validate_excel_structure(
    "input.xlsx", "Data", required
)

if is_valid:
    df = excel_handler.read_excel("input.xlsx", sheet_name="Data")
    # ... validation logic
```

---

## Error Handling

Always handle potential errors:

```python
from Core.excel_io import excel_handler
from Core.utils.logger import get_logger

logger = get_logger(__name__)

try:
    df = excel_handler.read_excel("file.xlsx", sheet_name="Sheet1")
    logger.info(f"Loaded {len(df)} rows")
    
except FileNotFoundError:
    logger.error("File not found")
    
except KeyError as e:
    logger.error(f"Sheet not found: {e}")
    
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

---

## Performance Tips

1. **Read only needed columns:**
   ```python
   df = excel_handler.read_columns(file, sheet, ["Col1", "Col2"])
   ```

2. **Use filters early:**
   ```python
   df = excel_handler.read_with_filter(file, sheet, "Status", "Active")
   ```

3. **Cache repeated reads:**
   ```python
   df = excel_handler.read_excel(file, sheet)  # Store in variable
   # Use df multiple times
   ```

4. **Clear cache when done:**
   ```python
   excel_handler.clear_cache()
   ```

---

## Troubleshooting

### Issue: "File not found"
**Solution:** Use absolute paths or Path objects
```python
from pathlib import Path
file_path = Path(__file__).parent / "data" / "file.xlsx"
```

### Issue: "Sheet not found"
**Solution:** List available sheets first
```python
sheets = excel_handler.read_sheet_names(file_path)
print(f"Available: {sheets}")
```

### Issue: "Column not found"
**Solution:** Validate structure first
```python
is_valid, missing = excel_handler.validate_excel_structure(
    file, sheet, required_columns
)
```

### Issue: Memory issues with large files
**Solution:** Read in chunks or specific ranges
```python
# Read only needed range
df = excel_handler.read_excel_range(
    file, sheet, start_row=0, end_row=1000
)
```

---

## Next Steps

1. **Copy a template** from `Core/templates/`
2. **Modify for your needs**
3. **Test with your data**
4. **Integrate into your project**

See `Core/templates/README.md` for more details on each template.
