import pandas as pd
from shared_data import get_wc_df, get_ceva_df, print_debug
import copy
import os
import math

# Rate storage for ISO language codes (loaded from Excel file)
RATES_DATA = {
    "MTPT": {},         # Will be populated from CEVA RATES.xlsx
    "Translation": {},  # Will be populated from CEVA RATES.xlsx
    "TM_Fuzzy": {},     # Fuzzy Match rates from "Fuzzy" and "Fuzzy - new" columns
    "TM_Exact": {}      # Exact Match rates from "Gold" and "Gold - new" columns
}

# Legacy rate storage (kept for compatibility)
LANGUAGE_PAIR_RATES = {
    # Will be populated from Excel file
    # Format: "source-target": {
    #     "old_rates": {"mtpt": rate, "translation": rate, "formatting": rate, "pd_maintenance": rate},
    #     "new_rates": {"translation": rate, "formatting": rate, "pd_maintenance": rate}
    # }
}
project_codes = [
    "65286",
    "169577",
    "3030037",
    "4216001",
    "2791343-GB-EVIDENCE PLATFORM PLANNING",
    "4020-01-001",
    "67953964MDD3002",
    "AMBER",
    "AMBER 213348",
    "AP11343",
    "AP11344",
    "AZA39508",
    "AZA39875",
    "AZA39877",
    "AZA41404",
    "AZAA1404",
    "B7981105",
    "BII23KOR",
    "BXA25285",
    "BXA26220",
    "BYA72263",
    "C4601003",
    "CXA27107",
    "CZA54600",
    "CZA61173",
    "CZA62190",
    "DYA76629",
    "DYAA3080",
    "EZA77492",
    "EZA78483",
    "EZA78753",
    "EZA79180",
    "FYA01036",
    "FZA87997",
    "GAZ99457",
    "GZA02743",
    "GZA96048",
    "GZA99269",
    "GZA99457",
    "GZA99494",
    "GZA99779",
    "HAB05282",
    "HAB10547",
    "HAB11892",
    "HAB23872",
    "HAB23914",
    "HAB25986",
    "HAB26285",
    "HAB30957",
    "HAB36455",
    "HAB37153",
    "HAB39821",
    "HAB40679",
    "HAB40679 / HAB40680 / HAB41081",
    "HAB40680",
    "HAB40680/ HAB41081",
    "HAB40681",
    "HAB41081",
    "HAB49536",
    "HAB61119",
    "HAB63455",
    "HAB65663",
    "HAB65776",
    "HAB67279",
    "HAB74193, HAB74194",
    "HAB78209",
    "HAB79885",
    "HAB81715",
    "HAB85640",
    "HAB88350",
    "HAB88477",
    "HAB90121",
    "HAB92403",
    "HAB95731",
    "HAB98842",
    "HABA5669",
    "HXA33839",
    "HXA33937",
    "HZA04167",
    "HZA09745",
    "HZA12816",
    "IAB01838",
    "IAB05272",
    "IAB06343",
    "IAB06994",
    "IAB16854",
    "IAB16906",
    "IAB16907",
    "IAB16929",
    "IAB23127",
    "IAB23127",
    "IAB23705",
    "IAB25078",
    "IAB25957",
    "IAB25982",
    "IAB26472",
    "IAB27809",
    "IAB29444",
    "IAB39815",
    "IAB45115",
    "IAB67904",
    "IAB76572",
    "IAB85704",
    "IAB88662",
    "IAB92608",
    "IABA3885",
    "IXA34985",
    "IXA35035",
    "IXAA4985",
    "IYA05655",
    "IZA14272",
    "J2G-MC-JZJX",
    "JAB12424",
    "JAB13240",
    "JAB22744",
    "JAB26866",
    "JAB30724",
    "JAB37584",
    "JAB39616",
    "JAB48306",
    "JAB50176",
    "JAB50178",
    "JAB54058",
    "JAB59964",
    "JAB63124",
    "JAB72754",
    "JAB80466",
    "JAB84012",
    "JAB86398",
    "JAB89206",
    "JAB93024",
    "JAB95430",
    "JYA08718",
    "JZA23878",
    "KAB18478",
    "KAB20992",
    "KAB28042",
    "KAB31714",
    "KAB32802",
    "KAB32808",
    "KAB32826",
    "KAB32826 AND KAB32808",
    "KAB36324",
    "KAB42028",
    "KAB53520",
    "KAB54162",
    "KAB56286",
    "KAB61292",
    "KAB62352",
    "KAB64072",
    "KAB64840",
    "KAB83228",
    "KAB97216",
    "KZA37618",
    "KZA43524",
    "KZA43696",
    "LAB09747",
    "LAB09783",
    "LAB15459",
    "LAB26829",
    "LAB44941",
    "LAB50945",
    "LAB52789",
    "LAB54827",
    "LAB59041",
    "LZA44303",
    "LZA47295",
    "LZA51611",
    "LZA51653",
    "MAB05943",
    "MAB07707",
    "MAB11979",
    "MAB24607",
    "MAB24721",
    "MAB5068",
    "MAB50683",
    "MAB59779",
    "MAB62057",
    "MAB66599",
    "MAB79477",
    "MZA55294",
    "MZA58497",
    "MZA58512",
    "NYA13501",
    "NZA67186",
    "NZA71096",
    "NZA71230",
    "OAB17141",
    "OAB36781",
    "OAB59739",
    "OS005271",
    "OWA02749",
    "OXA7058",
    "OXAA7058",
    "OYA16591",
    "OYA16888",
    "OYA17016",
    "OYA17266",
    "OZA74666",
    "PAB22280",
    "PNA57616",
    "PYA18007",
    "PZA83598",
    "PZA84215",
    "PZA87294",
    "PZA88513",
    "QWA05532",
    "QYA19796",
    "QZA95985",
    "QZAA1905",
    "RYA21028",
    "RYA21148",
    "RYA21529",
    "RYA21921",
    "RZA03966",
    "RZA05954",
    "RZA06490",
    "RZA10313",
    "RZA10708",
    "RZA14385",
    "RZA14831",
    "RZA17212",
    "RZA19459",
    "RZA24912",
    "RZA25912",
    "RZA26859",
    "RZA31939",
    "RZA31943",
    "RZA38718",
    "RZA40733",
    "RZA42947",
    "RZA44373",
    "RZA45357",
    "RZA45837",
    "RZA48078",
    "RZA48904",
    "RZA49555",
    "RZA51198",
    "RZA51207",
    "RZA52623",
    "RZA98192",
    "RZA98806",
    "RZA99004",
    "RZA99162",
    "S2358",
    "S2444",
    "SP5535",
    "SP5885",
    "STUDY CODE: ZZA85563",
    "SYA22199",
    "SYA22748",
    "SYA23489",
    "SYAA2227",
    "SZA5415",
    "SZA55405",
    "SZA55415",
    "SZA55415 | SZA55405",
    "SZA55415; SZA55405; GZA02743",
    "SZA554515",
    "SZA61259",
    "SZA63669",
    "SZA64400",
    "SZA64428",
    "TSR-042",
    "TYA24529",
    "TYA24558",
    "TYAA4426",
    "TZA67647",
    "TZA74011",
    "Unknown",
    "UVA97934",
    "UWAB4331",
    "UXA25557",
    "UXAA9108",
    "UYA25465",
    "UYA26121",
    "UZA76946",
    "UZA81741",
    "UZA82362",
    "VUA93412",
    "VWA16263",
    "VWA16264",
    "VZA84555",
    "VZA84660",
    "VZA88552",
    "VZA89574",
    "WYA33146",
    "WYA34098",
    "WZA95950",
    "WZA99661",
    "YXA41522",
    "YXAA0683",
    "YYA36217",
    "YYA36809",
    "YYA36819",
    "YYA37251",
    "YZA01090",
    "ZHA33821",
    "ZWA21957",
    "ZXA51494",
    "ZYA38035",
    "ZYAA7901",
    "ZZA05392",
    "ZZA06563",
    "ZZA09430",
    "ZZA09481",
    "ZZA09940",
    "ZZA15738",
    "ZZA19828",
    "ZZA20064",
    "ZZA23502",
    "ZZA34165",
    "ZZA35785",
    "ZZA36889",
    "ZZA36890",
    "ZZA36891",
    "ZZA41590",
    "ZZA45998",
    "ZZA46315",
    "ZZA46362",
    "ZZA46364",
    "ZZA50049",
    "ZZA51592",
    "ZZA52729",
    "ZZA54279",
    "ZZA56756",
    "ZZA57119",
    "ZZA57120",
    "ZZA58219",
    "ZZA60521",
    "ZZA62490",
    "ZZA64115",
    "ZZA76518",
    "ZZA78263",
    "ZZA85238",
    "ZZA85563",
    "ZZA92567",
    "ZZA92873",
    "ZZA95588"
]

# Charges template structure
CHARGES_TEMPLATE = {
    "Mark New Line Item": "",
    "Line Item Description": "",
    "Source": "",
    "Target": "",
    "Hide Unit Costs": 0,
    "Hide Details": 0,
    "Service Group 1": "",
    "Service Group 2": "",
    "Service Group 3": "",
    "Service": "",
    "UofM": "",
    "Quantity": "",
    "Rate": "",
    "CommentsForInvoice": "",
    "Technology Product": "GL PD"
}

def load_rates_from_excel(excel_file_path=None):
    """Load rates from Excel file with ISO language codes"""
    if not excel_file_path:
        # Default path in app folder - use CEVA RATES.xlsx
        excel_file_path = os.path.join(os.path.dirname(__file__), "CEVA RATES.xlsx")
    
    if not os.path.exists(excel_file_path):
        print_debug(f"Rates Excel file not found: {excel_file_path}")
        return False
    
    try:
        # Read the Excel file (MSA Pricing sheet)
        df = pd.read_excel(excel_file_path, sheet_name=0)  # First sheet
        print_debug(f"Loaded rates Excel file: {excel_file_path}")
        print_debug(f"Excel columns: {list(df.columns)}")
        
        global RATES_DATA
        # Clear existing data
        RATES_DATA['MTPT'].clear()
        RATES_DATA['Translation'].clear()
        RATES_DATA['TM_Fuzzy'].clear()
        RATES_DATA['TM_Exact'].clear()
        
        # Process each row to extract rates by ISO code
        for _, row in df.iterrows():
            iso_code = row.get('Iso Code', '').strip()
            if not iso_code or iso_code.lower() in ['nan', 'iso code', '']:
                continue
            
            # Extract MTPT rates 
            mtpt_old = extract_numeric_value(row.get('MTPT', None))
            mtpt_new = extract_numeric_value(row.get('MTPT - new', None))
            
            if mtpt_old is not None or mtpt_new is not None:
                RATES_DATA['MTPT'][iso_code] = {
                    'old_rate': mtpt_old if mtpt_old is not None else 0.0,
                    'new_rate': mtpt_new if mtpt_new is not None else 0.0
                }
            
            # Extract Translation rates (New Words columns)
            trans_old = extract_numeric_value(row.get('New Words', None))
            trans_new = extract_numeric_value(row.get('New Words - new', None))
            
            if trans_old is not None or trans_new is not None:
                RATES_DATA['Translation'][iso_code] = {
                    'old_rate': trans_old if trans_old is not None else 0.0,
                    'new_rate': trans_new if trans_new is not None else 0.0
                }
            
            # Extract TM Fuzzy Match rates (Fuzzy columns)
            fuzzy_old = extract_numeric_value(row.get('Fuzzy', None))
            fuzzy_new = extract_numeric_value(row.get('Fuzzy - new', None))
            
            if fuzzy_old is not None or fuzzy_new is not None:
                RATES_DATA['TM_Fuzzy'][iso_code] = {
                    'old_rate': fuzzy_old if fuzzy_old is not None else 0.0,
                    'new_rate': fuzzy_new if fuzzy_new is not None else 0.0
                }
            
            # Extract TM Exact Match rates (Gold columns)
            gold_old = extract_numeric_value(row.get('Gold', None))
            gold_new = extract_numeric_value(row.get('Gold - new', None))
            
            if gold_old is not None or gold_new is not None:
                RATES_DATA['TM_Exact'][iso_code] = {
                    'old_rate': gold_old if gold_old is not None else 0.0,
                    'new_rate': gold_new if gold_new is not None else 0.0
                }
        
        print_debug(f"Loaded rates for {len(RATES_DATA['MTPT'])} MTPT languages, {len(RATES_DATA['Translation'])} Translation languages")
        print_debug(f"Loaded TM rates for {len(RATES_DATA['TM_Fuzzy'])} Fuzzy Match and {len(RATES_DATA['TM_Exact'])} Exact Match languages")
        return True
        
    except Exception as e:
        print_debug(f"Error loading rates from Excel: {e}")
        return False

def extract_numeric_value(value):
    """Extract numeric value from cell, handling various formats"""
    if pd.isna(value) or value == '' or value == '-':
        return None
    
    try:
        # Remove dollar signs and convert to float
        if isinstance(value, str):
            value = value.replace('$', '').strip()
        return float(value)
    except (ValueError, TypeError):
        return None

def get_non_english_language_from_pair(language_pair):
    """Extract non-English language from a language pair like 'en>fr-FR' or 'English-French'"""
    if not language_pair:
        return None
    
    language_pair = str(language_pair).lower().strip()
    
    # Handle formats like "en>fr-FR", "en-us>fr-fr"
    for separator in ['>', '->', ' to ', ' into ', '_to_', '_into_']:
        if separator in language_pair:
            parts = language_pair.split(separator)
            if len(parts) == 2:
                source = parts[0].strip()
                target = parts[1].strip()
                
                # Return the non-English language
                if source.startswith('en') or 'english' in source:
                    return target
                elif target.startswith('en') or 'english' in target:
                    return source
                else:
                    # If neither is clearly English, return target
                    return target
    
    # Handle hyphenated format like "English-French"
    if '-' in language_pair:
        parts = language_pair.split('-')
        if len(parts) == 2:
            source = parts[0].strip()
            target = parts[1].strip()
            
            if 'english' in source or source == 'en':
                return target
            elif 'english' in target or target == 'en':
                return source
            else:
                return target
    
    return language_pair

def map_language_to_iso_code(language):
    """Map language to ISO code with fallback to base code"""
    if not language:
        return None
    
    language = str(language).lower().strip()
    
    # If it's already an ISO code, use it directly (keep original case from Excel)
    if len(language) >= 2 and '-' in language:
        # For codes like "fr-fr", try full code first, then base code
        # Convert to the format used in Excel (e.g., fr-FR)
        parts = language.split('-')
        if len(parts) == 2:
            formatted_code = f"{parts[0].lower()}-{parts[1].upper()}"
            base_code = parts[0].upper()
            
            # Check if formatted code exists in our rates
            if formatted_code in RATES_DATA.get('MTPT', {}) or formatted_code in RATES_DATA.get('Translation', {}):
                return formatted_code
            
            # Fallback to base code
            if base_code in RATES_DATA.get('MTPT', {}) or base_code in RATES_DATA.get('Translation', {}):
                return base_code
    
    # Simple language name mapping
    language_map = {
        'english': 'en-US',
        'english (us)': 'en-US',
        'english (uk)': 'en-GB',
        'french': 'fr-FR',
        'spanish': 'es-ES', 
        'german': 'de-DE',
        'italian': 'it-IT',
        'portuguese': 'pt-PT',
        'dutch': 'nl-NL',
        'chinese': 'zh-CN',
        'chinese (s)': 'zh-CN',  # Chinese (Simplified)
        'chinese simplified': 'zh-CN',
        'chinese (t)': 'zh-TW',  # Chinese (Traditional)
        'chinese traditional': 'zh-TW',
        'japanese': 'ja-JP',
        'korean': 'ko-KR',
        'arabic': 'ar-SA'
    }
    
    if language in language_map:
        iso_code = language_map[language]
        # Check if full code exists, otherwise try base code
        base_code = iso_code.split('-')[0].upper()
        
        if iso_code in RATES_DATA.get('MTPT', {}) or iso_code in RATES_DATA.get('Translation', {}):
            return iso_code
        elif base_code in RATES_DATA.get('MTPT', {}) or base_code in RATES_DATA.get('Translation', {}):
            return base_code
    
    # Handle regional variants that might not be in rates - fall back to standard variants
    if language.startswith('fr-') and len(language) == 5:
        # For French regional variants like fr-CI, try fallback to fr-FR first
        fallback_codes = ['fr-FR', 'FR']
        for fallback in fallback_codes:
            if fallback in RATES_DATA.get('MTPT', {}) or fallback in RATES_DATA.get('Translation', {}):
                return fallback
    
    # Return original language in case it matches directly
    return language

def get_rates_for_language_pair(language_pair, service_type, study_type):
    """Get rates for language pair based on service type and study type
    Returns: tuple (rate, actual_service_type) where actual_service_type may be different from 
             requested service_type if fallback occurred from MTPT to Translation"""
    if not language_pair or not service_type:
        return None, None
    
    # Extract non-English language from pair
    non_en_language = get_non_english_language_from_pair(language_pair)
    if not non_en_language:
        return None, None
    
    # Map to ISO code
    iso_code = map_language_to_iso_code(non_en_language)
    if not iso_code:
        return None, None
    
    # Get rates from loaded data
    service_rates = RATES_DATA.get(service_type, {})
    language_rates = service_rates.get(iso_code, {})
    
    # If exact match found, use it
    if language_rates:
        print_debug(f"Found exact rates for {iso_code} in service {service_type}")
    else:
        # Try base language code if full code not found (e.g., es-LA -> es)
        base_code = iso_code.split('-')[0] if '-' in iso_code else iso_code
        
        if base_code != iso_code:
            # Look for any language variant with the same base code
            for available_lang in service_rates.keys():
                if available_lang.startswith(base_code + '-') or available_lang == base_code:
                    language_rates = service_rates[available_lang]
                    print_debug(f"Using fallback rates from {available_lang} for requested {iso_code} in service {service_type}")
                    break
        
        # If still no rates found, try the base code directly
        if not language_rates:
            language_rates = service_rates.get(base_code, {})
            if language_rates:
                print_debug(f"Using base language rates from {base_code} for requested {iso_code} in service {service_type}")
    
    if not language_rates:
        print_debug(f"No rates found for language {iso_code} (or base {iso_code.split('-')[0]}) in service {service_type}")
        print_debug(f"Available languages in {service_type}: {list(service_rates.keys())}")
        return None, None
    
    # Return appropriate rate based on study type
    if study_type == "Old rate study":
        rate = language_rates.get('old_rate', 0.0)
    else:
        rate = language_rates.get('new_rate', 0.0)
    
    # Track the actual service type used (may change due to fallback)
    actual_service_type = service_type
    
    # FALLBACK LOGIC: If MTPT rate is 0 or None, fall back to Translation service
    if service_type == "MTPT" and (rate == 0.0 or rate is None):
        print_debug(f"MTPT rate is {rate} for {iso_code}, attempting fallback to Translation service")
        
        # Try to get Translation rate for the same language
        translation_rates = RATES_DATA.get('Translation', {}).get(iso_code, {})
        if translation_rates:
            fallback_rate = translation_rates.get('new_rate' if study_type != "Old rate study" else 'old_rate', 0.0)
            if fallback_rate > 0.0:
                print_debug(f"Using Translation fallback rate {fallback_rate} for {iso_code} (was MTPT {rate})")
                # Update both rate and service type for fallback
                rate = fallback_rate
                actual_service_type = "Translation"
            else:
                print_debug(f"Translation fallback rate is also {fallback_rate}, keeping MTPT rate {rate}")
        else:
            print_debug(f"No Translation rates available for fallback for {iso_code}")
    
    return rate, actual_service_type

def get_tm_rate_for_language_pair(language_pair, tm_type, study_type):
    """Get TM rate for language pair (Fuzzy Match or Exact Match)
    
    Args:
        language_pair: Language pair string (e.g., "en>fr-FR")
        tm_type: Either "TM_Fuzzy" or "TM_Exact"
        study_type: "Old rate study" or "New rate study"
    
    Returns:
        float: Rate value or 0.0 if not found
    """
    if not language_pair or not tm_type:
        return 0.0
    
    # Extract non-English language from pair
    non_en_language = get_non_english_language_from_pair(language_pair)
    if not non_en_language:
        return 0.0
    
    # Map to ISO code
    iso_code = map_language_to_iso_code(non_en_language)
    if not iso_code:
        return 0.0
    
    # Get rates from loaded data
    tm_rates = RATES_DATA.get(tm_type, {})
    language_rates = tm_rates.get(iso_code, {})
    
    # If exact match found, use it
    if language_rates:
        print_debug(f"Found exact TM rates for {iso_code} in {tm_type}")
    else:
        # Try base language code if full code not found
        base_code = iso_code.split('-')[0] if '-' in iso_code else iso_code
        
        if base_code != iso_code:
            # Look for any language variant with the same base code
            for available_lang in tm_rates.keys():
                if available_lang.startswith(base_code + '-') or available_lang == base_code:
                    language_rates = tm_rates[available_lang]
                    print_debug(f"Using fallback TM rates from {available_lang} for requested {iso_code} in {tm_type}")
                    break
        
        # If still no rates found, try the base code directly
        if not language_rates:
            language_rates = tm_rates.get(base_code, {})
            if language_rates:
                print_debug(f"Using base language TM rates from {base_code} for requested {iso_code} in {tm_type}")
    
    if not language_rates:
        print_debug(f"No TM rates found for language {iso_code} in {tm_type}")
        return 0.0
    
    # Return appropriate rate based on study type
    if study_type == "Old rate study":
        rate = language_rates.get('old_rate', 0.0)
    else:
        rate = language_rates.get('new_rate', 0.0)
    
    return rate if rate is not None else 0.0

def extract_rate_from_row(row, possible_column_names):
    """Extract rate value from row using possible column name variations"""
    for col_name in possible_column_names:
        # Try exact match first
        if col_name in row.index and pd.notna(row[col_name]):
            try:
                return float(row[col_name])
            except (ValueError, TypeError):
                continue
        
        # Try partial match (case insensitive)
        for actual_col in row.index:
            if col_name.lower() in str(actual_col).lower() and pd.notna(row[actual_col]):
                try:
                    return float(row[actual_col])
                except (ValueError, TypeError):
                    continue
    
    return None

def normalize_language_pair_from_excel(language_pair_str):
    """Normalize language pair string from Excel to our format"""
    # Handle common formats like "EN-US to ES-ES", "EN>ES", "English to Spanish"
    language_pair_str = str(language_pair_str).lower().strip()
    
    # Replace common separators
    for separator in [' to ', ' into ', '>', '->', ' -> ', '_to_', '_into_']:
        if separator in language_pair_str:
            parts = language_pair_str.split(separator)
            if len(parts) == 2:
                source = normalize_language_code(parts[0].strip())
                target = normalize_language_code(parts[1].strip())
                return f"{source}_{target}"
    
    return language_pair_str

def is_old_rate_study(project_code):
    """Check if project code exists in the project_codes array (Old rate study)"""
    if not project_code:
        return False
    
    project_code_str = str(project_code).strip()
    return project_code_str in project_codes

def get_project_code_for_sub_id(sub_id):
    """Extract project code for a specific Sub_ID from CEVA_DF"""
    ceva_df = get_ceva_df()
    if ceva_df.empty:
        print_debug(f"CEVA_DF is empty when looking for project code for Sub_ID {sub_id}")
        return None
    
    print_debug(f"Looking for project code for Sub_ID {sub_id} in CEVA_DF with {len(ceva_df)} rows")
    
    # Find submission ID column
    submission_col = find_column_by_patterns(ceva_df, ['submission id', 'submission_id', 'sub_id'])
    if not submission_col:
        print_debug(f"Could not find submission ID column in CEVA_DF")
        return None
    
    print_debug(f"Found submission ID column: '{submission_col}'")
    
    # Find the row for this Sub_ID
    matching_rows = ceva_df[ceva_df[submission_col].astype(str) == str(sub_id)]
    if matching_rows.empty:
        print_debug(f"No matching rows found for Sub_ID {sub_id}")
        return None
    
    row = matching_rows.iloc[0]
    print_debug(f"Found matching row for Sub_ID {sub_id}")
    
    # Find project code column - prioritize 'Project Code' over 'Protocol'
    project_code_col = find_column_by_patterns(ceva_df, ['project code', 'project_code'])
    if not project_code_col:
        print_debug(f"'Project Code' column not found, trying 'Protocol' as fallback")
        # Fallback to protocol if project code not found
        project_code_col = find_column_by_patterns(ceva_df, ['protocol'])
    
    if project_code_col:
        print_debug(f"Found project code column: '{project_code_col}'")
        if pd.notna(row[project_code_col]):
            project_code_value = str(row[project_code_col]).strip()
            print_debug(f"Extracted project code: '{project_code_value}'")
            return project_code_value
        else:
            print_debug(f"Project code column '{project_code_col}' is empty/null for Sub_ID {sub_id}")
    else:
        print_debug(f"No project code or protocol column found in CEVA_DF")
        print_debug(f"Available columns: {list(ceva_df.columns)}")
    
    return None

def normalize_language_code(language):
    """Normalize language codes to consistent format (lowercase with hyphens)"""
    if not language:
        return ""
    
    # Convert to lowercase and replace common separators
    normalized = str(language).lower().strip()
    normalized = normalized.replace('_', '-')
    normalized = normalized.replace(' ', '-')
    
    # Handle common language code mappings
    language_mappings = {
        'english': 'en-us',
        'greek': 'el-gr',
        'spanish': 'es-es',
        'french': 'fr-fr',
        'german': 'de-de',
        'italian': 'it-it',
        'portuguese': 'pt-pt',
        'dutch': 'nl-nl',
        'russian': 'ru-ru',
        'chinese': 'zh-cn',
        'chinese-(s)': 'zh-cn',  # Chinese (Simplified)
        'chinese-simplified': 'zh-cn',
        'chinese-(t)': 'zh-tw',  # Chinese (Traditional)
        'chinese-traditional': 'zh-tw',
        'japanese': 'ja-jp',
        'korean': 'ko-kr'
    }
    
    return language_mappings.get(normalized, normalized)

def get_language_pair_key(source_lang, target_lang):
    """Generate a standardized language pair key"""
    source = normalize_language_code(source_lang)
    target = normalize_language_code(target_lang)
    return f"{source}_{target}"

def create_translation_charge(source_lang, target_lang, word_count, project_code=None):
    """Create a translation charge line item based on study type and project code"""
    charge = copy.deepcopy(CHARGES_TEMPLATE)
    
    # Determine study type based on project code
    is_old_study = is_old_rate_study(project_code)
    study_type = "Old rate study" if is_old_study else "New rate study"
    
    # Create language pair string
    language_pair = f"{source_lang}>{target_lang}"
    
    # Determine service type based on study
    requested_service_type = "MTPT" if is_old_study else "Translation"
    
    # Get rate and actual service type for this language pair (may fallback from MTPT to Translation)
    rate_to_use, actual_service_type = get_rates_for_language_pair(language_pair, requested_service_type, study_type)
    if rate_to_use is None:
        # No fallback rates - rates must come from Excel file
        print_debug(f"ERROR: No rate found for {language_pair} ({study_type}, {requested_service_type}) in Excel file")
        print_debug("Please ensure this language pair exists in CEVA RATES.xlsx")
        return None
    else:
        print_debug(f"Using rate {rate_to_use} for {language_pair} ({study_type}, {actual_service_type})")
    
    # Normalize language codes for display
    source_display = normalize_language_code(source_lang).upper()
    target_display = normalize_language_code(target_lang).upper()
    
    charge["Mark New Line Item"] = "x"
    charge["Line Item Description"] = f"{source_display} into {target_display}"
    charge["Source"] = normalize_language_code(source_lang)
    charge["Target"] = normalize_language_code(target_lang)
    charge["Service Group 1"] = "Language Services"
    
    # Use actual service type (may have changed due to MTPT → Translation fallback)
    if actual_service_type == "MTPT":
        charge["Service Group 2"] = "Machine Translation"
        charge["Service"] = "Machine Translation"
    else:  # Translation
        charge["Service Group 2"] = "Translation"
        charge["Service"] = "Translation"
    
    charge["Service Group 3"] = ""
    charge["UofM"] = "Word"
    charge["Quantity"] = word_count
    charge["Rate"] = rate_to_use
    charge["CommentsForInvoice"] = ""
    charge["Technology Product"] = "GL PD"
    
    return charge

def create_formatting_charge(source_lang, target_lang, hours, rate_per_hour):
    """Create a formatting charge line item"""
    charge = copy.deepcopy(CHARGES_TEMPLATE)
    
    # Normalize language codes for display
    source_display = normalize_language_code(source_lang).upper()
    target_display = normalize_language_code(target_lang).upper()
    
    charge["Mark New Line Item"] = ""
    charge["Line Item Description"] = f"{source_display} into {target_display}"
    charge["Source"] = normalize_language_code(source_lang)
    charge["Target"] = normalize_language_code(target_lang)
    charge["Service Group 1"] = "Language Services"
    charge["Service Group 2"] = "Desktop Publishing"
    charge["Service Group 3"] = ""
    charge["Service"] = "Formatting"
    charge["UofM"] = "Hour"
    charge["Quantity"] = hours
    charge["Rate"] = rate_per_hour
    charge["CommentsForInvoice"] = ""
    
    return charge

def create_tm_fuzzy_charge(source_lang, target_lang, rate):
    """Create a TM - Fuzzy Matches charge line item"""
    charge = copy.deepcopy(CHARGES_TEMPLATE)
    
    # Normalize language codes for display
    source_display = normalize_language_code(source_lang).upper()
    target_display = normalize_language_code(target_lang).upper()
    
    charge["Mark New Line Item"] = ""
    charge["Line Item Description"] = f"{source_display} into {target_display}"
    charge["Source"] = normalize_language_code(source_lang)
    charge["Target"] = normalize_language_code(target_lang)
    charge["Service Group 1"] = "Language Services"
    charge["Service Group 2"] = "Translation"
    charge["Service Group 3"] = ""
    charge["Service"] = "TM - Fuzzy Matches"
    charge["UofM"] = "Word"
    charge["Quantity"] = 0
    charge["Rate"] = rate
    charge["CommentsForInvoice"] = ""
    charge["Technology Product"] = "GL PD"
    
    return charge

def create_tm_exact_charge(source_lang, target_lang, rate):
    """Create a TM - Exact Matches charge line item"""
    charge = copy.deepcopy(CHARGES_TEMPLATE)
    
    # Normalize language codes for display
    source_display = normalize_language_code(source_lang).upper()
    target_display = normalize_language_code(target_lang).upper()
    
    charge["Mark New Line Item"] = ""
    charge["Line Item Description"] = f"{source_display} into {target_display}"
    charge["Source"] = normalize_language_code(source_lang)
    charge["Target"] = normalize_language_code(target_lang)
    charge["Service Group 1"] = "Language Services"
    charge["Service Group 2"] = "Translation"
    charge["Service Group 3"] = ""
    charge["Service"] = "TM - Exact Matches"
    charge["UofM"] = "Word"
    charge["Quantity"] = 0
    charge["Rate"] = rate
    charge["CommentsForInvoice"] = ""
    charge["Technology Product"] = "GL PD"
    
    return charge

def create_pd_maintenance_charge(source_lang, target_lang, flat_fee):
    """Create a PD maintenance charge line item"""
    charge = copy.deepcopy(CHARGES_TEMPLATE)
    
    # Normalize language codes for display
    source_display = normalize_language_code(source_lang).upper()
    target_display = normalize_language_code(target_lang).upper()
    
    charge["Mark New Line Item"] = ""
    charge["Line Item Description"] = f"{source_display} into {target_display}"
    charge["Source"] = normalize_language_code(source_lang)
    charge["Target"] = normalize_language_code(target_lang)
    charge["Service Group 1"] = "Technology"
    charge["Service Group 2"] = "GL Project Director"
    charge["Service Group 3"] = ""
    charge["Service"] = "PD Maintenance"
    charge["UofM"] = "Fee"
    charge["Quantity"] = flat_fee
    charge["Rate"] = ""
    charge["CommentsForInvoice"] = ""
    
    return charge

def find_column_by_patterns(df, patterns):
    """Find column in DataFrame that matches any of the given patterns (case insensitive)"""
    # First try exact matches
    for pattern in patterns:
        for col in df.columns:
            if str(col).lower().strip() == pattern.lower().strip():
                return col
    
    # Then try partial matches
    for col in df.columns:
        col_lower = str(col).lower().strip()
        if any(pattern.lower() in col_lower for pattern in patterns):
            return col
    return None

def get_job_data_for_charges(sub_id):
    """Extract necessary data for charge generation from WC_DF and CEVA_DF"""
    # Get word count data
    wc_df = get_wc_df()
    if wc_df.empty:
        print_debug(f"WC_DF is empty for Sub_ID: {sub_id}")
        return None
    
    # Find the row for this Sub_ID in WC_DF
    wc_matching_rows = wc_df[wc_df['Sub_ID'].astype(str) == str(sub_id)]
    if wc_matching_rows.empty:
        print_debug(f"No matching data found in WC_DF for Sub_ID: {sub_id}")
        return None
    
    wc_row = wc_matching_rows.iloc[0]
    word_count = wc_row.get('Total_WC', 0)
    
    # Get language data from CEVA_DF
    ceva_df = get_ceva_df()
    if ceva_df.empty:
        print_debug(f"CEVA_DF is empty for Sub_ID: {sub_id}")
        return None
    
    # Find submission ID column in CEVA_DF
    submission_col = find_column_by_patterns(ceva_df, ['submission id', 'submission_id', 'sub_id'])
    if not submission_col:
        print_debug("Could not find Submission ID column in CEVA_DF")
        return None
    
    # Find the row for this Sub_ID in CEVA_DF
    ceva_matching_rows = ceva_df[ceva_df[submission_col].astype(str) == str(sub_id)]
    if ceva_matching_rows.empty:
        print_debug(f"No matching data found in CEVA_DF for Sub_ID: {sub_id}")
        return None
    
    ceva_row = ceva_matching_rows.iloc[0]
    
    # Extract source and target languages
    source_lang_col = find_column_by_patterns(ceva_df, ['source language', 'source_language', 'from language'])
    target_lang_col = find_column_by_patterns(ceva_df, ['target language', 'target_language', 'to language'])
    
    source_language = ""
    target_language = ""
    
    if source_lang_col and pd.notna(ceva_row[source_lang_col]):
        source_language = str(ceva_row[source_lang_col])
    
    if target_lang_col and pd.notna(ceva_row[target_lang_col]):
        target_language = str(ceva_row[target_lang_col])
    
    if not source_language or not target_language:
        print_debug(f"Missing language data for Sub_ID {sub_id}: Source='{source_language}', Target='{target_language}'")
        return None
    
    job_data = {
        'sub_id': sub_id,
        'word_count': word_count,
        'source_language': source_language,
        'target_language': target_language
    }
    
    print_debug(f"Job data for Sub_ID {sub_id}: {job_data}")
    return job_data

def calculate_formatting_hours(word_count):
    """Calculate formatting hours based on word count"""
    # Default formula: 1 hour per 1000 words, minimum 1 hour
    # Round up to nearest 0.5 (like Excel CEILING.MATH(value, 0.5))
    hours = word_count / 1000
    hours_ceiled = math.ceil(hours / 0.5) * 0.5
    return max(1, hours_ceiled)

def generate_charges_for_sub_id(sub_id):
    """Generate charges for a specific Sub_ID"""
    print_debug(f"Generating charges for Sub_ID: {sub_id}")
    
    # Get job data
    job_data = get_job_data_for_charges(sub_id)
    if not job_data:
        print_debug(f"Could not retrieve job data for Sub_ID: {sub_id}")
        return []
    
    source_lang = job_data['source_language']
    target_lang = job_data['target_language']
    word_count = job_data['word_count']
    
    # Get project code to determine study type
    project_code = get_project_code_for_sub_id(sub_id)
    is_old_study = is_old_rate_study(project_code)
    
    study_type = "Old rate study" if is_old_study else "New rate study"
    print_debug(f"Sub_ID {sub_id}: Project code '{project_code}' -> {study_type}")
    
    charges = []
    
    # 1. Translation charge
    if word_count > 0:
        translation_charge = create_translation_charge(
            source_lang, target_lang, word_count, project_code
        )
        if translation_charge is not None:
            charges.append(translation_charge)
        else:
            print_debug(f"ERROR: Could not create translation charge for Sub_ID {sub_id} - rate not found in Excel file")
            return []  # Return empty if we can't get translation rates
        
    # 2. TM - Fuzzy Matches charge output with 0 quantity and correct rate
    language_pair = f"{source_lang} > {target_lang}"
    is_old_study = project_code.lower().startswith('c-')
    study_type = 'old' if is_old_study else 'new'
    
    tm_fuzzy_rate = get_tm_rate_for_language_pair(language_pair, 'TM_Fuzzy', study_type)
    if tm_fuzzy_rate is not None:
        tm_fuzzy_charge = create_tm_fuzzy_charge(source_lang, target_lang, tm_fuzzy_rate)
        charges.append(tm_fuzzy_charge)
    else:
        print_debug(f"WARNING: Could not find TM - Fuzzy Matches rate for {language_pair} (study type: {study_type})")

    # 3. TM - Exact Matches charge output with 0 quantity and correct rate
    tm_exact_rate = get_tm_rate_for_language_pair(language_pair, 'TM_Exact', study_type)
    if tm_exact_rate is not None:
        tm_exact_charge = create_tm_exact_charge(source_lang, target_lang, tm_exact_rate)
        charges.append(tm_exact_charge)
    else:
        print_debug(f"WARNING: Could not find TM - Exact Matches rate for {language_pair} (study type: {study_type})")

    # 4. Formatting charge (using configuration rate)
    formatting_hours = calculate_formatting_hours(word_count)
    formatting_rate = 40.0  # Configuration rate (updated from hardcoded 85.0)
    formatting_charge = create_formatting_charge(
        source_lang, target_lang, formatting_hours, formatting_rate
    )
    charges.append(formatting_charge)
    
    # 5. PD Maintenance charge (using configuration rate)
    pd_rate = 0.01  # Configuration rate
    pd_charge = create_pd_maintenance_charge(
        source_lang, target_lang, pd_rate
    )
    charges.append(pd_charge)
    
    print_debug(f"Generated {len(charges)} charges for Sub_ID {sub_id} ({study_type})")
    return charges

def generate_all_charges():
    """Generate charges for all jobs in WC_DF"""
    wc_df = get_wc_df()
    if wc_df.empty:
        print_debug("WC_DF is empty, no charges to generate")
        return {}
    
    all_charges = {}
    sub_ids = wc_df['Sub_ID'].tolist()
    
    print_debug(f"Generating charges for {len(sub_ids)} jobs")
    
    for sub_id in sub_ids:
        try:
            charges = generate_charges_for_sub_id(sub_id)
            if charges:
                all_charges[sub_id] = charges
        except Exception as e:
            print_debug(f"Error generating charges for Sub_ID {sub_id}: {e}")
    
    print_debug(f"Successfully generated charges for {len(all_charges)} jobs")
    return all_charges

def export_charges_to_excel_worksheets(writer, job_ids):
    """Export charges for specific job IDs as separate worksheets in existing Excel writer
    
    Args:
        writer: pandas ExcelWriter object (already opened)
        job_ids: List of job IDs to process
    """
    successful_exports = []
    failed_exports = []
    
    for job_id in job_ids:
        try:
            print_debug(f"Generating charges worksheet for Sub_ID: {job_id}")
            
            # Generate charges for this job
            charges = generate_charges_for_sub_id(job_id)
            
            if not charges:
                print_debug(f"No charges generated for Sub_ID: {job_id}")
                failed_exports.append(f"Sub_ID {job_id}: No charges data")
                continue
            
            # Convert charges to DataFrame
            df = pd.DataFrame(charges)
            
            # Create worksheet name for charges (limit to 31 chars for Excel)
            ws_name = f"Sub_{job_id}_Charges"
            if len(ws_name) > 31:
                ws_name = f"S_{job_id}_Charges"[:31]
            
            # Write to worksheet
            df.to_excel(writer, sheet_name=ws_name, index=False)
            print_debug(f"Created charges worksheet '{ws_name}' for Sub_ID: {job_id}")
            successful_exports.append(job_id)
            
        except Exception as e:
            error_msg = f"Sub_ID {job_id}: {str(e)}"
            failed_exports.append(error_msg)
            print_debug(f"Error creating charges worksheet for Sub_ID {job_id}: {e}")
    
    return successful_exports, failed_exports

def update_language_pair_rates(source_lang, target_lang, translation_rate=None, formatting_rate=None, pd_maintenance_rate=None):
    """Update rates for a specific language pair"""
    pair_key = get_language_pair_key(source_lang, target_lang)
    
    if pair_key not in LANGUAGE_PAIR_RATES:
        LANGUAGE_PAIR_RATES[pair_key] = {}
    
    if translation_rate is not None:
        LANGUAGE_PAIR_RATES[pair_key]["translation"] = translation_rate
    
    if formatting_rate is not None:
        LANGUAGE_PAIR_RATES[pair_key]["formatting"] = formatting_rate
    
    if pd_maintenance_rate is not None:
        LANGUAGE_PAIR_RATES[pair_key]["pd_maintenance"] = pd_maintenance_rate
    
    print_debug(f"Updated rates for {source_lang} -> {target_lang}: {LANGUAGE_PAIR_RATES[pair_key]}")

def get_study_type_for_sub_id(sub_id):
    """Get the study type (Old/New rate study) for a specific Sub_ID for GUI display"""
    project_code = get_project_code_for_sub_id(sub_id)
    is_old = is_old_rate_study(project_code)
    return "Old rate study" if is_old else "New rate study"

def get_all_language_pairs():
    """Get all configured language pairs and their rates"""
    return LANGUAGE_PAIR_RATES.copy()

def load_rates_from_config(config_dict):
    """Load rates from a configuration dictionary"""
    global LANGUAGE_PAIR_RATES
    LANGUAGE_PAIR_RATES.update(config_dict)
    print_debug(f"Loaded rates for {len(config_dict)} language pairs")

def initialize_rates():
    """Initialize rates from Excel file"""
    print_debug("Initializing rates from Excel file...")
    success = load_rates_from_excel()
    if success:
        print_debug("Rates initialized successfully from Excel")
    else:
        print_debug("ERROR: Failed to load rates from Excel file")
        print_debug("Please ensure CEVA RATES.xlsx is available and properly formatted")
    return success

if __name__ == "__main__":
    # For testing purposes
    initialize_rates()
    print("ChargesIntegration module loaded successfully")
    print("Available MTPT rates:", len(RATES_DATA.get('MTPT', {})))
    print("Available Translation rates:", len(RATES_DATA.get('Translation', {})))
