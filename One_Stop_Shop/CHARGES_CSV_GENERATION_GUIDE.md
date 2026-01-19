# Charges CSV Generation - Step-by-Step Guide & Implementation Roadmap

## Overview
The One Stop Shop GUI enables users to generate a ProjectA-compatible Charges CSV file with quantities and rates based on selected services and language pairs. This guide outlines the current flow and identifies missing modules/code gaps.

---

## ✅ PART 1: CURRENT WORKFLOW (What Works)

### Step 1: Application Startup
**File:** `theonebp_app.py` (lines 1-150)

**Current Implementation:**
- Loads Excel ratesheet: `One_BP_IQ fixed.01.xlsx`
- Reads worksheets starting with "S " (e.g., "S IQVIA", "S Other Account")
- Initializes managers:
  - `WorkflowManager` - manages saved service combinations
  - `LanguagePairManager` - manages language pairs
  - `ServiceMappingManager` - maps services to QuoteMe/QTC fields

**Dependencies:**
- ✅ `Core.workflow_manager.WorkflowManager`
- ✅ `Core.language_pair_manager.LanguagePairManager`
- ✅ `Core.service_mapping_manager.ServiceMappingManager`
- ✅ `Core.rate_calculations` - rate lookup functions

---

### Step 2: User Selects Rate Sheet & Configuration
**File:** `theonebp_app.py` (lines 340-380)

**Current Implementation:**
```
┌─────────────────────────────────────────┐
│  Header Section                         │
├─────────────────────────────────────────┤
│  • PA Entity Dropdown     [TPTNY ▼]    │
│  • Rate Sheet Dropdown    [S IQVIA ▼] │
│  • File Type Dropdown     [Live ▼]    │
└─────────────────────────────────────────┘
```

**Triggers:**
- `on_worksheet_change()` → Reloads services, languages, workflows
- `populate_services_and_uom()` → Reads from "Services per account" sheet
- Services filtered by account name

---

### Step 3: User Selects Services (Workflow)
**File:** `theonebp_app.py` (lines 420-550)

**Current Implementation:**
- ✅ Service checkboxes displayed dynamically
- ✅ QuoteMe/QTC toggle switch (lines 900-1050)
- ✅ Preview grid updates in real-time
- ✅ Workflows can be saved/loaded

**Supported Services:**
- Word-based: Translation, Machine Translation, Back Translation, TM Services
- Hour-based: Formatting, Review, Proofreading, DTP
- Percentage: Project Management, Rush Premium

---

### Step 4: User Enters Word Counts
**File:** `theonebp_app.py` (lines 850-950)

**Current Implementation:**
```
┌─────────────────────────────────────────┐
│  QuoteMe Input Section                  │
├─────────────────────────────────────────┤
│  Context:           [500       ]       │
│  100%:              [100       ]       │
│  Repetitions:       [200       ]       │
│  Fuzzy Matches:     [100       ]       │
│  New Words:         [2500      ]       │
│  Total Words:       [3400] (auto)      │
└─────────────────────────────────────────┘
```

**Features:**
- ✅ Automatic "Total Words" calculation
- ✅ Validation: only numbers allowed
- ✅ Toggle to QTC mode for revision workflows

---

### Step 5: User Adds Language Pairs
**File:** `theonebp_app.py` (lines 1200-1350)

**Current Implementation:**
- ✅ Source & Target language dropdowns with autocomplete
- ✅ Language Pair Manager tracks all pairs
- ✅ Displayed as numbered list in Listbox

**Example:**
```
Language Pairs:
1. English (GB) into German (Austria)
2. English (GB) into French (FR)
```

---

### Step 6: User Triggers Preview Update
**File:** `theonebp_app.py` (lines 1000-1100)

**Current Implementation:**
- ✅ Real-time preview of active services
- ✅ Quantities calculated based on service type:
  - **Word-based**: Sum of mapped QuoteMe fields
  - **Hourly**: Calculated using file type + divider
  - **Percentage**: Dynamically computed

**Preview Grid:**
```
┌──────────────────┬──────────┬───────┐
│ Service          │ Quantity │ UofM  │
├──────────────────┼──────────┼───────┤
│ Translation      │ 2500     │ Word  │
│ Formatting       │ 4.25     │ Hour  │
│ Project Mgmt     │ 0.02     │ %     │
└──────────────────┴──────────┴───────┘
```

---

### Step 7: User Clicks "Save Charges CSV"
**File:** `theonebp_app.py` (lines 1087-1375)

**Current Implementation:**
- ✅ Validates language pairs & services
- ✅ Reads rates from ratesheet "S [Account]"
- ✅ Applies minimum fee logic per language pair
- ✅ Calculates Project Management rate (sum of services above)
- ✅ Calculates Rush Premium rate (sum of all services)
- ✅ Builds CSV with standard headers
- ✅ Opens file save dialog
- ✅ Exports to CSV with UTF-8 encoding

**CSV Headers:**
```
Mark New Line Item, Line Item Description, Source, Target, Hide Unit Costs,
Hide Details, Service Group 1, Service Group 2, Service Group 3, Service,
UofM, Quantity, Rate, CommentsForInvoice, Technology Product
```

---

## ⚠️ PART 2: MISSING MODULES & CODE GAPS

### **GAP #1: Missing Service Rate Lookups (CRITICAL)**
**Location:** `Core/rate_calculations.py`

**Current Status:** ❌ MISSING
- Only placeholders exist in `theonebp_app.py`
- Functions called but not properly implemented:
  - `get_word_rate()` - Returns rate for word-based services
  - `get_hourly_rate()` - Returns rate for hourly services
  - `apply_minimum_fee_logic()` - Applies min fee rules
  - `calculate_percentage_service_rate()` - Calculates PM & Rush Premium

**What's Needed:**
```python
def get_word_rate(df_ratesheet, source_lang, target_lang, service):
    """
    Look up word rate from ratesheet for a specific language pair + service
    
    Returns: float (rate per word or per hour)
    
    Implementation needed:
    1. Find source/target language columns in ratesheet
    2. Match service row
    3. Return rate value
    4. Handle missing rates gracefully
    """

def get_hourly_rate(df_ratesheet, service):
    """
    Look up hourly rate for a service (not LP-specific)
    
    Returns: float (rate per hour)
    """

def apply_minimum_fee_logic(word_service_rows, min_fee_rate):
    """
    Apply minimum fee to word-based services if sumproduct < min_fee
    
    Changes:
    - Sets UofM to "Minimum"
    - Sets Quantity to 1
    - Sets Rate to min_fee
    - Zeros other word services
    
    Returns: modified row data
    """
```

**Impact:** Without these, CSV export will have `None` or `0` rates

---

### **GAP #2: Language Code Normalization**
**Location:** `Core/language_normalization.py`

**Current Status:** ❌ MISSING
- Currently using display names: "English (GB)", "German (Austria)"
- CSV needs ISO 639-1 codes: "EN", "DE"

**What's Needed:**
```python
def normalize_language_code(language_display):
    """
    Convert display names to ISO codes
    
    Example:
    "English (GB)" → "EN"
    "German (Austria)" → "DE"
    "French (FR)" → "FR"
    
    Implementation:
    1. Read from Excel mapping sheet or config
    2. Return 2-letter ISO code
    3. Handle regional variants
    """
```

**Impact:** CSV won't match ProjectA import requirements

---

### **GAP #3: Service Group Mapping**
**Location:** Current partial implementation in `theonebp_app.py`

**Current Status:** ⚠️ PARTIALLY IMPLEMENTED
- Reads from Excel "UofM" sheet (lines 245-260)
- Stores in `ServiceGroup1`, `ServiceGroup2` dicts
- BUT: Not all services may have group assignments

**What's Needed:**
```python
# Ensure all services have proper group assignments:
ServiceGroup1 = {
    "Translation": "Language Services",
    "Machine Translation": "Language Services",
    "Formatting": "Language Services > Desktop Publishing",
    "Project Management": "Project Management",
    # ... etc
}

ServiceGroup2 = {
    "Translation": "",
    "Machine Translation": "",
    "Formatting": "Desktop Publishing",
    # ... etc
}
```

**Impact:** CSV Service Group columns may be empty/incorrect

---

### **GAP #4: Machine Translation Fallback Logic**
**Location:** `theonebp_app.py` (lines 1140-1160)

**Current Status:** ⚠️ IMPLEMENTED BUT NEEDS TESTING
- Checks if MT rate exists for LP
- Falls back to Translation if MT rate is 0
- Shows user warning

**Issues:**
- Logic only checks if `mt_rate > 0`
- Doesn't handle `None` or missing rates
- No test coverage

**Fix Needed:**
```python
mt_rate = get_word_rate(df_s_iqvia, source_language, target_language, "Machine Translation")
if mt_rate is None or mt_rate <= 0:  # <-- Changed logic
    # Fallback to Translation
    fallback_lps.append(lp)
```

---

### **GAP #5: CSV Header Validation**
**Location:** `theonebp_app.py` (line 230)

**Current Status:** ⚠️ HARDCODED
```python
Headers = [
    "Mark New Line Item", "Line Item Description", "Source", "Target", 
    "Hide Unit Costs", "Hide Details", "Service Group 1", "Service Group 2", 
    "Service Group 3", "Service", "UofM", "Quantity", "Rate", 
    "CommentsForInvoice", "Technology Product",
]
```

**Issues:**
- No validation that these match ratesheet
- No flexibility for different accounts
- "Technology Product" column always empty

**What's Needed:**
```python
def load_csv_headers_from_ratesheet():
    """
    Read expected CSV headers from ratesheet config
    Allow different headers per account/rate sheet
    """
```

---

### **GAP #6: Quantity Calculation for Percentage Services**
**Location:** `theonebp_app.py` (lines 1260-1290)

**Current Status:** ⚠️ PARTIALLY IMPLEMENTED
- Project Management: calculated as sum of services above
- Rush Premium: calculated as sum of all services + itself
- BUT: Logic is complex, hard to verify, no formula documentation

**Issues:**
- No comments explaining calculation
- No unit tests
- Edge cases not handled (e.g., what if only PM is selected?)

**What's Needed:**
```python
def calculate_project_management_rate(service_rows_above):
    """
    PM rate = SUM(Quantity * Rate) for all services above PM
    
    Ensures percentage-based services don't compound
    """
    total = sum(float(row['quantity']) * float(row['rate']) 
                for row in service_rows_above)
    return round(total, 2)

def calculate_rush_premium_rate(all_service_rows_up_to_self):
    """
    Rush Premium rate = SUM(Quantity * Rate) for all services including Rush Premium
    """
```

---

### **GAP #7: Minimum Fee Logic - Advanced Cases**
**Location:** `theonebp_app.py` (lines 1310-1360)

**Current Status:** ⚠️ PARTIALLY IMPLEMENTED
- Applies per language pair
- Handles Back Translation separately
- BUT: No handling for:
  - Multiple word-based services simultaneously
  - Machine Translation fallback + min fee interaction
  - Rush Premium with min fee applied

**What's Needed:**
```python
def apply_min_fee_per_lp(lp_rows, min_fee):
    """
    ALGORITHM:
    1. Calculate sumproduct for Translation/MT services (exclude Back Translation)
    2. If sumproduct < min_fee:
       a. Set Translation UofM = "Minimum"
       b. Set Translation Quantity = 1
       c. Set Translation Rate = min_fee
       d. Zero all other word-based services (except Back Translation)
    3. Calculate sumproduct for Back Translation separately
    4. Apply same logic if BT sumproduct < min_fee
    5. Recalculate PM/Rush Premium
    
    Returns: modified rows with min fee applied
    """
```

---

### **GAP #8: Error Handling & Validation**
**Location:** Various

**Current Status:** ❌ INCOMPLETE
- No validation that ratesheet columns exist
- No handling for missing language pair rates
- No checks for invalid service combinations

**What's Needed:**
```python
def validate_ratesheet_structure(df_ratesheet, account_name):
    """
    Validate that ratesheet has required columns:
    - Source language columns
    - Target language columns
    - Service rates
    
    Raises: ValueError with helpful message if structure invalid
    """

def validate_language_pair_has_rates(source, target, services, df_rates):
    """
    Check that all selected services have rates for this LP
    Returns: list of services without rates
    """
```

**Impact:** Silent failures, incorrect rates, undetected errors

---

### **GAP #9: Unit Tests**
**Location:** `tests/`

**Current Status:** ❌ NONE
- No unit tests for rate calculations
- No tests for CSV generation logic
- No tests for minimum fee logic
- No regression tests

**What's Needed:**
```python
# tests/test_charges_csv_generation.py

def test_word_rate_lookup():
    """Verify word rate lookup works for all services"""

def test_hourly_rate_calculation():
    """Verify hourly quantity calculation with dividers"""

def test_minimum_fee_application():
    """Verify min fee applied correctly per LP"""

def test_project_management_rate():
    """Verify PM rate = sum of services above"""

def test_rush_premium_rate():
    """Verify Rush Premium = sum all services"""

def test_csv_headers_correct():
    """Verify CSV output has all required headers"""

def test_machine_translation_fallback():
    """Verify MT fallback to Translation works"""
```

---

### **GAP #10: Documentation & Configuration**
**Location:** Various config files

**Current Status:** ⚠️ PARTIAL
- `oss_config.yaml` exists but minimal
- No documented mapping of service → rate sheet columns
- No documented field mappings for accounts

**What's Needed:**
```yaml
# oss_config.yaml - Enhanced version
rate_sheet_config:
  S IQVIA:
    language_column_prefix: "Language Pair"
    service_column_pattern: "{service}_Rate"
    services:
      - name: "Translation"
        column_name: "Translation_Rate"
        uom: "Word"
        group1: "Language Services"
      - name: "Machine Translation"
        column_name: "MT_Rate"
        uom: "Word"
        group1: "Language Services"

language_code_mapping:
  "English (GB)": "EN"
  "German (Austria)": "DE"
  "French (FR)": "FR"

minimum_fee_rate: 150
default_hourly_divider: 1000
```

---

## 📋 PART 3: IMPLEMENTATION ROADMAP

### **Priority 1: Critical (Blocks CSV Generation)**

#### 1.1 Implement Rate Lookup Functions
**File:** Create `Core/rate_calculations.py`
```python
def get_word_rate(df_ratesheet, source_lang, target_lang, service):
    # Implementation
    pass

def get_hourly_rate(df_ratesheet, service):
    # Implementation
    pass
```

**Time:** 2-3 hours
**Blocking:** Can't export CSV without rates

---

#### 1.2 Implement Language Code Normalization
**File:** Create `Core/language_normalization.py`
```python
def normalize_language_code(display_name):
    # Map display names to ISO codes
    pass
```

**Time:** 1-2 hours
**Blocking:** CSV won't match ProjectA import

---

#### 1.3 Fix Machine Translation Fallback
**File:** Update `theonebp_app.py` (lines 1140-1160)
- Handle `None` rates
- Add comprehensive logging

**Time:** 1 hour
**Risk:** Users may see incorrect rates without this

---

### **Priority 2: High (Improves Quality)**

#### 2.1 Implement Minimum Fee Logic Validation
**File:** Update `theonebp_app.py` (lines 1310-1360)
- Add detailed algorithm comments
- Handle edge cases
- Recalculate PM/Rush Premium after min fee

**Time:** 3-4 hours
**Impact:** Users get correct min fee behavior

---

#### 2.2 Add Service Group Validation
**File:** Update `populate_services_and_uom()`
- Verify all services have group assignments
- Default to "Language Services" if missing
- Log warnings for incomplete mappings

**Time:** 1-2 hours
**Impact:** CSV Service Group columns always populated

---

#### 2.3 Create Unit Tests
**File:** Create `tests/test_charges_csv_generation.py`
- Test each calculation function
- Test CSV output format
- Test edge cases (min fee, fallback, etc.)

**Time:** 4-5 hours
**Impact:** Confidence in correctness, catch regressions

---

### **Priority 3: Medium (Enhances Robustness)**

#### 3.1 Add Comprehensive Error Handling
**File:** Update `theonebp_app.py` and rate calculation functions
- Validate ratesheet structure
- Check for missing rates
- Provide helpful error messages

**Time:** 3 hours
**Impact:** Users know what went wrong, not silent failures

---

#### 3.2 Document Configuration Format
**File:** Create `OSS_CONFIGURATION.md`
- Document ratesheet expected structure
- Document language code mapping
- Document service definitions

**Time:** 2 hours
**Impact:** Others can configure new accounts

---

#### 3.3 Add Logging
**File:** Add logging throughout `theonebp_app.py` and calculations
- Log rate lookups
- Log min fee applications
- Log fallback decisions

**Time:** 2 hours
**Impact:** Debugging easier, audit trail available

---

### **Priority 4: Low (Nice to Have)**

#### 4.1 Add CSV Preview Dialog
- Show CSV data before save
- Allow editing rates manually
- Validate before export

**Time:** 5 hours

---

#### 4.2 Add Batch Import Feature
- Import multiple quote jobs
- Generate CSV for each
- Zip and export

**Time:** 8 hours

---

## 📊 PART 4: CODE GAP CHECKLIST

| # | Component | Current | Needed | Priority | Est. Hrs |
|---|-----------|---------|--------|----------|----------|
| 1 | Word Rate Lookup | ❌ | `get_word_rate()` | P1 | 2 |
| 2 | Hourly Rate Lookup | ❌ | `get_hourly_rate()` | P1 | 2 |
| 3 | Language Normalization | ❌ | Mapping function | P1 | 1 |
| 4 | Min Fee Logic | ⚠️ | Enhanced version | P2 | 3 |
| 5 | Service Groups | ⚠️ | Validation | P2 | 1 |
| 6 | MT Fallback | ⚠️ | Fix None handling | P1 | 1 |
| 7 | CSV Headers | ⚠️ | Dynamic loading | P2 | 2 |
| 8 | Error Handling | ⚠️ | Comprehensive | P3 | 3 |
| 9 | Unit Tests | ❌ | Full suite | P2 | 5 |
| 10 | Documentation | ⚠️ | Config guide | P3 | 2 |
| **TOTAL** | | | | | **22 hrs** |

---

## 🚀 QUICK START: Next Steps

### **Immediate (Today):**
1. ✅ Read this guide
2. ✅ Identify which ratesheet columns contain rates
3. ✅ Map language display names to ISO codes
4. ✅ Document current rate sheet structure

### **This Week:**
1. Implement `get_word_rate()` and `get_hourly_rate()`
2. Implement language normalization
3. Test CSV export with real data
4. Fix any rate lookup issues

### **Next Week:**
1. Implement comprehensive min fee logic
2. Create unit tests
3. Add error handling
4. Document configuration

---

## 📝 RELATED FILES

- **Main GUI:** [theonebp_app.py](theonebp_app.py)
- **Ratesheet:** `One_BP_IQ fixed.01.xlsx`
- **Core Modules:** `Core/rate_calculations.py` (needs creation)
- **Core Modules:** `Core/language_pair_manager.py`
- **Core Modules:** `Core/service_mapping_manager.py`
- **Core Modules:** `Core/workflow_manager.py`
- **Existing Charges Engine:** `Core/charges_engine_ceva.py` (reference)

---

## ✅ CURRENT VALIDATION CHECKLIST

Before proceeding with Priority 1 tasks:

- [ ] Ratesheet column structure documented
- [ ] Language code mapping available
- [ ] Service definitions complete
- [ ] Expected CSV format confirmed with ProjectA team
- [ ] Test data available for validation
- [ ] Rate sheet access verified (no permissions issues)
