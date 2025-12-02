# TheOneBP to One_Stop_Shop Migration Summary

## Migration Completed Successfully ✓

**Date:** November 26, 2025  
**Source:** `d:\BP TECH\Python apps\REPOs\TheOneBP\`  
**Destination:** `d:\BP TECH\Python apps\REPOs\AutomationSuite\One_Stop_Shop\`

---

## Files Copied

### Configuration & Data Files
- ✓ `One_BP_IQ fixed.01.xlsx` - Rate sheet database
- ✓ `workflows.json` - Workflow definitions
- ✓ `service_label_mapping.json` - Service mappings

### Application Files (Refactored)
- ✓ `MainScript.py` → `theonebp_app.py`
- ✓ `AdminConfig.py` → `admin_config_ui.py` (refactored version)
- ✓ `admin_config_legacy.py` (original backup)

---

## Core Modules Created

### New Reusable Business Logic Modules

1. **`Core/rate_calculations.py`** (272 lines)
   - `get_service_type()` - Determine service type by UofM
   - `calculate_hourly_quantity()` - Calculate hourly service quantities
   - `get_word_rate()` - Retrieve word-based rates from ratesheet
   - `get_hourly_rate()` - Retrieve hourly rates from ratesheet
   - `apply_minimum_fee_logic()` - Apply min fee rules
   - `calculate_percentage_service_rate()` - Calculate PM/Rush Premium
   - `sanitize_csv_value()` - Clean values for CSV export

2. **`Core/workflow_manager.py`** (112 lines)
   - `WorkflowManager` class for managing workflows
   - Methods: load, save, delete, rename workflows
   - Per-account workflow storage

3. **`Core/language_pair_manager.py`** (118 lines)
   - `LanguagePairManager` class for LP management
   - Methods: add, remove, parse, get LPs
   - Validation and duplicate checking

4. **`Core/service_mapping_manager.py`** (119 lines)
   - `ServiceMappingManager` class for service mappings
   - Methods: load, save mappings per account
   - Get labels, PM percent, hourly rates

---

## Architecture Changes

### Before (TheOneBP)
```
TheOneBP/
├── MainScript.py (1560 lines - monolithic)
├── AdminConfig.py
├── workflows.json
├── service_label_mapping.json
└── One_BP_IQ fixed.01.xlsx
```

### After (One_Stop_Shop)
```
AutomationSuite/
├── One_Stop_Shop/
│   ├── oss_main.py              # Entry point (20 lines)
│   ├── theonebp_app.py          # UI logic (1560 lines)
│   ├── admin_config_ui.py       # Admin UI (300 lines)
│   ├── requirements.txt          # Dependencies
│   ├── oss_config.yaml          # Configuration
│   ├── README.md                # Documentation
│   ├── workflows.json
│   ├── service_label_mapping.json
│   └── One_BP_IQ fixed.01.xlsx
│
└── Core/
    ├── rate_calculations.py       # Business logic
    ├── workflow_manager.py        # Workflow management
    ├── language_pair_manager.py   # LP management
    └── service_mapping_manager.py # Mapping management
```

---

## Code Refactoring Summary

### Imports Updated
- Added Core module imports
- Added manager class instantiations
- Updated admin config import path

### Functions Replaced

| Original Function | New Approach |
|------------------|--------------|
| `load_workflows()` | `workflow_manager.load_workflows()` |
| `save_workflows_to_file()` | `workflow_manager.save_workflows()` |
| `load_service_label_mapping()` | `mapping_manager.get_mapping_for_account()` |
| Direct `LPs` list manipulation | `lp_manager` methods |
| Workflow file operations | `workflow_manager` methods |

### Manager Instances Created
```python
workflow_manager = WorkflowManager(...)
lp_manager = LanguagePairManager()
mapping_manager = ServiceMappingManager(...)
```

### Key Functions Updated
- `on_worksheet_change()` - Uses workflow_manager
- `save_workflow()` - Uses workflow_manager methods
- `delete_workflow()` - Uses workflow_manager.delete_workflow()
- `save_lp()` - Uses lp_manager.add_language_pair()
- `delete_lp()` - Uses lp_manager.remove_language_pair()
- `clean_all()` - Uses lp_manager.clear_all()
- `refresh_lp_listbox()` - Uses lp_manager.get_numbered_list()

---

## Configuration Files

### New: `requirements.txt`
```
customtkinter>=5.2.0
ttkthemes>=3.2.2
pandas>=2.0.0
openpyxl>=3.1.0
```

### Updated: `oss_config.yaml`
- Added `theonebp` section with settings
- Configured UI defaults
- Listed PA entities
- Updated export settings

---

## Legacy Files (Preserved)

- `admin_config_legacy.py` - Original AdminConfig.py
- `oss_main_old.py` - Original oss_main.py stub

---

## Next Steps

### Installation
```powershell
cd "d:\BP TECH\Python apps\REPOs\AutomationSuite\One_Stop_Shop"
pip install -r requirements.txt
```

### Testing
```powershell
python oss_main.py
```

### Verification Checklist
- [ ] Application launches successfully
- [ ] Rate sheets load correctly
- [ ] Services can be selected/deselected
- [ ] Workflows can be saved/loaded/deleted
- [ ] Language pairs can be added/removed
- [ ] Admin config opens and saves correctly
- [ ] CSV export generates correct output
- [ ] QuoteMe and QTC modes work
- [ ] Min fee logic applies correctly

---

## Benefits Achieved

### ✓ Separation of Concerns
- Business logic isolated in Core modules
- UI code kept together in theonebp_app.py
- Configuration externalized to YAML

### ✓ Reusability
- Core modules can be imported by other AutomationSuite projects
- Rate calculations available for API/CLI tools
- Workflow manager usable across applications

### ✓ Maintainability
- Smaller, focused modules easier to understand
- Clear separation between data and presentation
- Manager classes encapsulate related functionality

### ✓ Testability
- Core modules can be unit tested independently
- Business logic testable without UI
- Mock data easier to inject

### ✓ Documentation
- README.md provides comprehensive guide
- Inline docstrings in Core modules
- Configuration file self-documented

---

## Source Data Preservation

**Important:** All original files in `TheOneBP/` remain unchanged.  
This was a **copy and integrate** operation, not a move.

Source files preserved at:
`d:\BP TECH\Python apps\REPOs\TheOneBP\`

---

## Migration Statistics

- **Files copied:** 5
- **Core modules created:** 4
- **New files created:** 6
- **Lines of business logic extracted:** ~620
- **Manager classes created:** 3
- **Functions refactored:** 15+
- **Configuration files updated:** 1

---

## Questions & Clarifications Addressed

1. ✓ Excel file copied to One_Stop_Shop folder
2. ✓ Files renamed to follow AutomationSuite conventions
3. ✓ Integrated directly into One_Stop_Shop (not subdirectory)
4. ✓ Business logic extracted, UI kept together
5. ✓ Dependencies added to requirements.txt

---

## Contact & Support

For questions about the migration or usage:
- Review `One_Stop_Shop/README.md`
- Check Core module docstrings
- Refer to original TheOneBP files if needed

**Migration completed successfully! 🎉**
