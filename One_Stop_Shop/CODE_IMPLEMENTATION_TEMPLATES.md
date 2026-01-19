# Code Implementation Templates for Missing Modules

This document provides code templates for the critical missing functions identified in the gap analysis.

---

## 1. Rate Calculations Module

**File:** `Core/rate_calculations.py` (NEW - needs to be created)

```python
"""
Rate Calculations Module
Handles rate lookups, calculations, and validation for Charges CSV generation
"""

import pandas as pd
import logging
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# RATE LOOKUP FUNCTIONS (CRITICAL)
# ============================================================================

def get_word_rate(df_ratesheet: pd.DataFrame, 
                  source_lang: str, 
                  target_lang: str, 
                  service: str) -> Optional[float]:
    """
    Look up the word rate for a specific service and language pair.
    
    Args:
        df_ratesheet: DataFrame containing rate information (e.g., from "S IQVIA" sheet)
        source_lang: Source language display name (e.g., "English (GB)")
        target_lang: Target language display name (e.g., "German (Austria)")
        service: Service name (e.g., "Translation", "Machine Translation")
    
    Returns:
        float: Rate per word (e.g., 0.15)
        None: If rate not found or error occurs
    
    Raises:
        ValueError: If ratesheet structure is invalid
    
    Examples:
        >>> df = pd.read_excel("ratesheet.xlsx", sheet_name="S IQVIA")
        >>> rate = get_word_rate(df, "English (GB)", "German (Austria)", "Translation")
        >>> print(rate)
        0.15
        
        >>> # Machine Translation rate not available
        >>> rate = get_word_rate(df, "English (GB)", "Unknown Lang", "Translation")
        >>> print(rate)
        None
    
    Implementation Notes:
    ─────────────────────
    TODO: Verify ratesheet structure:
    1. What column contains service names? (e.g., "Service", "Service Type")
    2. What columns contain language pair rates? (e.g., "EN > DE_Translation", "EN-DE Translation")
    3. Are language codes or display names used? (e.g., "EN" vs "English (GB)")
    4. Are there separate columns for old/new rates?
    5. How are missing rates represented? (NaN, "", 0, N/A)
    
    Suggested Algorithm:
    ───────────────────
    1. Normalize language names to match ratesheet format
    2. Find column for this language pair + service combo
    3. Look for service row in first column or dedicated column
    4. Extract rate value
    5. Handle missing values gracefully
    6. Log lookup attempts for debugging
    """
    try:
        # IMPLEMENT ME:
        # 1. Normalize source_lang and target_lang to match column headers
        # 2. Find the rate column for this language pair
        # 3. Find the service row
        # 4. Return the rate value
        
        logger.debug(f"Looking up rate: {source_lang} > {target_lang} / {service}")
        
        # Placeholder: Return None until implemented
        logger.warning(f"Rate lookup not implemented for {service}")
        return None
        
    except Exception as e:
        logger.error(f"Error looking up word rate: {e}")
        return None


def get_hourly_rate(df_ratesheet: pd.DataFrame, 
                    service: str) -> Optional[float]:
    """
    Look up the hourly rate for a service (not language-pair specific).
    
    Hourly rates are typically the same across all language pairs,
    unlike word rates which vary by language pair.
    
    Args:
        df_ratesheet: DataFrame containing rate information
        service: Service name (e.g., "Formatting", "DTP", "Review")
    
    Returns:
        float: Rate per hour (e.g., 40.0)
        None: If rate not found
    
    Examples:
        >>> df = pd.read_excel("ratesheet.xlsx", sheet_name="S IQVIA")
        >>> rate = get_hourly_rate(df, "Formatting")
        >>> print(rate)
        40.0
        
        >>> rate = get_hourly_rate(df, "Unknown Service")
        >>> print(rate)
        None
    
    Implementation Notes:
    ─────────────────────
    TODO: Verify ratesheet structure:
    1. Is there a column like "Hourly Rate" or "Rate per Hour"?
    2. How are hourly rates distinguished from word rates?
    3. Are all services listed as rows, or are there separate columns per service?
    
    Suggested Algorithm:
    ───────────────────
    1. Find row matching service name
    2. Extract hourly rate column value
    3. Return rate or None
    """
    try:
        logger.debug(f"Looking up hourly rate for: {service}")
        
        # IMPLEMENT ME:
        # 1. Find the service row
        # 2. Extract the hourly rate column
        # 3. Return rate value
        
        logger.warning(f"Hourly rate lookup not implemented for {service}")
        return None
        
    except Exception as e:
        logger.error(f"Error looking up hourly rate: {e}")
        return None


# ============================================================================
# LANGUAGE NORMALIZATION (CRITICAL)
# ============================================================================

# Language code mapping - needs to be loaded from config or Excel
LANGUAGE_CODE_MAPPING = {
    # IMPLEMENT ME: Map all display names to ISO 639-1 codes
    # "English (GB)": "EN",
    # "German (Austria)": "DE",
    # "French (FR)": "FR",
    # ... etc
}


def load_language_mapping(excel_path: str = None) -> Dict[str, str]:
    """
    Load language code mapping from Excel or config file.
    
    Args:
        excel_path: Optional path to Excel file containing mapping
    
    Returns:
        Dictionary mapping display names to ISO codes
    
    Implementation Notes:
    ─────────────────────
    TODO: Determine where language mapping should be stored:
    1. In a dedicated Excel sheet?
    2. In a JSON config file?
    3. Hard-coded in this module?
    4. In oss_config.yaml?
    
    Should map:
    - "English (GB)" → "EN"
    - "German (Austria)" → "DE"
    - "French (FR)" → "FR"
    - etc.
    """
    try:
        if excel_path:
            # TODO: Read from Excel if needed
            pass
        
        # TODO: Load from JSON or other config
        logger.debug(f"Loaded {len(LANGUAGE_CODE_MAPPING)} language mappings")
        return LANGUAGE_CODE_MAPPING
        
    except Exception as e:
        logger.error(f"Error loading language mapping: {e}")
        return {}


def normalize_language_code(display_name: str) -> str:
    """
    Convert display name to ISO 639-1 language code.
    
    Args:
        display_name: Display name like "English (GB)" or "German (Austria)"
    
    Returns:
        str: ISO 639-1 code like "EN" or "DE"
        str: Original display_name if not found (fallback)
    
    Examples:
        >>> normalize_language_code("English (GB)")
        "EN"
        
        >>> normalize_language_code("German (Austria)")
        "DE"
        
        >>> normalize_language_code("Unknown Language")
        "Unknown Language"  # Fallback
    
    Implementation Notes:
    ─────────────────────
    This is critical for CSV export to ProjectA.
    ProjectA expects ISO 639-1 codes, not display names.
    """
    normalized = LANGUAGE_CODE_MAPPING.get(display_name, display_name)
    
    if normalized != display_name:
        logger.debug(f"Normalized language: {display_name} → {normalized}")
    else:
        logger.warning(f"Language code not found for: {display_name}")
    
    return normalized


# ============================================================================
# MINIMUM FEE LOGIC (COMPLEX)
# ============================================================================

def apply_minimum_fee_logic(service_rows: List[Dict], 
                           min_fee_rate: float) -> List[Dict]:
    """
    Apply minimum fee logic to service rows for a single language pair.
    
    The minimum fee rule states:
    - If the total cost of word-based services < min_fee, charge the min_fee instead
    - Applies only to primary word-based service (Translation or Machine Translation)
    - Back Translation is handled separately
    
    Args:
        service_rows: List of service dictionaries for one language pair
                     Each dict should have: service, quantity, rate, UofM
        min_fee_rate: Minimum fee threshold (e.g., 150.0)
    
    Returns:
        List of modified service dictionaries with min fee applied
    
    Algorithm:
    ──────────
    1. Find all word-based services (UofM == "Word")
    2. Exclude Back Translation from primary services
    3. Calculate: sumproduct_primary = SUM(qty * rate) for primary word services
    4. If sumproduct_primary < min_fee_rate:
       a. Find Translation or Machine Translation row
       b. Set that row's UofM = "Minimum"
       c. Set that row's Quantity = 1
       d. Set that row's Rate = min_fee_rate
       e. Set all other primary word services' Quantity to 0
    5. Handle Back Translation separately:
       a. Calculate: sumproduct_bt = qty * rate for Back Translation
       b. If sumproduct_bt < min_fee_rate:
          - Set BT UofM = "Minimum"
          - Set BT Quantity = 1
          - Set BT Rate = min_fee_rate
    6. Return modified service_rows
    
    Examples:
    ─────────
    # Scenario 1: Below minimum fee
    services = [
        {"service": "Translation", "quantity": 100, "rate": 0.50, "UofM": "Word"},
        {"service": "Formatting", "quantity": 2.0, "rate": 40.0, "UofM": "Hour"},
    ]
    # Sumproduct: 100 * 0.50 = 50 < min_fee (150)
    # Result: Translation becomes UofM="Minimum", qty=1, rate=150
    
    # Scenario 2: Above minimum fee
    services = [
        {"service": "Translation", "quantity": 2500, "rate": 0.15, "UofM": "Word"},
        {"service": "Formatting", "quantity": 4.0, "rate": 40.0, "UofM": "Hour"},
    ]
    # Sumproduct: 2500 * 0.15 = 375 > min_fee (150)
    # Result: Unchanged
    
    Implementation Notes:
    ─────────────────────
    IMPORTANT: After applying min fee, percentage services (PM, Rush Premium)
               must be recalculated based on updated word service rates!
    
    This function should be called BEFORE calculating PM/Rush Premium.
    """
    try:
        logger.debug(f"Applying min fee logic: min_fee={min_fee_rate}")
        
        # IMPLEMENT ME:
        # 1. Identify word-based services (Primary + Back Translation)
        # 2. Calculate sumproduct for primary services
        # 3. If below min fee, modify Translation/MT row
        # 4. Handle Back Translation separately
        # 5. Return modified rows
        
        # For now, return unchanged
        return service_rows
        
    except Exception as e:
        logger.error(f"Error applying minimum fee logic: {e}")
        return service_rows


# ============================================================================
# PERCENTAGE SERVICE CALCULATIONS
# ============================================================================

def calculate_project_management_rate(service_rows_above: List[Dict]) -> float:
    """
    Calculate Project Management rate as sum of all services above PM.
    
    PM Rate = SUM(quantity * rate) for all services positioned above PM
    
    Args:
        service_rows_above: List of service dicts above PM in order
    
    Returns:
        float: Calculated PM rate (rounded to 2 decimals)
    
    Examples:
        >>> services_above = [
        ...     {"quantity": 2500, "rate": 0.15},  # Translation
        ...     {"quantity": 4.0, "rate": 40.0},   # Formatting
        ... ]
        >>> calculate_project_management_rate(services_above)
        535.0
    """
    try:
        total = sum(
            float(row.get('quantity', 0)) * float(row.get('rate', 0))
            for row in service_rows_above
        )
        return round(total, 2)
    except Exception as e:
        logger.error(f"Error calculating PM rate: {e}")
        return 0.0


def calculate_rush_premium_rate(all_service_rows_up_to_self: List[Dict]) -> float:
    """
    Calculate Rush Premium rate as sum of ALL services up to and including RP itself.
    
    Rush Premium Rate = SUM(quantity * rate) for all services
    
    This allows Rush Premium to be a percentage of the entire quote.
    
    Args:
        all_service_rows_up_to_self: List of all service dicts up to RP
    
    Returns:
        float: Calculated RP rate (rounded to 2 decimals)
    
    Examples:
        >>> services = [
        ...     {"quantity": 2500, "rate": 0.15},  # Translation
        ...     {"quantity": 4.0, "rate": 40.0},   # Formatting
        ...     {"quantity": 0.02, "rate": 535.0}, # Project Management
        ... ]
        >>> calculate_rush_premium_rate(services)
        535.1  # Sum of all above
    """
    try:
        total = sum(
            float(row.get('quantity', 0)) * float(row.get('rate', 0))
            for row in all_service_rows_up_to_self
        )
        return round(total, 2)
    except Exception as e:
        logger.error(f"Error calculating Rush Premium rate: {e}")
        return 0.0


# ============================================================================
# VALIDATION & ERROR CHECKING
# ============================================================================

def validate_ratesheet_structure(df_ratesheet: pd.DataFrame) -> Tuple[bool, str]:
    """
    Validate that ratesheet has required columns and structure.
    
    Args:
        df_ratesheet: DataFrame from ratesheet Excel sheet
    
    Returns:
        Tuple of (is_valid: bool, message: str)
    
    Implementation Notes:
    ─────────────────────
    TODO: Define required columns:
    1. What column contains service names?
    2. Are there required language pair columns?
    3. What's the structure for different accounts?
    
    Should validate:
    - Service names column exists
    - Language pair columns exist (or can be built)
    - No completely empty rows
    - Numeric rate columns contain valid numbers
    """
    try:
        # IMPLEMENT ME: Validate structure
        logger.debug("Validating ratesheet structure...")
        
        if df_ratesheet.empty:
            return False, "Ratesheet is empty"
        
        # TODO: Add specific validation checks
        return True, "Ratesheet structure valid"
        
    except Exception as e:
        logger.error(f"Error validating ratesheet: {e}")
        return False, f"Validation error: {str(e)}"


def validate_language_pair_has_rates(source_lang: str, 
                                     target_lang: str, 
                                     services: List[str], 
                                     df_ratesheet: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that all services have rates for the given language pair.
    
    Args:
        source_lang: Source language display name
        target_lang: Target language display name
        services: List of service names to validate
        df_ratesheet: DataFrame containing rates
    
    Returns:
        Tuple of (all_have_rates: bool, services_without_rates: List[str])
    
    Examples:
        >>> has_rates, missing = validate_language_pair_has_rates(
        ...     "English (GB)", "German (Austria)", 
        ...     ["Translation", "Formatting"],
        ...     df_ratesheet
        ... )
        >>> if not has_rates:
        ...     print(f"Missing rates for: {missing}")
        ...     Missing rates for: ['Machine Translation']
    """
    try:
        services_without_rates = []
        
        # IMPLEMENT ME:
        # For each service:
        # 1. Check if rate exists in ratesheet
        # 2. If not, add to services_without_rates list
        
        all_have_rates = len(services_without_rates) == 0
        
        if not all_have_rates:
            logger.warning(f"Missing rates for {source_lang} > {target_lang}: {services_without_rates}")
        
        return all_have_rates, services_without_rates
        
    except Exception as e:
        logger.error(f"Error validating rates: {e}")
        return False, services


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_available_languages(df_ratesheet: pd.DataFrame) -> List[str]:
    """
    Extract available languages from ratesheet.
    
    Args:
        df_ratesheet: DataFrame containing rates
    
    Returns:
        List of language display names available in this ratesheet
    """
    # IMPLEMENT ME: Extract language list from ratesheet
    return []


def get_available_services(df_ratesheet: pd.DataFrame) -> List[str]:
    """
    Extract available services from ratesheet.
    
    Args:
        df_ratesheet: DataFrame containing rates
    
    Returns:
        List of service names available in this ratesheet
    """
    # IMPLEMENT ME: Extract service list from ratesheet
    return []


if __name__ == "__main__":
    # Test placeholder
    print("Rate Calculations Module")
    print("This module requires implementation based on ratesheet structure")
    print("\nMissing implementations:")
    print("- get_word_rate()")
    print("- get_hourly_rate()")
    print("- apply_minimum_fee_logic()")
    print("- validate_ratesheet_structure()")
```

---

## 2. Language Mapping Configuration

**File:** `Core/language_code_mapping.json` (NEW - needs to be created)

```json
{
  "language_mappings": {
    "English (GB)": "EN",
    "English (US)": "EN",
    "English": "EN",
    
    "German (Germany)": "DE",
    "German (Austria)": "DE",
    "German": "DE",
    
    "French (FR)": "FR",
    "French (Canada)": "FR",
    "French": "FR",
    
    "Spanish (Spain)": "ES",
    "Spanish (Mexico)": "ES",
    "Spanish": "ES",
    
    "Italian": "IT",
    
    "Portuguese (Brazil)": "PT",
    "Portuguese": "PT",
    
    "Dutch": "NL",
    
    "Japanese": "JA",
    
    "Chinese (Simplified)": "ZH",
    "Chinese (Traditional)": "ZH",
    "Chinese": "ZH",
    
    "Korean": "KO",
    
    "Russian": "RU",
    
    "Turkish": "TR",
    
    "Arabic": "AR",
    
    "Hindi": "HI",
    
    "Thai": "TH",
    
    "Vietnamese": "VI",
    
    "Polish": "PL",
    
    "Czech": "CS",
    
    "Hungarian": "HU",
    
    "Swedish": "SV",
    
    "Norwegian": "NO",
    
    "Danish": "DA",
    
    "Finnish": "FI",
    
    "Greek": "EL",
    
    "Hebrew": "HE",
    
    "Afrikaans": "AF",
    
    "Bulgarian": "BG",
    
    "Croatian": "HR",
    
    "Estonian": "ET",
    
    "Icelandic": "IS",
    
    "Indonesian": "ID",
    
    "Latvian": "LV",
    
    "Lithuanian": "LT",
    
    "Malay": "MS",
    
    "Maltese": "MT",
    
    "Romanian": "RO",
    
    "Serbian": "SR",
    
    "Slovak": "SK",
    
    "Slovenian": "SL",
    
    "Ukrainian": "UK"
  },
  
  "metadata": {
    "last_updated": "2026-01-13",
    "iso_standard": "ISO 639-1",
    "description": "Maps language display names to ISO 639-1 codes for ProjectA CSV export",
    "notes": "Add new mappings as needed for new language pairs"
  }
}
```

---

## 3. Enhanced Configuration

**File:** Update `oss_config.yaml`

```yaml
# One Stop Shop Configuration

# Ratesheet Configuration
ratesheet:
  default_file: "One_BP_IQ fixed.01.xlsx"
  
  # Structure description for each account worksheet
  accounts:
    IQVIA:
      sheet_name: "S IQVIA"
      language_pair_format: "source_target"  # How LP columns are named
      service_column: "Service"              # Column containing service names
      rate_columns_pattern: "{service}_Rate" # Pattern for finding rate columns
      
    # Add other accounts here
    # OTHER_ACCOUNT:
    #   sheet_name: "S Other Account"
    #   ...

# Language and Service Configuration
languages:
  mapping_file: "Core/language_code_mapping.json"
  
services:
  word_based:
    - "Translation"
    - "Machine Translation"
    - "Back Translation"
    - "TM - Fuzzy Match"
    - "TM - Exact Match"
  
  hourly_based:
    - "Formatting"
    - "Review"
    - "Proofreading"
    - "Desktop Publishing (DTP)"
    - "Editing"
    - "Reconciliation"
  
  percentage_based:
    - "Project Management"
    - "Rush Premium"

# Minimum Fee Configuration
minimum_fee:
  default_rate: 150.0
  applies_to:
    - "Translation"
    - "Machine Translation"
    - "Back Translation"
  
  # Excludes these services from min fee calculation
  exclude_from_sumproduct:
    - "Project Management"
    - "Rush Premium"

# Hourly Calculation Configuration
hourly_calculations:
  default_divider: 1000  # words per hour
  min_hourly_rate: 0.5   # minimum hours to charge
  increment_rate: 0.25   # rounding increment (0.25 = quarter hours)

# CSV Export Configuration
csv_export:
  encoding: "utf-8-sig"  # UTF-8 with BOM
  default_extension: ".csv"
  
  # Required column headers (order matters!)
  headers:
    - "Mark New Line Item"
    - "Line Item Description"
    - "Source"
    - "Target"
    - "Hide Unit Costs"
    - "Hide Details"
    - "Service Group 1"
    - "Service Group 2"
    - "Service Group 3"
    - "Service"
    - "UofM"
    - "Quantity"
    - "Rate"
    - "CommentsForInvoice"
    - "Technology Product"

# Logging Configuration
logging:
  level: "DEBUG"
  file: "one_stop_shop.log"
  format: "[%(asctime)s] %(levelname)s: %(message)s"
```

---

## 4. Unit Test Template

**File:** `tests/test_rate_calculations.py` (NEW - needs to be created)

```python
"""
Unit Tests for Rate Calculations Module

Tests cover:
- Rate lookups (word and hourly)
- Language normalization
- Minimum fee logic
- Percentage calculations
- Validation functions
"""

import unittest
import pandas as pd
from Core.rate_calculations import (
    get_word_rate,
    get_hourly_rate,
    normalize_language_code,
    apply_minimum_fee_logic,
    calculate_project_management_rate,
    calculate_rush_premium_rate,
    validate_ratesheet_structure,
    validate_language_pair_has_rates
)


class TestRateLookups(unittest.TestCase):
    """Test rate lookup functions"""
    
    @classmethod
    def setUpClass(cls):
        """Load test ratesheet"""
        # TODO: Create mock ratesheet or load from test file
        cls.df_ratesheet = pd.DataFrame()  # Placeholder
    
    def test_get_word_rate_existing_service(self):
        """Test getting word rate for existing service/LP"""
        # TODO: Implement test
        pass
    
    def test_get_word_rate_missing_service(self):
        """Test getting word rate for non-existent service"""
        # TODO: Implement test
        pass
    
    def test_get_word_rate_missing_lp(self):
        """Test getting word rate for non-existent language pair"""
        # TODO: Implement test
        pass
    
    def test_get_hourly_rate_existing_service(self):
        """Test getting hourly rate for existing service"""
        # TODO: Implement test
        pass
    
    def test_get_hourly_rate_missing_service(self):
        """Test getting hourly rate for non-existent service"""
        # TODO: Implement test
        pass


class TestLanguageNormalization(unittest.TestCase):
    """Test language code normalization"""
    
    def test_normalize_english_gb(self):
        """Test English (GB) normalizes to EN"""
        result = normalize_language_code("English (GB)")
        self.assertEqual(result, "EN")
    
    def test_normalize_german_austria(self):
        """Test German (Austria) normalizes to DE"""
        result = normalize_language_code("German (Austria)")
        self.assertEqual(result, "DE")
    
    def test_normalize_unknown_language(self):
        """Test unknown language returns as-is"""
        result = normalize_language_code("Unknown Language")
        self.assertEqual(result, "Unknown Language")
    
    def test_normalize_all_supported_languages(self):
        """Test all supported languages normalize correctly"""
        # TODO: Add all language pairs from ratesheet
        pass


class TestMinimumFeeLogic(unittest.TestCase):
    """Test minimum fee calculation and application"""
    
    def test_min_fee_below_threshold(self):
        """Test min fee applied when sumproduct < threshold"""
        services = [
            {"service": "Translation", "quantity": 100, "rate": 0.50, "UofM": "Word"},
            {"service": "Formatting", "quantity": 2.0, "rate": 40.0, "UofM": "Hour"},
        ]
        
        result = apply_minimum_fee_logic(services, min_fee_rate=150.0)
        
        # Find Translation row in result
        trans_row = next((r for r in result if r["service"] == "Translation"), None)
        
        # Verify min fee applied
        self.assertEqual(trans_row["UofM"], "Minimum")
        self.assertEqual(trans_row["quantity"], 1)
        self.assertEqual(trans_row["rate"], 150.0)
    
    def test_min_fee_above_threshold(self):
        """Test min fee NOT applied when sumproduct > threshold"""
        services = [
            {"service": "Translation", "quantity": 2500, "rate": 0.15, "UofM": "Word"},
            {"service": "Formatting", "quantity": 4.0, "rate": 40.0, "UofM": "Hour"},
        ]
        
        result = apply_minimum_fee_logic(services, min_fee_rate=150.0)
        
        # Find Translation row in result
        trans_row = next((r for r in result if r["service"] == "Translation"), None)
        
        # Verify min fee NOT applied
        self.assertEqual(trans_row["quantity"], 2500)
        self.assertEqual(trans_row["rate"], 0.15)
    
    def test_min_fee_back_translation_separate(self):
        """Test Back Translation handled separately from Translation"""
        # TODO: Implement test
        pass
    
    def test_min_fee_machine_translation_fallback(self):
        """Test min fee applied to MT when Translation unavailable"""
        # TODO: Implement test
        pass


class TestPercentageCalculations(unittest.TestCase):
    """Test Project Management and Rush Premium calculations"""
    
    def test_project_management_rate(self):
        """Test PM rate calculated as sum of services above"""
        services_above = [
            {"quantity": 2500, "rate": 0.15},  # Translation = 375
            {"quantity": 4.0, "rate": 40.0},    # Formatting = 160
        ]
        
        result = calculate_project_management_rate(services_above)
        self.assertEqual(result, 535.0)
    
    def test_rush_premium_rate(self):
        """Test RP rate calculated as sum of all services"""
        services = [
            {"quantity": 2500, "rate": 0.15},   # Translation = 375
            {"quantity": 4.0, "rate": 40.0},    # Formatting = 160
            {"quantity": 0.02, "rate": 535.0},  # PM = 10.7
        ]
        
        result = calculate_rush_premium_rate(services)
        expected = 375.0 + 160.0 + 10.7
        self.assertAlmostEqual(result, expected, places=1)
    
    def test_percentage_with_zero_services(self):
        """Test percentage calculation with empty service list"""
        result = calculate_project_management_rate([])
        self.assertEqual(result, 0.0)


class TestValidation(unittest.TestCase):
    """Test validation functions"""
    
    def test_validate_empty_ratesheet(self):
        """Test validation fails for empty ratesheet"""
        df = pd.DataFrame()
        is_valid, message = validate_ratesheet_structure(df)
        self.assertFalse(is_valid)
    
    def test_validate_language_pair_all_services_have_rates(self):
        """Test validation passes when all services have rates"""
        # TODO: Implement test
        pass
    
    def test_validate_language_pair_missing_rates(self):
        """Test validation identifies services without rates"""
        # TODO: Implement test
        pass


class TestEndToEnd(unittest.TestCase):
    """End-to-end integration tests"""
    
    def test_full_csv_generation_workflow(self):
        """Test complete workflow: input → process → CSV"""
        # TODO: Implement full integration test
        pass
    
    def test_multiple_language_pairs_minimum_fee(self):
        """Test min fee applied correctly across multiple LPs"""
        # TODO: Implement test
        pass
    
    def test_machine_translation_fallback_workflow(self):
        """Test MT fallback with min fee and percentage calculations"""
        # TODO: Implement test
        pass


if __name__ == '__main__':
    unittest.main()
```

---

## 5. Integration Point: Update `theonebp_app.py`

**Location:** Lines ~1120-1125 in `save_charges_csv()`

```python
# CURRENT (BROKEN):
rate = get_word_rate(df_s_iqvia, source_language, target_language, service)

# UPDATED (WITH ERROR HANDLING):
try:
    from Core.rate_calculations import (
        get_word_rate, 
        get_hourly_rate,
        normalize_language_code
    )
    
    # Determine if word-based or hourly
    UofM = Services_UofM.get(service, "")
    
    if UofM == "Word":
        rate = get_word_rate(df_s_iqvia, source_language, target_language, service)
    elif UofM == "Hour":
        rate = get_hourly_rate(df_s_iqvia, service)
    else:
        rate = None
    
    if rate is None:
        logger.warning(f"Rate not found for {service} ({source_language} > {target_language})")
        messagebox.showwarning(
            "Missing Rate",
            f"Rate not found for:\n"
            f"Service: {service}\n"
            f"Language Pair: {source_language} > {target_language}\n\n"
            f"Please verify the ratesheet configuration."
        )
        rate = 0  # Fallback
        
except ImportError as e:
    logger.error(f"Failed to import rate calculation functions: {e}")
    messagebox.showerror(
        "Import Error",
        f"Failed to load rate calculation module.\n"
        f"Please ensure Core/rate_calculations.py exists.\n\n"
        f"Error: {e}"
    )
    return
```

---

## Summary

These templates provide:
1. ✅ Complete rate_calculations.py module structure
2. ✅ Detailed algorithm descriptions
3. ✅ Language mapping configuration template
4. ✅ Enhanced oss_config.yaml with structure documentation
5. ✅ Comprehensive unit test template
6. ✅ Integration points in existing code

**Next Steps:**
1. Determine actual ratesheet column structure
2. Fill in "IMPLEMENT ME" sections
3. Test with real ratesheet data
4. Run unit tests to verify correctness
5. Update theonebp_app.py to import and use new functions

