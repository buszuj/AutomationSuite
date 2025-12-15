# PA Template System - User Guide
**One Stop Shop PA Template Integration**

## Overview
The PA Template System allows you to configure custom field mappings per account for generating ProjectA import worksheets. Each account can have its own template configuration that defines how job data is transformed into PA-ready format.

---

## Features Implemented

### ✅ 1. Configure Template Mapper
**Menu: PA Template → Configure Template Mapper**

- Visual GUI for creating field mappings
- Supports 4 mapping types:
  - **Direct**: Copy directly from source column
  - **Static**: Use a fixed value
  - **Calculated**: Apply formula/calculation
  - **Concatenate**: Combine multiple columns
- Format options: date, number, text
- Save templates per account
- Auto-loads existing templates for editing

**How to use:**
1. Select an account first (Configuration → Select Account)
2. Open the Template Mapper
3. Click "➕ Add Mapping" to create field mappings
4. Fill in:
   - PA Field Name (what appears in ProjectA)
   - Mapping Type (how to get the value)
   - Source Column (which column to pull from)
   - Static Value (if using static mapping)
   - Format (optional formatting)
5. Click "👁️ Preview" to see how it will look
6. Click "💾 Save Template" to save

---

### ✅ 2. Preview Integration Data
**Menu: PA Template → Preview Integration Data**

- Shows how your job data will look when transformed
- Displays 2-column format (Field Name | Value)
- Uses first row of data as example
- No file generated - preview only

**How to use:**
1. Load job data (File → Import Job Data or Pull from GLE API)
2. Select account with configured template
3. Click "Preview Integration Data"
4. Review the transformed output

---

### ✅ 3. Generate PA Worksheets
**Menu: PA Template → Generate PA Worksheets**

- Processes all rows in your job data
- Creates Sub_{ID} worksheets for each job
- Groups by Sub_ID, Job_ID, or ID column
- Exports to Excel file (.xlsx)
- Option to open file immediately after generation

**How to use:**
1. Load job data
2. Select account
3. Ensure template is configured (will prompt if not)
4. Click "Generate PA Worksheets"
5. Choose save location
6. Optionally open the generated file

**Output:**
- One worksheet per Sub_ID
- Each worksheet in 2-column format
- Ready for ProjectA import

---

### ✅ 4. Kick Off Automation
**Menu: PA Template → Kick Off Automation**

- Automates ProjectA import process
- Uses CEVA's KickOff.py module
- Processes each worksheet pair sequentially
- Triggers TransPerfect Tools import

**Requirements:**
- Generated PA worksheets file must exist
- TransPerfect add-in must be installed in Excel
- VBA macros must be enabled

**How to use:**
1. Generate PA worksheets first
2. Click "Kick Off Automation"
3. Confirm the file to process
4. Follow on-screen prompts during automation
5. Wait for each job to complete import

**Process:**
1. Opens Excel file
2. Renames worksheets to "Integration" and "Charges Integration"
3. Triggers ProjectA import via macro/UI automation
4. Waits for completion
5. Deletes processed worksheets
6. Moves to next job

---

## Workflow Example

### Complete End-to-End Process:

1. **Select Account**
   - Configuration → Select Account → Choose "MyAccount"

2. **Load Data**
   - File → Import Job Data → Select Excel file
   - OR File → Pull from GLE API → Enter Job ID

3. **Configure Template** (First time only)
   - PA Template → Configure Template Mapper
   - Add mappings:
     ```
     PA Field: "Project Code"
     Mapping: Direct
     Source Column: "Project_Code"
     
     PA Field: "Job ID"
     Mapping: Direct
     Source Column: "Sub_ID"
     
     PA Field: "Client"
     Mapping: Static
     Static Value: "ACME Corp"
     
     ... (add more as needed)
     ```
   - Save template

4. **Preview** (Optional)
   - PA Template → Preview Integration Data
   - Review output format

5. **Generate Worksheets**
   - PA Template → Generate PA Worksheets
   - Save as: `PA_Import_MyAccount_20251210_143000.xlsx`
   - Open file to verify

6. **Run Automation** (Optional)
   - PA Template → Kick Off Automation
   - Confirm file to process
   - Wait for automation to complete

---

## Column Data Display Spacing
**✅ FIXED:** Reduced vertical spacing between column rows from 2px to 0px for tighter, more compact display.

---

## Technical Details

### File Locations
- **Template Mapper GUI:** `One_Stop_Shop/gui/pa_template_mapper_gui.py`
- **Template Storage:** `Core/pa_template_configs.json`
- **PA Template Manager:** `Core/pa_template_manager.py`
- **PA Template Processor:** `Core/pa_template_processor.py`
- **KickOff Automation:** `CEVA_Launcher/KickOff.py`

### Template Structure (JSON)
```json
{
  "MyAccount": {
    "template_name": "Integration Template",
    "description": "Standard PA import template",
    "key_column_name": "Field Name",
    "data_column_name": "Value",
    "mappings": [
      {
        "key": "Project Code",
        "source_column": "Project_Code",
        "mapping_type": "direct",
        "static_value": null,
        "formula": null,
        "format": null
      },
      ...
    ]
  }
}
```

### Mapping Types Explained

1. **Direct Mapping**
   - Copies value from source column as-is
   - Most common type
   - Example: Sub_ID → Job ID

2. **Static Mapping**
   - Uses a fixed value for all rows
   - Good for constants (e.g., Client name, Department)
   - Example: "ACME Corp" → End Client/Sponsor

3. **Calculated Mapping**
   - Applies formula or calculation
   - Can reference multiple columns
   - Example: Concatenate first + last name

4. **Concatenate Mapping**
   - Combines multiple column values
   - Specify separator
   - Example: City + ", " + State → Location

---

## Troubleshooting

### "No PA template configured for account"
- **Solution:** Use Configure Template Mapper to create one

### "Could not find Sub_ID or Job_ID column"
- **Solution:** Ensure your data has an ID column (Sub_ID, Job_ID, or ID)

### "Template Mapper shows empty columns list"
- **Solution:** Load job data first, then open Template Mapper

### "Kick Off Automation not working"
- **Check:** TransPerfect add-in installed in Excel
- **Check:** Macros enabled in Excel
- **Check:** Generated file exists and is not open

### "Preview shows wrong data"
- **Solution:** Preview uses first row only - verify your template with full generation

---

## Tips & Best Practices

1. **Test with small dataset first**
   - Load 1-2 jobs initially
   - Verify template produces correct output
   - Then process full dataset

2. **Use Preview before generating**
   - Quickly verify mappings are correct
   - Saves time vs generating full file

3. **Save templates incrementally**
   - Add a few mappings, save, test
   - Easier to debug than creating all at once

4. **Document your templates**
   - Use Description field in Template Settings
   - Note any special requirements

5. **Column naming matters**
   - Use exact column names from your data
   - Case-sensitive

6. **Excel worksheet limits**
   - Worksheet names max 31 characters
   - System auto-truncates if needed

---

## Future Enhancements (Roadmap)

- 📊 Charges worksheet generation (Sub_{ID}_Charges)
- 🔍 Template validation with warnings
- 📋 Template library with presets
- 🔄 Bulk template copy across accounts
- 📈 Advanced calculated fields with Python expressions
- 🎨 Custom formatting rules per field
- 📤 Export/Import template configurations
- 🧪 Test mode with sample data

---

## Support

For issues or questions:
1. Check this guide first
2. Review PA Template Manager/Processor code in Core/
3. Check console output for error messages
4. Test with minimal data to isolate issues

---

**Version:** 1.0  
**Date:** December 10, 2025  
**Status:** ✅ All 5 features implemented and tested
