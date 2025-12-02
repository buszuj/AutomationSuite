"""
Rate Calculations Module
Handles all rate and quantity calculations for services.
"""

import math
import pandas as pd
from typing import Dict, Any


def get_service_type(service: str, uom: str) -> str:
    """
    Determine the service type based on Unit of Measure (UofM).
    
    Args:
        service: Service name
        uom: Unit of Measure (Word, Hour, etc.)
    
    Returns:
        Service type: 'wcType', 'hType', or 'PercentageType'
    """
    if uom == "Word":
        return "wcType"
    elif uom == "Hour":
        return "hType"
    else:
        return "PercentageType"


def calculate_hourly_quantity(
    service: str,
    file_type: str,
    use_qtc_input: bool,
    quoteme_wc: float,
    qtc_wc_translation: float,
    qtc_wc_revision: float,
    config: Dict[str, Any]
) -> float:
    """
    Calculate the quantity for an hourly service based on configuration.
    
    Args:
        service: Service name
        file_type: "Live" or "Dead"
        use_qtc_input: Whether QTC input is used (True) or QuoteMe (False)
        quoteme_wc: Total QuoteMe word count
        qtc_wc_translation: QTC word count for translation
        qtc_wc_revision: QTC word count for revision
        config: Service configuration mapping
    
    Returns:
        Calculated quantity in hours
    """
    min_hourly_rate = float(config.get("min_hourly_rate", 0.5) or 0.5)
    increment_rate = float(config.get("increment_rate", 0.25) or 0.25)
    
    svc_conf = config.get(service, {})
    
    if use_qtc_input:
        qtc_cfg = svc_conf.get("QTC", {})
        divider = float(qtc_cfg.get("live_divider" if file_type == "Live" else "dead_divider", 1) or 1)
        
        # Use the tickboxes to decide which QTC WC to use
        if qtc_cfg.get("use_wc_for_translation"):
            wc = qtc_wc_translation
        elif qtc_cfg.get("use_wc_for_revision"):
            wc = qtc_wc_revision
        else:
            wc = 0
    else:
        quoteme_cfg = svc_conf.get("QuoteMe", {})
        divider = float(quoteme_cfg.get("live_divider" if file_type == "Live" else "dead_divider", 1) or 1)
        wc = quoteme_wc

    if divider == 0:
        return min_hourly_rate
    
    hours = wc / divider
    hours_ceiled = math.ceil(hours / increment_rate) * increment_rate
    
    return max(hours_ceiled, min_hourly_rate)


def get_word_rate(
    df_ratesheet: pd.DataFrame,
    source_lang: str,
    target_lang: str,
    service: str
) -> float:
    """
    Get word-based rate from ratesheet worksheet.
    
    Args:
        df_ratesheet: DataFrame containing the ratesheet
        source_lang: Source language
        target_lang: Target language
        service: Service name
    
    Returns:
        Rate for the service, or 0 if not found
    """
    # Map plural service names to singular column names if needed
    service_column_map = {
        "TM - Fuzzy Matches": "TM - Fuzzy Match",
        "TM - Exact Matches": "TM - Exact Match",
    }
    service_lookup = service_column_map.get(service, service)
    
    try:
        mask = (df_ratesheet["Source Language"] == source_lang) & \
               (df_ratesheet["Target Language"] == target_lang)
        row = df_ratesheet[mask]
        
        if not row.empty:
            if service_lookup in df_ratesheet.columns:
                rate = row[service_lookup].iloc[0]
                return float(rate) if pd.notna(rate) else 0
            else:
                if service in ["Translation", "Machine Translation"]:
                    print(f"Warning: Service '{service_lookup}' not found in ratesheet")
    except Exception as e:
        print(f"Error getting word rate for {service}: {str(e)}")
    
    return 0


def get_hourly_rate(df_ratesheet: pd.DataFrame, service: str) -> float:
    """
    Get hourly rate from ratesheet worksheet (first row).
    
    Args:
        df_ratesheet: DataFrame containing the ratesheet
        service: Service name
    
    Returns:
        Hourly rate for the service, or 0 if not found
    """
    try:
        if service in df_ratesheet.columns:
            rate = df_ratesheet[service].iloc[0]
            return float(rate) if pd.notna(rate) else 0
    except Exception as e:
        print(f"Error getting hourly rate: {e}")
    
    return 0


def apply_minimum_fee_logic(
    row_data: list,
    services_uofm: Dict[str, str],
    min_fee: float
) -> list:
    """
    Apply minimum fee logic to service rows.
    
    Args:
        row_data: List of dictionaries containing service row data
        services_uofm: Dictionary mapping services to their UofM
        min_fee: Minimum fee threshold
    
    Returns:
        Updated row_data with minimum fee logic applied
    """
    # Calculate sumproduct for Word services except Back Translation
    word_sumproduct = sum(
        float(row["quantity"]) * float(row["rate"])
        for row in row_data
        if services_uofm.get(row["service"], "") == "Word" and row["service"] != "Back Translation"
    )
    
    if word_sumproduct < min_fee:
        for row in row_data:
            if row["service"] in ["Translation", "Machine Translation"]:
                row["UofM"] = "Minimum"
                row["quantity"] = 1
                row["rate"] = min_fee
            elif services_uofm.get(row["service"], "") == "Word" and row["service"] != "Back Translation":
                row["quantity"] = 0
    
    # Back Translation min fee logic
    bt_row = next((row for row in row_data if row["service"] == "Back Translation"), None)
    if bt_row:
        bt_sum = float(bt_row["quantity"]) * float(bt_row["rate"])
        if bt_sum < min_fee:
            bt_row["UofM"] = "Minimum"
            bt_row["quantity"] = 1
            bt_row["rate"] = min_fee
    
    return row_data


def calculate_percentage_service_rate(
    row_data: list,
    service_index: int,
    service_name: str
) -> float:
    """
    Calculate rate for percentage-based services (Project Management, Rush Premium).
    
    Args:
        row_data: List of service row dictionaries
        service_index: Index of the current service in row_data
        service_name: Name of the service
    
    Returns:
        Calculated rate based on sum of previous services
    """
    total_value = 0
    
    if service_name == "Project Management":
        # Sum all services above (excluding itself)
        for j in range(service_index):
            total_value += float(row_data[j]["quantity"]) * float(row_data[j]["rate"])
    elif service_name == "Rush Premium":
        # Sum all services above (including Project Management and itself)
        for j in range(service_index + 1):
            q = float(row_data[j]["quantity"])
            r = float(row_data[j]["rate"]) if row_data[j]["rate"] is not None else 0
            total_value += q * r
    
    return round(total_value, 6)


def sanitize_csv_value(val) -> str:
    """
    Sanitize values for CSV output.
    
    Args:
        val: Value to sanitize
    
    Returns:
        Sanitized string value
    """
    if pd.isna(val) or val is None or str(val).lower() == 'nan':
        return ""
    return str(val)
