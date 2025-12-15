# PA Template System - Testing Guide

## Overview
This guide helps you test the newly created PA Template infrastructure step-by-step.

## What Was Built

### ✅ Completed Core Modules

1. **Core/charges_engine_ceva.py** - CEVA's original logic (preserved)
2. **Core/pa_template_manager.py** - Template configuration manager
3. **Core/pa_template_processor.py** - DataFrame to PA format processor
4. **Core/charges_engine.py** - Generic charges generator

## How to Test

### Step 1: Run the Test Suite

Open a terminal in the `Core` folder and run:

```powershell
python test_pa_template_system.py
```

**What this tests:**
- ✓ Creating and managing PA templates
- ✓ Processing DataFrames with templates
- ✓ Generating charges (Translation, TM, Formatting)
- ✓ Complete workflow simulation

**Expected output:**
- Console showing test progress
- 3-4 Excel files created in Core folder
- All tests should PASS

### Step 2: Verify Excel Outputs

After running tests, check these files in the `Core` folder:

#### 1. `test_pa_output.xlsx`
**Purpose:** Validates PA Template Processor output

**What to verify:**
- Multiple worksheets named `Sub_12345`, `Sub_12346`, `Sub_12347`
- Each worksheet has **2 columns**: "Field Name" | "Value"
- Field Name column contains keys like:
  - Project Code
  - Job ID
  - Language Pair
  - Word Count
  - Status
  - Total Cost (calculated)
- Value column contains actual data

**Example:**
```
| Field Name     | Value              |
|----------------|--------------------|
| Project Code   | HAB12345           |
| Job ID         | 12345              |
| Language Pair  | en-US > fr-FR      |
| Word Count     | 1500               |
| Status         | Ready for Import   |
| Total Cost     | $225.00            |
```

#### 2. `test_charges_output.xlsx`
**Purpose:** Validates Charges Engine output

**What to verify:**
- Worksheets named `Sub_12345_Charges`, `Sub_12346_Charges`
- Each worksheet has columns:
  - Project Code
  - Job ID
  - Service (Translation, TM-Fuzzy, TM-Exact, Formatting)
  - Language Pair
  - Quantity
  - Unit (words or hours)
  - Rate
  - Amount

**Example:**
```
| Service           | Quantity | Unit  | Rate  | Amount  |
|-------------------|----------|-------|-------|---------|
| Translation       | 1500     | words | 0.15  | 225.00  |
| TM-Fuzzy Match    | 200      | words | 0.08  | 16.00   |
| TM-Exact Match    | 100      | words | 0.05  | 5.00    |
| Formatting        | 0.5      | hours | 55.00 | 27.50   |
```

#### 3. `test_integration_output.xlsx`
**Purpose:** Validates complete workflow

**What to verify:**
- Has both `Sub_98765` (Integration) and `Sub_98765_Charges` worksheets
- This mimics CEVA's exact pattern: Sub_{ID} + Sub_{ID}_Charges
- Integration worksheet = 2-column format
- Charges worksheet = charges breakdown

**This is exactly what KickOff.py expects!**

### Step 3: Manual Template Testing (Optional)

Test creating a custom template for a new account:

```python
# In Python console or new script
from Core.pa_template_manager import PATemplateManager

manager = PATemplateManager()

# Create template for new account
manager.create_template(
    account_name="YOUR_ACCOUNT",
    template_name="Your Account Integration Template",
    key_column_name="Field Name",
    data_column_name="Value",
    mappings=[
        {
            "key": "Customer Name",
            "source_column": "Customer",
            "mapping_type": "direct",
            "static_value": None,
            "formula": None,
            "format": "text"
        },
        {
            "key": "Order Number",
            "source_column": "Order_ID",
            "mapping_type": "direct",
            "static_value": None,
            "formula": None,
            "format": "text"
        }
    ]
)

# Verify it was saved
template = manager.get_template("YOUR_ACCOUNT")
print(template)
```

**What to verify:**
- Template is saved to `Core/pa_template_configs.json`
- You can retrieve it with `get_template()`
- JSON file is human-readable

### Step 4: Check JSON Configuration

Open `Core/pa_template_configs.json` in a text editor.

**What to verify:**
- Contains "TEST_ACCOUNT" template
- Structure matches the 2-column format
- Mappings array has all configured fields
- You can manually edit this file if needed

**Example structure:**
```json
{
    "TEST_ACCOUNT": {
        "template_name": "Test Integration Template",
        "description": "Test template for validation",
        "key_column_name": "Field Name",
        "data_column_name": "Value",
        "mappings": [
            {
                "key": "Project Code",
                "source_column": "Project_Code",
                "mapping_type": "direct",
                "static_value": null,
                "formula": null,
                "format": "text"
            }
        ]
    }
}
```

## Understanding the Workflow

### CEVA's Pattern (Current)
1. main_orchestrator.py creates `Sub_12345` worksheet with merged data
2. ChargesIntegration.py creates `Sub_12345_Charges` worksheet
3. KickOff.py renames to "Integration" + "Charges Integration"
4. PA import happens
5. Worksheets deleted, next job processed

### OSS's Pattern (New, Configurable)
1. User uploads job data to OSS
2. OSS applies account-specific PA template → creates `Sub_12345` worksheet
3. OSS uses generic charges engine → creates `Sub_12345_Charges` worksheet
4. Same KickOff.py process for PA import
5. **But now works for ANY account, not just CEVA!**

## Common Issues & Solutions

### Issue: "No module named 'pa_template_manager'"
**Solution:** Make sure you're running from the Core directory, or add Core to PYTHONPATH:
```powershell
$env:PYTHONPATH = "d:\BP TECH\Python apps\REPOs\AutomationSuite\Core"
python test_pa_template_system.py
```

### Issue: "Permission denied" when creating Excel files
**Solution:** Close any open Excel files in the Core folder and retry.

### Issue: Test fails with "Template not found"
**Solution:** This is expected on first run. The test creates the template, then uses it.

### Issue: Charges amounts seem wrong
**Solution:** Default rates are used (0.15/word for translation). To use custom rates:
1. Create an Excel file with your rates
2. Load it with `engine.load_rates_from_excel("your_rates.xlsx")`

## Validation Checklist

Before proceeding to GUI development, verify:

- [ ] Test suite runs without errors
- [ ] All 4 test sections PASS
- [ ] Excel files are created in Core folder
- [ ] Integration worksheets have correct 2-column format
- [ ] Charges worksheets have proper charge breakdown
- [ ] Template JSON file is created and readable
- [ ] You understand mapping types: direct, static, calculated, concatenate
- [ ] You understand format types: text, number, date, currency

## Next Steps

Once all tests pass:

1. **Option A: Build GUI** → Create PA Template Mapper GUI for visual configuration
2. **Option B: Test with Real Data** → Try processing actual CEVA data through new system
3. **Option C: Create More Templates** → Add templates for other accounts

## Questions to Consider

Before building the GUI, think about:

1. **Which accounts need PA templates?** (CEVA already works, what others?)
2. **What data sources?** (Excel files, GLE API, manual entry?)
3. **Who configures templates?** (You, or end users via GUI?)
4. **Rate management?** (Single rates file, or per-account?)

## Getting Help

If tests fail or output looks wrong:
1. Check the console output for error messages
2. Verify file paths are correct
3. Check that pandas, openpyxl are installed
4. Review the test file comments for expected behavior

---

**Status:** Core infrastructure complete and ready for testing!
**Next:** Run test suite and verify outputs before GUI development.
