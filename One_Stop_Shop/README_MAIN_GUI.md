# One Stop Shop - Main GUI

## Overview
Central hub for job data import and GLE API integration. This tool allows you to import Excel files or pull data directly from the TransPerfect GLE Portal API, store it in memory, and view it in a spreadsheet-like interface.

## Features

### 📁 Import Job Data from File
- **Drag & Drop**: Drag Excel files directly onto the drop zone
- **File Browser**: Click "Browse for File" to select files from your system
- **Supported Formats**: .xlsx, .xls, .xlsm
- **In-Memory Storage**: Data is kept in memory until cleared or replaced

### 🌐 Pull GLE Data
- **API Integration**: Direct connection to TransPerfect GLE Portal API
- **Job ID Search**: Enter any GL Portal Number to fetch project data
- **OAuth Authentication**: Automatic token management
- **Excel Export**: API returns data in Excel format, automatically loaded into the application

### 📊 Data Actions
- **Show Raw Data**: View the entire dataset in a spreadsheet-like grid window
  - Displays all columns and rows
  - Scrollable interface
  - Shows up to 1000 rows for performance (with warning if more)
- **Clear Data**: Remove loaded data from memory

## Usage

### Launch the Application
```bash
cd "One_Stop_Shop"
python launch_main.py
```

### Import from File
1. **Option 1 - Drag & Drop**:
   - Drag an Excel file onto the drop zone
   - File will be automatically loaded

2. **Option 2 - Browse**:
   - Click "Browse for File"
   - Select your Excel file
   - Click "Open"

### Pull from GLE API
1. Enter the **GL Portal Number** (Job ID) in the text field
2. Click "Pull Data"
3. Wait for the API call to complete
4. Data will be automatically loaded

### View Data
- Once data is loaded (from file or API), click "Show Raw Data"
- A new window will open displaying the data in a table format
- Scroll to view all rows and columns

### Clear Data
- Click "Clear Data" when you want to remove the current dataset
- Confirm the action in the dialog

## API Configuration

The application uses the following GLE API credentials (production):

```python
TOKEN_URL = "https://sso.transperfect.com/connect/token"
CLIENT_ID = "6wZh7rFrLCQh0ZWGrMz8AcZWVAg74BqT"
CLIENT_SECRET = "c9H58gvpDyc46NY10Fp2eLVafTMtNzLg"
ORG_ID = "51334c7b-d7fb-4d40-ae95-f2f6808d97da"
```

## Technical Details

### Data Storage
- Data is stored in memory as a pandas DataFrame
- No persistent storage - data is discarded when:
  - Application is closed
  - "Clear Data" is clicked
  - New data is loaded (replaces existing)

### Dependencies
- `customtkinter>=5.2.0` - Modern UI framework
- `tkinterdnd2>=0.3.0` - Drag-and-drop support
- `pandas>=2.0.0` - Data manipulation
- `openpyxl>=3.1.0` - Excel file handling
- `requests>=2.31.0` - HTTP requests for API calls

### Performance
- Data viewer shows first 1000 rows to maintain UI responsiveness
- Full dataset remains in memory for processing
- Large files (>100MB) may take longer to load

## File Structure
```
One_Stop_Shop/
├── one_stop_shop_main.py    # Main application code
├── launch_main.py            # Application launcher
├── requirements.txt          # Python dependencies
└── README_MAIN_GUI.md        # This file
```

## Future Enhancements
- Job processing workflow integration
- Data export functionality
- Advanced filtering and search
- Multiple dataset management
- Data validation and cleaning tools

## Troubleshooting

### Drag & Drop Not Working
- Ensure `tkinterdnd2` is installed: `pip install tkinterdnd2`
- Try the "Browse for File" option instead

### API Connection Failed
- Check internet connection
- Verify credentials are correct
- Ensure Job ID exists in the system
- Check firewall settings

### File Load Error
- Ensure file is a valid Excel format
- Check file is not corrupted
- Try opening file in Excel first to verify

## Status Bar
The status bar at the bottom shows:
- "Ready" - Application ready for input
- "Loading file..." - File being read
- "Fetching data from GLE API..." - API call in progress
- "✅ File loaded: [filename]" - Success
- "✅ GLE data pulled for Job ID: [id]" - Success
- "❌ Failed..." - Error occurred

## Integration
This tool works alongside other One Stop Shop modules:
- Entity Manager
- Service Mapper
- Workflow Manager
- Quote Calculator

Launch them separately or integrate them into a unified launcher in the future.
