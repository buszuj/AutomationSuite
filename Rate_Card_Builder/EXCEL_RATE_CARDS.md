# Excel Rate Card Support for Rate Card Builder

## Overview
The Rate Card Builder module has been enhanced to support reading Excel rate card files from `d:\BP TECH\Python apps\REPOs\TheOneBP\RateCards\`.

## Features

### Supported Excel Files
The following Excel rate card files are now supported:
- JJ_RC.xlsx
- Menarini_RC.xlsx
- Novartis_RC.xlsx
- NovoNordisk_RC.xlsx
- Pfizer_RC.xlsx
- PXL_RC.xlsx
- Regeneron_RC.xlsx
- Sanofi_RC.xlsx

### File Format
Each Excel rate card contains:
- **Language Column**: Language name (e.g., "Afrikaans (South Africa)", "Chinese (Traditional)")
- **Service Columns**: Multiple columns for different services (Translation, MT, TM Fuzzy, TM Exact, etc.)
- **Rate Values**: Numeric rates for each language-service combination

### Conversion to JSON
Excel rate cards are automatically converted to the Rate Card Builder's JSON format:
```json
{
  "name": "Pfizer",
  "sponsor": "Pfizer",
  "services": ["Translation and Proofreading", "MT full EditProof", ...],
  "iso_codes": {"Afrikaans (South Africa)": "af-ZA", ...},
  "languages": {
    "Afrikaans (South Africa)": {
      "iso_code": "af-ZA",
      "rates": {"Translation and Proofreading": "0.21", ...}
    },
    ...
  },
  "type": "itemized",
  "source": "Excel: Pfizer_RC.xlsx"
}
```

## Components Created/Modified

### New Files
1. **excel_rate_card_loader.py**
   - `ExcelRateCardLoader` class for converting Excel to JSON
   - `load_excel_rate_card()` function for loading Excel files
   - `find_excel_rate_cards()` function for discovering Excel files
   - Service name normalization and language column detection

### Modified Files
1. **load_rate_card_window.py**
   - Updated file dialog to support both JSON and XLSX files
   - Added Excel rate card discovery from TheOneBP/RateCards directory
   - Updated `populate_file_list()` to show both JSON and Excel files with type indicators
   - Updated `on_file_selected()` to handle Excel files
   - Updated `on_browse()` file dialog filters

2. **itemized_rate_card_editor.py**
   - Added import for `load_excel_rate_card`
   - Updated `on_load_rate_card()` to support Excel files
   - File dialog now shows both JSON and XLSX formats
   - Proper error handling for missing Excel dependencies

## Usage

### Loading Excel Rate Cards

#### Method 1: Load Rate Card Window
1. Open One_Stop_Shop
2. Navigate to Rate Cards tab
3. Click "Load Rate Card"
4. In the "Load Rate Card" window:
   - Browse through the list showing both JSON and Excel files
   - Excel files are marked with `[XLSX]` prefix
   - Select an Excel rate card and click "Open Selected"

#### Method 2: Browse Files
1. In the "Load Rate Card" window
2. Click "Browse Files"
3. Navigate to `d:\BP TECH\Python apps\REPOs\TheOneBP\RateCards\`
4. Select an Excel file (.xlsx)
5. File loads and converts automatically

#### Method 3: Itemized Editor
1. In the Itemized Rate Card tab
2. Click "Load Rate Card" button
3. Select an Excel file from the file dialog
4. Rate card loads into the editor for modification

### Automatic Discovery
Excel rate cards from `d:\BP TECH\Python apps\REPOs\TheOneBP\RateCards\` are automatically discovered and displayed in:
- Load Rate Card window file list
- File browser dialogs

## Technical Details

### Excel Sheet Structure
The loader expects:
- **First column**: Language names (detected automatically)
- **Subsequent columns**: Service rates
- **Column headers**: Service names

### Service Name Mapping
Common service name variations are automatically normalized:
- "Translation/Proofreading" → "Translation and Proofreading"
- "MT EditProof" → "MT full EditProof"
- "TM - Fuzzy" → "TM - Fuzzy Matches"
- etc.

### Language Column Detection
The loader automatically identifies the language column by:
1. Checking for column names containing "language", "lang", "source", etc.
2. Inspecting first row values for language-like names
3. Using first column if it contains language names

### ISO Code Extraction
ISO codes are extracted from parenthetical country/region identifiers:
- "Afrikaans (South Africa)" → "af-ZA"
- "French (Canada)" → "fr-CA"
- etc.

## Dependencies

### Required
- pandas >= 1.0
- openpyxl >= 3.0 (for Excel reading)
- customtkinter >= 5.0
- tkinter (Python standard library)

### Installation
```bash
pip install pandas openpyxl
```

## Error Handling

### Missing Dependencies
If pandas or openpyxl are not installed:
```
Error: Excel support not available. 
Install: pip install openpyxl pandas
```

### File Not Found
If the Excel file path is invalid:
```
Error: File not found: [path]
```

### Invalid Format
If the Excel file format is unexpected:
```
Error: Failed to read file: [detailed error message]
```

## API Reference

### ExcelRateCardLoader Class

```python
from excel_rate_card_loader import ExcelRateCardLoader

# Initialize loader
loader = ExcelRateCardLoader("path/to/rate_card.xlsx")

# Load and convert to JSON
rate_card_data = loader.load_rate_card()
```

### Functions

#### load_excel_rate_card()
```python
from excel_rate_card_loader import load_excel_rate_card

rate_card = load_excel_rate_card("path/to/Pfizer_RC.xlsx")
# Returns: dict with JSON rate card structure
```

#### find_excel_rate_cards()
```python
from excel_rate_card_loader import find_excel_rate_cards

files = find_excel_rate_cards()
# Returns: list of (filename, filepath) tuples

# Or specify a directory
files = find_excel_rate_cards("d:/BP TECH/Python apps/REPOs/TheOneBP/RateCards")
```

## Testing

### Verify Excel Support
```python
from excel_rate_card_loader import find_excel_rate_cards, load_excel_rate_card

# List available Excel rate cards
files = find_excel_rate_cards()
print("Available rate cards:")
for filename, filepath in files:
    print(f"  - {filename}")

# Load a specific rate card
if files:
    filename, filepath = files[0]
    rate_card = load_excel_rate_card(filepath)
    print(f"\nLoaded: {rate_card['name']}")
    print(f"Languages: {len(rate_card['languages'])}")
    print(f"Services: {len(rate_card['services'])}")
```

## Troubleshooting

### Excel Files Not Appearing in List
1. Verify Excel files exist in `d:\BP TECH\Python apps\REPOs\TheOneBP\RateCards\`
2. Check that files have .xlsx extension (not .xls)
3. Ensure pandas and openpyxl are installed

### "File not found" Error
1. Verify the file path is correct
2. Check file permissions
3. Try browsing to the file manually

### Language Column Not Detected
1. Verify the first column contains language names
2. Check that language names are not empty
3. Ensure column header is recognizable (language, lang, source, etc.)

### Rate Values Not Loading
1. Verify rate values are in numeric format (or numeric strings like "0.21")
2. Check that service column headers are recognizable
3. Look for data validation or hidden columns in Excel file

## Future Enhancements

Potential improvements:
1. Support for .xls format (older Excel)
2. Custom column mapping UI
3. Rate card preview before loading
4. Batch import of multiple Excel files
5. Excel export functionality
6. Rate card validation and warnings
7. Template-based Excel import

## Support

For issues or questions:
1. Check error messages in the application
2. Verify Excel file format matches expected structure
3. Check Python console output for detailed error logs
4. Ensure all required dependencies are installed
