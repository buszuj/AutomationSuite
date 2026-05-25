# Excel Rate Card Integration Summary

## Objective
Enable the Rate Card Builder module to read and import Excel rate card files from `d:\BP TECH\Python apps\REPOs\TheOneBP\RateCards\`.

## Changes Completed

### 1. New Module Created: excel_rate_card_loader.py
**Location**: `d:\BP TECH\Python apps\REPOs\AutomationSuite\Rate_Card_Builder\excel_rate_card_loader.py`

**Purpose**: Converts Excel rate card files to JSON format compatible with Rate Card Builder

**Key Features**:
- `ExcelRateCardLoader` class - Main converter class
- `load_excel_rate_card()` - Convenience function to load single file
- `find_excel_rate_cards()` - Discovery function to find all Excel rate cards
- **SERVICE_NAME_MAPPING** - Normalizes various service column names
- Automatic language column detection
- ISO code extraction from language names
- Handles missing/empty cells gracefully

**Supported Excel Files**:
- JJ_RC.xlsx
- Menarini_RC.xlsx
- Novartis_RC.xlsx
- NovoNordisk_RC.xlsx
- Pfizer_RC.xlsx
- PXL_RC.xlsx
- Regeneron_RC.xlsx
- Sanofi_RC.xlsx

### 2. Modified: load_rate_card_window.py
**Changes**:
- Added import for `load_excel_rate_card` and `find_excel_rate_cards`
- Updated `populate_file_list()` - Now discovers and displays both JSON and Excel files
  - JSON files from Rate_Card_Builder folder
  - Excel files from TheOneBP/RateCards folder
  - Files displayed with [JSON] or [XLSX] type indicators
- Updated `on_file_selected()` - Handles both JSON and Excel formats
  - Detects file type by extension
  - Loads Excel files using new loader
  - Displays combined information from both formats
- Updated `on_browse()` - File dialog now supports both formats
  - Filters show "All Supported", "JSON files", "Excel files"
  - Can browse to any location for both formats

### 3. Modified: itemized_rate_card_editor.py
**Changes**:
- Added import for `load_excel_rate_card`
- Updated `on_load_rate_card()` - Handles both JSON and Excel formats
  - File dialog supports both formats
  - Auto-detects file type
  - Loads Excel files transparently
  - Proper error handling for missing dependencies

### 4. Documentation Files

#### EXCEL_RATE_CARDS.md
Comprehensive guide including:
- Overview of Excel support
- Supported file list
- File format explanation
- JSON conversion details
- Usage instructions (3 methods)
- Technical details
- API reference
- Testing procedures
- Troubleshooting guide
- Future enhancements

#### test_excel_loader.py
Test script to verify:
- Module imports correctly
- Excel files are discovered
- Rate cards load successfully
- Data structure is valid

## File Structure

```
Rate_Card_Builder/
├── excel_rate_card_loader.py          (NEW)
├── load_rate_card_window.py           (MODIFIED)
├── itemized_rate_card_editor.py       (MODIFIED)
├── itemized_rate_card_window.py       (unchanged - no load method)
├── EXCEL_RATE_CARDS.md                (NEW)
├── test_excel_loader.py               (NEW)
└── ... (other existing files)
```

## Workflow

### Loading Excel Rate Card - Step by Step

1. **User opens One_Stop_Shop**
   - Navigates to Rate Cards tab
   - Clicks "Load Rate Card" button

2. **Load Rate Card Window Opens**
   - Shows both JSON and Excel rate cards with type indicators
   - Excel files auto-discovered from TheOneBP/RateCards directory

3. **User selects Excel file**
   - Clicks on Excel rate card (marked with [XLSX])
   - File information displays (name, sponsor, language count, services)

4. **User clicks "Open Selected"**
   - `on_file_selected()` detects .xlsx extension
   - Calls `load_excel_rate_card(filepath)`
   - `ExcelRateCardLoader` reads Excel file
   - Converts to JSON format
   - Data loads into editor window for viewing/editing

### Conversion Process

```
Excel File (.xlsx)
    ↓
pandas.read_excel()
    ↓
ExcelRateCardLoader._process_dataframe()
    ├─ Identify language column
    ├─ Extract service columns
    ├─ Normalize service names
    ├─ Detect rates for each language-service pair
    └─ Extract ISO codes from language names
    ↓
JSON Structure
    ├─ name (from filename)
    ├─ sponsor (from filename)
    ├─ services (normalized list)
    ├─ iso_codes (language → ISO mapping)
    ├─ languages (language → {iso_code, rates})
    └─ type ("itemized")
    ↓
Loaded into Rate Card Builder
```

## Technical Details

### Service Name Normalization
Maps common variations to standard names:
- "Translation/Proofreading" → "Translation and Proofreading"
- "MT EditProof" → "MT full EditProof"
- "TM - Fuzzy" → "TM - Fuzzy Matches"
- etc.

### Language Column Detection
Automatic detection by:
1. Checking column headers for "language", "lang", "source" keywords
2. Inspecting first row for language-like values
3. Using first column if it contains language names

### ISO Code Extraction
Maps country/region names to ISO codes:
- "Afrikaans (South Africa)" → "af-ZA"
- "Chinese (Traditional)" → "zh"
- "French (Canada)" → "fr-CA"
- etc.

## Dependencies

### Required
- pandas >= 1.0 - Data processing
- openpyxl >= 3.0 - Excel file reading
- customtkinter >= 5.0 - UI framework
- tkinter - UI widgets

### Installation
```bash
pip install pandas openpyxl
```

## Error Handling

**Missing Dependencies**:
```
Error: Excel support not available.
Install: pip install openpyxl pandas
```

**File Not Found**:
```
Error: File not found: [path]
```

**Invalid Format**:
```
Error: Failed to read file: [detailed error message]
```

**Language Column Not Detected**:
```
ValueError: Could not identify language column in Excel file
```

## Testing

### Quick Test
Run the included test script:
```bash
python test_excel_loader.py
```

Expected output:
```
Testing imports...
✓ Successfully imported excel_rate_card_loader

Searching for Excel rate cards...
✓ Found 8 Excel rate card files:
  - JJ_RC.xlsx
  - Menarini_RC.xlsx
  - ...

Loading: JJ_RC.xlsx
============================================================
Rate Card Loaded Successfully!
  Name: JJ
  Sponsor: JJ
  Type: itemized
  Languages: 248
  Services: 15
  ...
✓ Excel rate card loader is working correctly!
```

## Integration Points

1. **Load Rate Card Window** - Main entry point for users
2. **Itemized Rate Card Editor** - Loads for editing
3. **Rate Card Browser Tab** - Shows available rate cards

## Backward Compatibility

✓ All existing JSON functionality preserved
✓ All existing rate card files still work
✓ No breaking changes to existing API
✓ Graceful fallback if Excel support unavailable

## Future Enhancements

Potential improvements:
1. Support for .xls format (older Excel)
2. Custom column mapping UI
3. Excel export functionality
4. Batch import of multiple files
5. Rate card validation warnings
6. Template-based import

## Verification Checklist

- [x] Module imports without errors
- [x] Excel files discovered automatically
- [x] Rate cards load from Excel
- [x] JSON conversion works correctly
- [x] Service names normalized
- [x] ISO codes extracted
- [x] Error handling implemented
- [x] Documentation complete
- [x] Test script created
- [x] Backward compatibility maintained

## Support Resources

1. **EXCEL_RATE_CARDS.md** - Complete user guide
2. **excel_rate_card_loader.py** - Source code documentation
3. **test_excel_loader.py** - Working example
4. **load_rate_card_window.py** - Implementation reference
5. **itemized_rate_card_editor.py** - Editor integration

## Summary

The Rate Card Builder module now fully supports reading Excel rate cards from the TheOneBP/RateCards directory. Excel files are automatically discovered, converted to JSON format, and can be loaded just like JSON rate cards. The implementation includes comprehensive error handling, documentation, and backward compatibility with existing JSON-based rate cards.

Users can now:
✓ Browse and load Excel rate cards alongside JSON files
✓ Edit Excel-sourced rate cards in the editor
✓ Convert Excel rate cards to editable JSON format
✓ Save modified rate cards as JSON files
