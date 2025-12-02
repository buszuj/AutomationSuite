# One Stop Shop - Post-Migration Testing Checklist

## Installation & Setup

- [ ] Install Python dependencies
  ```powershell
  cd "d:\BP TECH\Python apps\REPOs\AutomationSuite\One_Stop_Shop"
  pip install -r requirements.txt
  ```

- [ ] Verify Excel file exists
  - [ ] `One_BP_IQ fixed.01.xlsx` is in One_Stop_Shop directory
  - [ ] File contains required worksheets: "S IQVIA", "S PFM", etc.
  - [ ] "Services per account" sheet present
  - [ ] "UofM" sheet present

- [ ] Verify JSON files exist
  - [ ] `workflows.json` present
  - [ ] `service_label_mapping.json` present

---

## Application Launch

- [ ] Application launches without errors
  ```powershell
  python oss_main.py
  ```

- [ ] Main window displays correctly
  - [ ] Title: "The One-Stop Shop v.1.1"
  - [ ] Three-column layout visible
  - [ ] All UI elements render properly

---

## Rate Sheet Management

- [ ] Rate Sheet dropdown populated
  - [ ] "S IQVIA" available
  - [ ] "S PFM" available
  - [ ] Other rate sheets if present

- [ ] Switching rate sheets works
  - [ ] Services update correctly
  - [ ] Language pairs clear with confirmation
  - [ ] Workflows update for new sheet

---

## Service Selection

- [ ] Services checkboxes display
  - [ ] All account-specific services shown
  - [ ] Checkboxes functional
  - [ ] Services persist after operations

- [ ] Service preview updates
  - [ ] Selected services appear in preview
  - [ ] Quantities calculate correctly
  - [ ] UofM displays correctly

---

## Workflow Management

- [ ] Load existing workflow
  - [ ] Workflow list populates
  - [ ] Selecting workflow checks correct services
  - [ ] Preview updates after workflow load

- [ ] Save new workflow
  - [ ] Enter workflow name
  - [ ] Select services
  - [ ] Click "Save/Update Workflow"
  - [ ] Workflow appears in list
  - [ ] Workflow saved to `workflows.json`

- [ ] Update existing workflow
  - [ ] Select workflow from list
  - [ ] Modify services
  - [ ] Change workflow name (optional)
  - [ ] Click "Save/Update Workflow"
  - [ ] Changes reflected

- [ ] Delete workflow
  - [ ] Select workflow
  - [ ] Click "Delete Workflow"
  - [ ] Confirmation dialog appears
  - [ ] Workflow removed from list
  - [ ] File updated

---

## Language Pair Management

- [ ] Add language pair
  - [ ] Select source language
  - [ ] Select target language
  - [ ] Click "Save LP"
  - [ ] LP appears in list (numbered)

- [ ] Duplicate prevention
  - [ ] Try adding same LP twice
  - [ ] Error message appears

- [ ] Delete language pair
  - [ ] Select LP from list
  - [ ] Click "Delete LP"
  - [ ] LP removed

- [ ] Clear all input
  - [ ] Click "Clear all INPUT"
  - [ ] All LPs cleared
  - [ ] Word counts reset to 0

---

## Input Modes

### QuoteMe Mode (Default)

- [ ] QuoteMe fields visible
  - [ ] Context
  - [ ] 100%
  - [ ] Repetitions
  - [ ] Fuzzy Matches
  - [ ] New Words
  - [ ] Total Words (auto-calculated)

- [ ] Enter test values
  - [ ] Context: 100
  - [ ] 100%: 50
  - [ ] Repetitions: 200
  - [ ] Fuzzy Matches: 150
  - [ ] New Words: 2500

- [ ] Total Words calculates
  - [ ] Sum = 3000

- [ ] Preview updates
  - [ ] Translation quantity matches New Words
  - [ ] TM services show correct quantities

### QTC Mode

- [ ] Toggle to QTC mode
  - [ ] Click QTC Mode switch
  - [ ] Confirmation if QuoteMe has values

- [ ] QTC fields visible
  - [ ] TC WC for TRANSLATION
  - [ ] TC WC for REVISION

- [ ] Enter test values
  - [ ] Translation: 2500
  - [ ] Revision: 1000

- [ ] Preview updates
  - [ ] Quantities calculate based on QTC

- [ ] Switch back to QuoteMe
  - [ ] Confirmation if QTC has values
  - [ ] Fields clear correctly

---

## Admin Configuration

- [ ] Open Admin Config
  - [ ] Click "Admin Config" button
  - [ ] Window opens with rate sheet name in title

- [ ] Per Word Services Table
  - [ ] Word services displayed
  - [ ] QuoteMe columns present
  - [ ] QTC columns present
  - [ ] Checkboxes functional

- [ ] Map service to QuoteMe field
  - [ ] Check "Translation" → "New Words:"
  - [ ] Check "TM - Fuzzy Matches" → "Repetitions:" & "Fuzzy Matches:"
  - [ ] Check "TM - Exact Matches" → "Context:" & "100%:"

- [ ] Per Hour Services Table
  - [ ] Hour services displayed
  - [ ] Live/Dead dividers present
  - [ ] WC for Translation/Revision checkboxes

- [ ] Set hourly dividers
  - [ ] Formatting Live: 500
  - [ ] Formatting Dead: 1000
  - [ ] Review Live: 500
  - [ ] Review Dead: 1000

- [ ] Set global settings
  - [ ] Min hourly rate: 0.5
  - [ ] Increment rate: 0.25
  - [ ] Default PM %: 10

- [ ] Save configuration
  - [ ] Click "Save & Close"
  - [ ] Window closes
  - [ ] Changes saved to `service_label_mapping.json`
  - [ ] Preview updates with new mappings

---

## CSV Export

- [ ] Prepare test quote
  - [ ] Select services (Translation, TM, Formatting, PM, Rush)
  - [ ] Enter word counts
  - [ ] Add 2+ language pairs

- [ ] Export charges
  - [ ] Click "Save Charges CSV"
  - [ ] File save dialog appears
  - [ ] Choose location and filename
  - [ ] File saves successfully

- [ ] Verify CSV content
  - [ ] Open exported CSV
  - [ ] Headers present: Mark New Line Item, Line Item Description, Source, Target, Service, UofM, Quantity, Rate, etc.
  - [ ] One "x" marker per LP
  - [ ] Services duplicated for each LP
  - [ ] Quantities correct
  - [ ] Rates populated

- [ ] Minimum fee logic
  - [ ] Test with low word count (< min fee)
  - [ ] Translation shows "Minimum" UofM
  - [ ] Quantity = 1
  - [ ] Rate = Min Fee value
  - [ ] Other word services quantity = 0

- [ ] Project Management
  - [ ] PM rate = sum of services above
  - [ ] Quantity = PM % / 100

- [ ] Rush Premium
  - [ ] Rush rate = sum of all services including PM
  - [ ] Quantity = Rush % / 100

- [ ] Machine Translation fallback
  - [ ] Select MT service
  - [ ] For LP without MT rate
  - [ ] Warning message shown
  - [ ] Translation used instead

---

## File Type Selection

- [ ] File Type dropdown present
  - [ ] "Live" option
  - [ ] "Dead" option

- [ ] Live file calculations
  - [ ] Select "Live"
  - [ ] Hourly services use live divider
  - [ ] Quantities adjust accordingly

- [ ] Dead file calculations
  - [ ] Select "Dead"
  - [ ] Hourly services use dead divider
  - [ ] Quantities adjust accordingly

---

## PA Entity Selection

- [ ] PA Entity dropdown present
- [ ] All entities listed
  - [ ] TPTNY, TPTUK, TPTZA, etc.
- [ ] Selection persists
- [ ] (Note: Currently for reference, not affecting calculations)

---

## Core Module Integration

### Test Workflow Manager

```python
from Core.workflow_manager import WorkflowManager

wf_mgr = WorkflowManager("workflows.json")
```

- [ ] Load workflows
- [ ] Save workflow
- [ ] Delete workflow
- [ ] Get workflows for account

### Test Language Pair Manager

```python
from Core.language_pair_manager import LanguagePairManager

lp_mgr = LanguagePairManager()
```

- [ ] Add language pair
- [ ] Remove language pair
- [ ] Get all LPs
- [ ] Parse LP string

### Test Service Mapping Manager

```python
from Core.service_mapping_manager import ServiceMappingManager

map_mgr = ServiceMappingManager("service_label_mapping.json")
```

- [ ] Get mapping for account
- [ ] Save mapping
- [ ] Get service labels
- [ ] Get default PM percent

### Test Rate Calculations

```python
from Core.rate_calculations import (
    calculate_hourly_quantity,
    get_service_type,
    apply_minimum_fee_logic
)
```

- [ ] Calculate hourly quantity
- [ ] Get service type
- [ ] Apply min fee logic

---

## Error Handling

- [ ] Invalid inputs handled
  - [ ] Non-numeric word counts prevented
  - [ ] Empty workflow name rejected
  - [ ] Duplicate workflow name rejected
  - [ ] Invalid LP selection prevented

- [ ] Missing files handled
  - [ ] Excel file missing: error message
  - [ ] JSON files missing: creates new

- [ ] Edge cases
  - [ ] Zero word count
  - [ ] Very large word count
  - [ ] Empty service selection
  - [ ] No language pairs
  - [ ] Switch rate sheet with data

---

## Performance

- [ ] Application responsive
- [ ] Preview updates quickly
- [ ] CSV export fast for 10+ LPs
- [ ] No lag when switching rate sheets
- [ ] Admin config opens quickly

---

## Cleanup

- [ ] Test data removed
- [ ] Temporary files deleted
- [ ] Application closes cleanly
- [ ] No orphaned processes

---

## Documentation Review

- [ ] README.md complete
- [ ] Migration summary accurate
- [ ] Code comments present
- [ ] Docstrings in Core modules

---

## Issues Found

Document any issues here:

1. 
2. 
3. 

---

## Sign-off

- [ ] All critical tests passed
- [ ] Known issues documented
- [ ] Ready for production use

**Tested by:** _________________  
**Date:** _________________  
**Status:** ☐ Pass ☐ Fail ☐ Pass with notes
