# Core Excel Templates

This folder contains template scripts for common Excel operations using the Core `excel_io` module.

## Available Templates

### 1. `excel_reader_template.py`
Complete template with 11+ examples of reading Excel data:
- Basic reading
- Read all sheets
- Read specific columns
- Filter data
- Read ranges
- Get file info
- Validate structure
- Find sheets by prefix
- Process data
- Read multiple files
- Advanced options

**Use when:** You need to read Excel data in various ways

**Example:**
```python
from Core.excel_io import excel_handler

df = excel_handler.read_excel("file.xlsx", sheet_name="Sheet1")
```

### 2. `excel_processor_template.py`
Template class for complete data processing pipeline:
- Load data
- Validate structure
- Clean data
- Transform data
- Analyze data
- Export results

**Use when:** You need a structured approach to process Excel data

**Example:**
```python
processor = ExcelDataProcessor("input.xlsx")
processor.process()
processor.export_results("output.xlsx")
```

## Quick Start

1. **Copy a template to your project folder**
   ```powershell
   Copy-Item "Core\templates\excel_reader_template.py" "YourProject\my_script.py"
   ```

2. **Modify for your needs**
   - Update file paths
   - Uncomment examples you need
   - Add your custom logic
   - Adjust column names

3. **Run your script**
   ```powershell
   python my_script.py
   ```

## Common Patterns

### Read Single Sheet
```python
from Core.excel_io import excel_handler

df = excel_handler.read_excel("file.xlsx", sheet_name="Sheet1")
```

### Read All Sheets
```python
all_sheets = excel_handler.read_excel("file.xlsx", sheet_name=None)
for sheet_name, df in all_sheets.items():
    print(f"Processing {sheet_name}...")
```

### Read Specific Columns
```python
columns = ["ID", "Name", "Value"]
df = excel_handler.read_columns("file.xlsx", "Sheet1", columns)
```

### Filter Data
```python
df = excel_handler.read_with_filter(
    "file.xlsx", 
    "Sheet1", 
    filter_column="Status",
    filter_value="Active"
)
```

### Validate Structure
```python
required_cols = ["ID", "Name", "Status"]
is_valid, missing = excel_handler.validate_excel_structure(
    "file.xlsx", "Sheet1", required_cols
)
```

### Get File Info
```python
info = excel_handler.get_excel_info("file.xlsx")
print(f"Sheets: {info['sheet_names']}")
```

## Tips

1. **Use the logger** for better debugging:
   ```python
   from Core.utils.logger import get_logger
   logger = get_logger(__name__)
   logger.info("Processing data...")
   ```

2. **Handle errors gracefully**:
   ```python
   try:
       df = excel_handler.read_excel(file_path, sheet_name)
   except FileNotFoundError:
       logger.error(f"File not found: {file_path}")
   except Exception as e:
       logger.error(f"Error: {e}")
   ```

3. **Validate before processing**:
   ```python
   is_valid, missing = excel_handler.validate_excel_structure(
       file_path, sheet_name, required_columns
   )
   if not is_valid:
       raise ValueError(f"Missing columns: {missing}")
   ```

4. **Use pathlib for file paths**:
   ```python
   from pathlib import Path
   
   file_path = Path(__file__).parent / "data" / "file.xlsx"
   ```

## Integration with Projects

These templates work seamlessly with all AutomationSuite projects:
- **CEVA_Launcher**
- **KP_Validator**
- **One_Stop_Shop**
- Your custom projects

Simply import the `excel_handler` from Core and use the methods shown in the templates.
