# Charges CSV Generation - Visual Flow Diagram

## 🔄 Complete User Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    APPLICATION STARTUP                                 │
│  • Load Excel: "One_BP_IQ fixed.01.xlsx"                              │
│  • Initialize Managers (Workflow, LanguagePair, ServiceMapping)        │
│  • Read "Services per account" sheet                                   │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    STEP 1: USER CONFIGURATION                          │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ PA Entity:        [TPTNY ▼]                                     │  │
│  │ Rate Sheet:       [S IQVIA ▼]                                   │  │
│  │ File Type:        [Live ▼]                                      │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Trigger: on_worksheet_change()                                       │
│  └─> Reload Services, Languages, Workflows                            │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              STEP 2: SELECT SERVICES & INPUT MODE                      │
│                                                                         │
│  ┌─ Services Checkboxes ──────────────────────────────────────────┐   │
│  │ ☑ Translation          ☑ Formatting                            │   │
│  │ ☑ Machine Translation  ☑ Proofreading                          │   │
│  │ ☑ Back Translation     ☑ Project Management                    │   │
│  │ ☐ TM - Fuzzy Match     ☐ Rush Premium                          │   │
│  │ ☐ TM - Exact Match     ☐ Reconciliation                        │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─ Input Mode Toggle ────────────────────────────────────────────┐   │
│  │  ○ QuoteMe Mode          ● QTC Mode                            │   │
│  │  (Switches between word count input methods)                   │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Trigger: var.trace() on checkbox_state                               │
│  └─> Calls update_preview()                                           │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              STEP 3: ENTER WORD COUNTS (QuoteMe Mode)                   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Context:            [500        ]  ┐                          │  │
│  │  100%:               [100        ]  ├─ Auto sums to:           │  │
│  │  Repetitions:        [200        ]  │                          │  │
│  │  Fuzzy Matches:      [100        ]  ├─ TM Exact:     600 words │  │
│  │  New Words:          [2500       ]  │  TM Fuzzy:     300 words │  │
│  │  ─────────────────────────────────  │  New Words:   2500 words │  │
│  │  Total Words:        [3400] (RO)    ┘                          │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  OR (QTC Mode):                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  TC WC for TRANSLATION:   [5000      ]                         │  │
│  │  TC WC for REVISION:      [2000      ]                         │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Trigger: .bind("<KeyRelease>") on entries                            │
│  └─> Calls update_total_words() and update_preview()                  │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              STEP 4: PREVIEW ACTIVE SERVICES                           │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ Service              │  Quantity  │  UofM                      │  │
│  ├──────────────────────┼────────────┼──────────────────────────┤  │
│  │ Translation          │    2500    │  Word                    │  │
│  │ Machine Translation  │     600    │  Word  (MT used, not TM) │  │
│  │ Formatting           │    4.25    │  Hour  (calculated)      │  │
│  │ Proofreading         │    3.5     │  Hour  (calculated)      │  │
│  │ Project Management   │  (TBD)     │  %     (sum of above)    │  │
│  │ Rush Premium         │  (TBD)     │  %     (sum of all)      │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Function: update_preview()                                           │
│  • Reads selected services checkboxes                                 │
│  • Calculates quantities based on service type:                       │
│    - Word-based: sum of mapped QuoteMe/QTC fields                     │
│    - Hourly: wc / divider, rounded up                                │
│    - Percentage: calculated dynamically                              │
│  • Displays in grid format                                           │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              STEP 5: ADD LANGUAGE PAIRS                                │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Source Language:     [English (GB)    ▼]                      │  │
│  │  Target Language:     [German (Austria) ▼]                     │  │
│  │                       [Save LP] [Delete LP]                    │  │
│  │                       [Clear all INPUT]                        │  │
│  │                                                                 │  │
│  │  Language Pairs:                                               │  │
│  │  1. English (GB) into German (Austria)                         │  │
│  │  2. English (GB) into French (FR)                              │  │
│  │  3. English (GB) into Italian                                  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Functions: save_lp(), delete_lp()                                    │
│  • Stores in LanguagePairManager                                      │
│  • Can add multiple pairs                                            │
│  • Each pair will get separate charge rows                           │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              STEP 6: USER CLICKS "SAVE CHARGES CSV"                     │
│                                                                         │
│  Function: save_charges_csv()                                         │
│                                                                         │
│  ✓ Validate Inputs                                                    │
│    • Check LPs not empty                                              │
│    • Check services selected                                          │
│    • Warn if no LPs                                                   │
│                                                                         │
│  ✓ Read Ratesheet                                                     │
│    • Load df_s_iqvia from current worksheet                           │
│    • Verify language pair columns exist                               │
│                                                                         │
│  ✓ Prepare Word Counts Dictionary                                    │
│    • new_words: New Words field value                                │
│    • tm_exact: Context + 100% fields                                 │
│    • tm_fuzzy: Repetitions + Fuzzy Matches fields                    │
│                                                                         │
│  ✓ Build Rows for Each Language Pair                                 │
│    │                                                                  │
│    ├─> Determine Services for this LP                                │
│    │   • Check if MT rate exists                                     │
│    │   • If MT rate missing: FALLBACK to Translation                │
│    │   • Remove conflicting services                                 │
│    │                                                                  │
│    ├─> Get Quantities & Rates for Each Service                       │
│    │   • Word-based: quantity = word_counts[service_type]            │
│    │   • Hourly: quantity = calculated based on divider              │
│    │   • Rate: get_word_rate() or get_hourly_rate()                 │
│    │   ❌ GAP: These functions may not exist!                        │
│    │                                                                  │
│    ├─> Apply Minimum Fee Logic (PER LANGUAGE PAIR)                   │
│    │   • Calculate sumproduct for Translation/MT                     │
│    │   • If sumproduct < min_fee:                                    │
│    │     - Set Translation UofM = "Minimum"                          │
│    │     - Set Quantity = 1                                          │
│    │     - Set Rate = min_fee                                        │
│    │     - Zero other word services                                  │
│    │   • Do same for Back Translation                                │
│    │   ❌ GAP: Complex logic, needs refactoring/testing!             │
│    │                                                                  │
│    ├─> Calculate PM & Rush Premium (If Selected)                     │
│    │   • PM Rate = SUM(qty * rate) of services above PM              │
│    │   • Rush Premium = SUM(qty * rate) of all services             │
│    │   ❌ GAP: Recalculation after min fee not tested!              │
│    │                                                                  │
│    └─> Add Service Group Fields                                      │
│        • Service Group 1: from ServiceGroup1 dict                    │
│        • Service Group 2: from ServiceGroup2 dict                    │
│        • Service Group 3: (usually empty)                            │
│        ❌ GAP: May be missing for some services!                     │
│                                                                         │
│  ✓ Convert to DataFrame                                              │
│    • Create DataFrame with all rows                                  │
│    • Fill NaN with empty strings                                     │
│                                                                         │
│  ✓ Apply Min Fee Logic (PER LANGUAGE PAIR) - DATA VALIDATION         │
│    • Re-check per LP using DataFrame operations                      │
│    • Enforce minimum fee using mask/apply                            │
│                                                                         │
│  ✓ Show File Save Dialog                                             │
│    • User selects location & filename                                │
│    • Default extension: .csv                                         │
│                                                                         │
│  ✓ Export to CSV                                                      │
│    • df.to_csv(file_path, index=False, encoding='utf-8-sig')         │
│    • Show success message                                            │
│                                                                         │
│  ✓ Output Columns (in order):                                        │
│    1. Mark New Line Item (x for first service per LP)               │
│    2. Line Item Description (Source into Target)                    │
│    3. Source (ISO code) ❌ GAP: May be display name, not ISO!        │
│    4. Target (ISO code) ❌ GAP: May be display name, not ISO!        │
│    5. Hide Unit Costs (0)                                            │
│    6. Hide Details (0)                                               │
│    7. Service Group 1 ❌ GAP: May be empty/wrong!                    │
│    8. Service Group 2 ❌ GAP: May be empty/wrong!                    │
│    9. Service Group 3 (empty)                                        │
│   10. Service (service name)                                         │
│   11. UofM (Word/Hour/Minimum/%)                                     │
│   12. Quantity (calculated)                                          │
│   13. Rate ❌ GAP: May be None/0 if lookup fails!                    │
│   14. CommentsForInvoice (empty or sumproduct)                       │
│   15. Technology Product (empty)                                     │
│                                                                         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 📌 CRITICAL GAP LOCATIONS IN FLOW

```
  FILE: save_charges_csv() in theonebp_app.py [LINES 1087-1375]
  
  Line 1120: ❌ get_word_rate() - FUNCTION DOESN'T EXIST
             └─> Returns None → Quantity/Rate will be 0/None
  
  Line 1125: ❌ get_hourly_rate() - FUNCTION DOESN'T EXIST
             └─> Returns None → Hourly services won't work
  
  Line 1140-1160: ⚠️ MT Fallback Logic
                 └─> Doesn't handle None rates properly
                 └─> User warning not always shown
  
  Line 1220: Headers[2] Source - ❌ Display name, not ISO code
             Headers[3] Target - ❌ Display name, not ISO code
             └─> CSV won't match ProjectA format
  
  Line 1240-1250: ❌ Service Groups may be empty
                 └─> CSV columns blank/wrong
  
  Line 1280-1320: ⚠️ Minimum Fee Logic Complex
                 └─> No unit tests verify correctness
                 └─> Edge cases not documented
  
  Line 1360-1370: ⚠️ PM & Rush Premium Recalculation
                 └─> After min fee applied, doesn't recalculate
                 └─> May produce incorrect percentages
```

---

## 🔧 MISSING IMPLEMENTATION DETAIL

### Missing Module: `Core/rate_calculations.py`

**Current State:** ❌ Does not exist or is incomplete

**Needed Functions:**

```python
# ========================================
# RATE LOOKUPS (CRITICAL)
# ========================================

def get_word_rate(df_ratesheet, source_lang, target_lang, service):
    """
    Look up word rate from ratesheet
    
    Args:
        df_ratesheet: DataFrame of ratesheet (S_IQVIA, etc.)
        source_lang: Source language display name
        target_lang: Target language display name
        service: Service name (Translation, MT, etc.)
    
    Returns:
        float: Rate per word
        None: If not found
    
    Implementation Gap:
    - Need to know ratesheet column structure
    - Need to normalize language names to column headers
    - Need to find service row
    - Need to extract rate value
    
    Example pseudocode:
    ├─ Find row where Service = service_name
    ├─ Find column for language pair (EN > DE, etc.)
    ├─ Return cell value
    └─ If not found, return None
    """
    pass

def get_hourly_rate(df_ratesheet, service):
    """
    Look up hourly rate (not language-pair specific)
    
    Args:
        df_ratesheet: DataFrame of ratesheet
        service: Service name
    
    Returns:
        float: Rate per hour
        None: If not found
    
    Implementation Gap:
    - Hourly rates same across all language pairs
    - Need to find service row
    - Need to extract hourly rate column
    """
    pass

# ========================================
# LANGUAGE NORMALIZATION (CRITICAL)
# ========================================

def normalize_language_code(display_name):
    """
    Convert display names to ISO 639-1 codes
    
    Args:
        display_name: Display name like "English (GB)"
    
    Returns:
        str: ISO code like "EN"
    
    Implementation Gap:
    - Need mapping of display names to codes
    - Need to handle all language pairs used
    - Need to handle regional variants
    
    Example data needed:
    {
        "English (GB)": "EN",
        "English (US)": "EN",
        "German (Austria)": "DE",
        "German (Germany)": "DE",
        "French (FR)": "FR",
        ...
    }
    """
    pass

# ========================================
# MINIMUM FEE LOGIC (COMPLEX)
# ========================================

def apply_minimum_fee_logic(lp_rows, min_fee_rate):
    """
    Apply minimum fee to word-based services for a language pair
    
    Args:
        lp_rows: List of service rows for one LP
        min_fee_rate: Minimum fee threshold
    
    Returns:
        List of modified rows
    
    Algorithm Needed:
    1. Find all word-based services (excluding Back Translation)
    2. Calculate sumproduct = SUM(quantity * rate)
    3. If sumproduct < min_fee_rate:
       a. Find Translation or Machine Translation row
       b. Set UofM = "Minimum"
       c. Set Quantity = 1
       d. Set Rate = min_fee_rate
       e. Set all other word service quantities to 0
    4. Handle Back Translation separately
    5. DO NOT apply to hourly or percentage services
    6. Return modified rows
    
    Implementation Gap:
    - Complex state management
    - Multiple edge cases
    - No unit tests
    """
    pass

# ========================================
# VALIDATION (ERROR CHECKING)
# ========================================

def validate_ratesheet_structure(df_ratesheet):
    """
    Validate that ratesheet has required columns
    
    Implementation Gap:
    - Define required column patterns
    - Check language pair columns exist
    - Check service rows exist
    - Return helpful error messages
    """
    pass

def validate_language_pair_rates(source, target, services, df_ratesheet):
    """
    Check that all services have rates for this LP
    
    Implementation Gap:
    - Check each service has a rate
    - Return list of services without rates
    - Warn user of missing rates
    """
    pass
```

---

## 📊 Data Flow: Input to Output

```
USER INPUT (GUI)
├─ PA Entity: "TPTNY"
├─ Rate Sheet: "S IQVIA"
├─ File Type: "Live"
├─ Services: [Translation, Formatting, PM, Rush]
├─ Language Pairs: [EN into DE, EN into FR]
├─ QuoteMe Values:
│  ├─ New Words: 2500
│  ├─ TM Exact: 600
│  └─ TM Fuzzy: 300
└─ Settings:
   ├─ Min Fee: 150
   └─ Hourly Divider: 1000
         │
         ▼
PROCESSING LAYER (save_charges_csv)
├─ Validate inputs
├─ Load ratesheet "S IQVIA"
├─ For each Language Pair:
│  └─ For each Service:
│     ├─ Calculate Quantity
│     ├─ Get Rate via: ❌ get_word_rate() or get_hourly_rate()
│     ├─ Normalize Language: ❌ normalize_language_code()
│     ├─ Get Service Groups: ⚠️ From dicts (may be incomplete)
│     └─ Apply Min Fee: ⚠️ Complex logic (not tested)
├─ Build CSV rows
└─ Convert to DataFrame
         │
         ▼
OUTPUT (CSV FILE)
├─ Filename: User selected
├─ Format: UTF-8 with BOM
├─ Headers: 15 columns (see flow chart)
└─ Rows: Service rows for each LP
   ├─ Row 1: x | EN into DE | EN | ❌ DE | Translation | Word | 2500 | ❌ None | ...
   ├─ Row 2:   | EN into DE |    |      | Formatting | Hour | 4.25 | ❌ None | ...
   ├─ Row 3:   | EN into DE |    |      | PM | % | 0.02 | ❌ None | ...
   ├─ Row 4: x | EN into FR | EN | ❌ FR | Translation | Word | 2500 | ❌ None | ...
   └─ ...
   
   ❌ = Missing values / Not normalized
   ⚠️ = May be wrong
```

---

## ⚙️ Configuration Files Needed

```
Config Files Status:
├─ ✅ oss_config.yaml (exists, minimal)
├─ ✅ service_label_mapping.json (exists)
├─ ✅ workflows.json (exists)
├─ ✅ One_BP_IQ fixed.01.xlsx (exists)
│  ├─ "S IQVIA" (ratesheet) - structure needs documenting ❌
│  ├─ "S [Other Accounts]" (ratesheets) - structure needs documenting ❌
│  ├─ "Services per account" (config) - ✅
│  ├─ "UofM" (config) - ⚠️ Incomplete service mappings
│  └─ "Languages" (config) - needs ISO code mapping ❌
└─ ❌ language_code_mapping.json (NEEDS CREATION)
   └─ Should map display names to ISO 639-1 codes
```

---

## 🎯 Test Scenarios Needed

```
Priority 1 Tests:
1. test_get_word_rate_single_service
   Input: df_ratesheet, "EN", "DE", "Translation"
   Output: 0.15 (dollars per word)
   
2. test_get_word_rate_missing_lp
   Input: df_ratesheet, "EN", "UNKNOWN", "Translation"
   Output: None
   
3. test_normalize_language_all_variants
   Input: "English (GB)", "German (Austria)", "French (FR)"
   Output: "EN", "DE", "FR"
   
4. test_min_fee_below_threshold
   Input: Translation row with qty=100, rate=0.50 (sumproduct=50 < min_fee=150)
   Output: Translation qty=1, rate=150
   
5. test_min_fee_above_threshold
   Input: Translation row with qty=2500, rate=0.15 (sumproduct=375 > min_fee=150)
   Output: Translation qty=2500, rate=0.15 (unchanged)
   
6. test_pm_rate_sum_above
   Input: Services above PM sum to $500
   Output: PM rate = 500
   
7. test_rush_premium_sum_all
   Input: All services sum to $600
   Output: Rush Premium rate = 600
   
8. test_csv_export_format
   Input: Multiple LPs with multiple services
   Output: CSV file with correct headers and 15 columns

9. test_machine_translation_fallback
   Input: MT selected but no rate in ratesheet
   Output: Falls back to Translation service

10. test_end_to_end_full_workflow
    Input: All GUI inputs complete
    Output: Valid ProjectA-compatible CSV
```

---

## 📋 Implementation Order (Recommended)

```
WEEK 1:
├─ Day 1-2: Understand ratesheet structure
│           Document column names and formats
│
├─ Day 3-4: Create language_code_mapping.json
│           Implement normalize_language_code()
│           Test with all language pairs
│
└─ Day 5: Implement get_word_rate() and get_hourly_rate()
          Test with sample ratesheets

WEEK 2:
├─ Day 1-2: Fix MT fallback logic (handle None rates)
│
├─ Day 3-4: Refactor minimum fee logic into testable function
│           Add comprehensive comments
│
└─ Day 5: Create unit tests for all functions
          Run against real ratesheet data

WEEK 3:
├─ Day 1-2: Add error handling and validation
│
├─ Day 3-4: Document configuration format
│
└─ Day 5: End-to-end testing with real workflows
          Fix any issues found
```

