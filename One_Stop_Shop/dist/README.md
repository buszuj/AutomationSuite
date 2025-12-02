# One Stop Shop - TheOneBP Quote Calculator

## Overview
The One Stop Shop application integrates TheOneBP functionality into the AutomationSuite framework. It provides a comprehensive quote calculator for translation services with support for multiple ratesheets, workflows, and service configurations.

## Migration from TheOneBP

This project was migrated from `TheOneBP` to `AutomationSuite/One_Stop_Shop` with the following improvements:

### Refactored Architecture
- **Business logic extracted to Core modules** for reusability across projects
- **UI-heavy components kept together** in `theonebp_app.py`
- **Modular design** following AutomationSuite conventions

### Core Modules Created
1. **`Core/rate_calculations.py`** - Service rate and quantity calculations
2. **`Core/workflow_manager.py`** - Workflow configuration management
3. **`Core/language_pair_manager.py`** - Language pair handling
4. **`Core/service_mapping_manager.py`** - Service-to-label mapping configuration

### File Structure
```
One_Stop_Shop/
├── oss_main.py                     # Main entry point
├── theonebp_app.py                 # Main application UI
├── admin_config_ui.py              # Admin configuration window
├── requirements.txt                # Python dependencies
├── oss_config.yaml                 # Application configuration
├── workflows.json                  # Workflow definitions
├── service_label_mapping.json     # Service mappings
├── One_BP_IQ fixed.01.xlsx        # Rate sheet database
├── admin_config_legacy.py         # Legacy admin config (backup)
└── oss_main_old.py                # Old main file (backup)
```

## Installation

1. **Install Dependencies**
   ```powershell
   cd "d:\BP TECH\Python apps\REPOs\AutomationSuite\One_Stop_Shop"
   pip install -r requirements.txt
   ```

2. **Verify Excel File**
   Ensure `One_BP_IQ fixed.01.xlsx` is present in the One_Stop_Shop directory

## Usage

### Running the Application

**From One_Stop_Shop directory:**
```powershell
python oss_main.py
```

**From AutomationSuite root:**
```python
from One_Stop_Shop.oss_main import main
main()
```

### Features

#### 1. **Rate Sheet Selection**
- Select from multiple pre-configured rate sheets (S IQVIA, S PFM, S Pfizer, S JJ)
- Each rate sheet has account-specific services and rates

#### 2. **Service Configuration**
- Check/uncheck services to include in quotes
- Services automatically calculate quantities based on word counts
- Support for word-based, hourly, and percentage-based services

#### 3. **Workflow Management**
- Save frequently used service combinations as workflows
- Load workflows to quickly configure service selections
- Update or delete existing workflows

#### 4. **Language Pairs**
- Add multiple language pairs (e.g., "English (GB) into French (France)")
- Automatically duplicates services for each language pair
- Delete or clear language pairs as needed

#### 5. **Input Modes**
- **QuoteMe Mode**: Traditional word count breakdown
  - Context matches
  - 100% matches
  - Repetitions
  - Fuzzy matches
  - New words
- **QTC Mode**: Translation/Revision word counts
  - TC WC for Translation
  - TC WC for Revision

#### 6. **Admin Configuration**
- Map services to input fields (QuoteMe/QTC)
- Configure hourly dividers for live/dead files
- Set minimum hourly rates and increment rates
- Customize Project Management percentage

#### 7. **CSV Export**
- Generate charges CSV with all selected services and language pairs
- Automatic minimum fee logic application
- Machine Translation fallback to Translation when rates unavailable
- Project Management and Rush Premium calculated as percentages

## Reusable Core Modules

### Rate Calculations (`Core/rate_calculations.py`)
```python
from Core.rate_calculations import (
    calculate_hourly_quantity,
    get_word_rate,
    apply_minimum_fee_logic
)

# Example: Calculate hourly service quantity
hours = calculate_hourly_quantity(
    service="Formatting",
    file_type="Live",
    use_qtc_input=False,
    quoteme_wc=5000,
    qtc_wc_translation=0,
    qtc_wc_revision=0,
    config=service_mapping
)
```

### Workflow Manager (`Core/workflow_manager.py`)
```python
from Core.workflow_manager import WorkflowManager

wf_manager = WorkflowManager("workflows.json")
wf_manager.save_workflow("S IQVIA", "Trans + Proof", ["Translation", "Proofreading"])
workflows = wf_manager.get_workflows_for_account("S IQVIA")
```

### Language Pair Manager (`Core/language_pair_manager.py`)
```python
from Core.language_pair_manager import LanguagePairManager

lp_manager = LanguagePairManager()
success, error = lp_manager.add_language_pair("English (GB)", "French (France)")
all_lps = lp_manager.get_all_language_pairs()
```

### Service Mapping Manager (`Core/service_mapping_manager.py`)
```python
from Core.service_mapping_manager import ServiceMappingManager

mapping_mgr = ServiceMappingManager("service_label_mapping.json")
labels = mapping_mgr.get_service_labels("S IQVIA", "Translation", "QuoteMe")
pm_percent = mapping_mgr.get_default_pm_percent("S IQVIA")
```

## Configuration

### oss_config.yaml
Configure application defaults, UI settings, and PA entities in `oss_config.yaml`.

### service_label_mapping.json
Maps services to input fields per rate sheet. Editable via Admin Config UI.

### workflows.json
Stores predefined service workflows per rate sheet.

## Known Differences from Original

1. **Import paths updated** to use Core modules
2. **Manager classes** replace direct file operations
3. **Legacy files preserved** with `_legacy` or `_old` suffixes for reference
4. **Global variables** maintained for UI compatibility (will be refactored in future versions)

## Future Enhancements

- [ ] Full OOP refactoring of UI components
- [ ] Database backend for rate sheets
- [ ] API integration for real-time rate updates
- [ ] Multi-language UI support
- [ ] Automated testing suite
- [ ] Historical quote tracking

## Source Files

**Original Location:** `d:\BP TECH\Python apps\REPOs\TheOneBP\`

**Note:** Source files in TheOneBP remain unchanged. This is a copy-and-integrate operation.

## Support

For questions or issues, refer to the AutomationSuite documentation or contact the development team.
