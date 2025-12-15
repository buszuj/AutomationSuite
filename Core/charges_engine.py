"""
Generic Charges Engine - Core Module
Generates charges for translation jobs based on configurable rate structures

This module provides a flexible, account-agnostic charges engine that:
1. Loads rates from configurable Excel files
2. Generates charges based on service types (Translation, TM-Fuzzy, TM-Exact, Formatting, etc.)
3. Supports custom charge calculation formulas
4. Exports charges to Excel worksheets

Unlike charges_engine_ceva.py (CEVA-specific), this engine works with any account's ratesheet.

Author: AutomationSuite Team
Date: December 2025
"""

import pandas as pd
import numpy as np
import os
import math
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


class ChargesEngine:
    """
    Generic charges engine for translation jobs
    
    Supports:
    - Word-based rates (Translation, TM-Fuzzy, TM-Exact)
    - Hour-based rates (Formatting, PM, QA, etc.)
    - Minimum fee logic
    - Custom percentage-based rates
    """
    
    def __init__(self, rates_file: Optional[str] = None):
        """
        Initialize Charges Engine
        
        Args:
            rates_file: Path to Excel file with rates (optional)
        """
        self.rates_file = rates_file
        self.rates_data: Dict[str, Dict[str, Any]] = {}
        
        if rates_file and os.path.exists(rates_file):
            self.load_rates_from_excel(rates_file)
    
    def load_rates_from_excel(
        self,
        file_path: str,
        sheet_name: str = "Rates",
        iso_column: str = "Iso Code",
        service_columns: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Load rates from Excel file
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name containing rates
            iso_column: Column name for ISO codes
            service_columns: Dict mapping service types to column names
                Example: {"Translation": "New Words", "TM_Fuzzy": "Fuzzy Match"}
        
        Returns:
            True if successful, False otherwise
        """
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Default service column mappings
            if service_columns is None:
                service_columns = {
                    "Translation": "New Words",
                    "TM_Fuzzy": "Fuzzy",
                    "TM_Exact": "Gold",
                    "MTPT": "MTPT",
                    "Formatting": "Formatting",
                    "PM": "PM"
                }
            
            # Clear existing data
            self.rates_data.clear()
            
            # Process each row
            for _, row in df.iterrows():
                iso_code = str(row.get(iso_column, "")).strip()
                if not iso_code or iso_code.lower() in ['nan', 'iso code', '']:
                    continue
                
                # Initialize rates dict for this ISO code
                if iso_code not in self.rates_data:
                    self.rates_data[iso_code] = {}
                
                # Extract rates for each service type
                for service_type, column_name in service_columns.items():
                    if column_name in df.columns:
                        rate = self._extract_numeric_value(row.get(column_name))
                        if rate is not None:
                            self.rates_data[iso_code][service_type] = rate
            
            print(f"Loaded rates for {len(self.rates_data)} language(s)")
            return True
        
        except Exception as e:
            print(f"Error loading rates from Excel: {e}")
            return False
    
    def _extract_numeric_value(self, value: Any) -> Optional[float]:
        """Extract numeric value from cell, handling various formats"""
        if pd.isna(value) or value == '' or value == '-':
            return None
        
        try:
            # Remove currency symbols and convert to float
            if isinstance(value, str):
                value = value.replace('$', '').replace('€', '').replace('£', '').strip()
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def get_rate(
        self,
        language_pair: str,
        service_type: str,
        fallback_rate: Optional[float] = None
    ) -> Optional[float]:
        """
        Get rate for a language pair and service type
        
        Args:
            language_pair: Language pair (e.g., "en-US > fr-FR")
            service_type: Service type (e.g., "Translation", "TM_Fuzzy")
            fallback_rate: Optional fallback rate if not found
        
        Returns:
            Rate value or None if not found
        """
        # Extract target language ISO code
        iso_code = self._extract_target_language(language_pair)
        if not iso_code:
            return fallback_rate
        
        # Try full ISO code first (e.g., "fr-FR")
        if iso_code in self.rates_data:
            rate = self.rates_data[iso_code].get(service_type)
            if rate is not None:
                return rate
        
        # Try base code (e.g., "fr" from "fr-FR")
        if '-' in iso_code:
            base_code = iso_code.split('-')[0].upper()
            if base_code in self.rates_data:
                rate = self.rates_data[base_code].get(service_type)
                if rate is not None:
                    return rate
        
        return fallback_rate
    
    def _extract_target_language(self, language_pair: str) -> Optional[str]:
        """
        Extract target language ISO code from language pair
        
        Args:
            language_pair: Language pair string (e.g., "en-US > fr-FR")
        
        Returns:
            Target language ISO code or None
        """
        if not language_pair:
            return None
        
        language_pair = str(language_pair).strip()
        
        # Handle various separators
        for separator in ['>', '->', ' to ', ' into ', '_to_', '_into_']:
            if separator in language_pair:
                parts = language_pair.split(separator)
                if len(parts) == 2:
                    target = parts[1].strip()
                    return target
        
        # If no separator, assume it's just the target language
        return language_pair
    
    def generate_translation_charge(
        self,
        word_count: float,
        language_pair: str,
        project_code: str = "",
        job_id: str = ""
    ) -> Dict[str, Any]:
        """
        Generate translation charge
        
        Args:
            word_count: Number of words
            language_pair: Language pair
            project_code: Project code
            job_id: Job ID
        
        Returns:
            Charge dictionary
        """
        rate = self.get_rate(language_pair, "Translation", fallback_rate=0.15)
        
        return {
            "Project Code": project_code,
            "Job ID": job_id,
            "Service": "Translation",
            "Language Pair": language_pair,
            "Quantity": word_count,
            "Unit": "words",
            "Rate": rate,
            "Amount": round(word_count * rate, 2)
        }
    
    def generate_tm_fuzzy_charge(
        self,
        word_count: float,
        language_pair: str,
        project_code: str = "",
        job_id: str = ""
    ) -> Dict[str, Any]:
        """
        Generate TM Fuzzy Match charge
        
        Args:
            word_count: Number of fuzzy match words
            language_pair: Language pair
            project_code: Project code
            job_id: Job ID
        
        Returns:
            Charge dictionary
        """
        rate = self.get_rate(language_pair, "TM_Fuzzy", fallback_rate=0.08)
        
        return {
            "Project Code": project_code,
            "Job ID": job_id,
            "Service": "TM-Fuzzy Match",
            "Language Pair": language_pair,
            "Quantity": word_count,
            "Unit": "words",
            "Rate": rate,
            "Amount": round(word_count * rate, 2)
        }
    
    def generate_tm_exact_charge(
        self,
        word_count: float,
        language_pair: str,
        project_code: str = "",
        job_id: str = ""
    ) -> Dict[str, Any]:
        """
        Generate TM Exact Match charge
        
        Args:
            word_count: Number of exact match words
            language_pair: Language pair
            project_code: Project code
            job_id: Job ID
        
        Returns:
            Charge dictionary
        """
        rate = self.get_rate(language_pair, "TM_Exact", fallback_rate=0.05)
        
        return {
            "Project Code": project_code,
            "Job ID": job_id,
            "Service": "TM-Exact Match",
            "Language Pair": language_pair,
            "Quantity": word_count,
            "Unit": "words",
            "Rate": rate,
            "Amount": round(word_count * rate, 2)
        }
    
    def generate_formatting_charge(
        self,
        word_count: float,
        language_pair: str,
        hourly_rate: float = 55.0,
        words_per_hour: float = 3000.0,
        project_code: str = "",
        job_id: str = ""
    ) -> Dict[str, Any]:
        """
        Generate formatting charge based on hours
        
        Args:
            word_count: Number of words
            language_pair: Language pair
            hourly_rate: Hourly rate for formatting
            words_per_hour: Words processed per hour
            project_code: Project code
            job_id: Job ID
        
        Returns:
            Charge dictionary
        """
        # Calculate hours (rounded up to nearest 0.5)
        hours = word_count / words_per_hour
        hours = math.ceil(hours / 0.5) * 0.5
        
        return {
            "Project Code": project_code,
            "Job ID": job_id,
            "Service": "Formatting",
            "Language Pair": language_pair,
            "Quantity": hours,
            "Unit": "hours",
            "Rate": hourly_rate,
            "Amount": round(hours * hourly_rate, 2)
        }
    
    def generate_pm_charge(
        self,
        hours: float,
        hourly_rate: float = 65.0,
        project_code: str = "",
        job_id: str = ""
    ) -> Dict[str, Any]:
        """
        Generate Project Management charge
        
        Args:
            hours: Number of PM hours
            hourly_rate: Hourly rate for PM
            project_code: Project code
            job_id: Job ID
        
        Returns:
            Charge dictionary
        """
        return {
            "Project Code": project_code,
            "Job ID": job_id,
            "Service": "Project Management",
            "Language Pair": "",
            "Quantity": hours,
            "Unit": "hours",
            "Rate": hourly_rate,
            "Amount": round(hours * hourly_rate, 2)
        }
    
    def generate_charges_for_job(
        self,
        job_data: Dict[str, Any],
        charge_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate all charges for a single job
        
        Args:
            job_data: Dictionary with job information:
                - project_code: Project code
                - job_id: Job ID
                - language_pair: Language pair
                - word_count: Total word count
                - tm_fuzzy_count: Fuzzy match word count (optional)
                - tm_exact_count: Exact match word count (optional)
                - formatting_hours: Formatting hours (optional, calculated if not provided)
                - pm_hours: PM hours (optional)
            charge_types: List of charge types to generate (default: all)
        
        Returns:
            List of charge dictionaries
        """
        if charge_types is None:
            charge_types = ["Translation", "TM_Fuzzy", "TM_Exact", "Formatting"]
        
        charges = []
        
        project_code = job_data.get("project_code", "")
        job_id = job_data.get("job_id", "")
        language_pair = job_data.get("language_pair", "")
        word_count = job_data.get("word_count", 0)
        
        # Translation charge
        if "Translation" in charge_types and word_count > 0:
            charge = self.generate_translation_charge(
                word_count, language_pair, project_code, job_id
            )
            charges.append(charge)
        
        # TM Fuzzy charge
        if "TM_Fuzzy" in charge_types:
            fuzzy_count = job_data.get("tm_fuzzy_count", 0)
            if fuzzy_count > 0:
                charge = self.generate_tm_fuzzy_charge(
                    fuzzy_count, language_pair, project_code, job_id
                )
                charges.append(charge)
        
        # TM Exact charge
        if "TM_Exact" in charge_types:
            exact_count = job_data.get("tm_exact_count", 0)
            if exact_count > 0:
                charge = self.generate_tm_exact_charge(
                    exact_count, language_pair, project_code, job_id
                )
                charges.append(charge)
        
        # Formatting charge
        if "Formatting" in charge_types and word_count > 0:
            formatting_hours = job_data.get("formatting_hours")
            if formatting_hours is None:
                # Calculate based on word count
                charge = self.generate_formatting_charge(
                    word_count, language_pair, project_code=project_code, job_id=job_id
                )
            else:
                # Use provided hours
                hourly_rate = job_data.get("formatting_rate", 55.0)
                charge = {
                    "Project Code": project_code,
                    "Job ID": job_id,
                    "Service": "Formatting",
                    "Language Pair": language_pair,
                    "Quantity": formatting_hours,
                    "Unit": "hours",
                    "Rate": hourly_rate,
                    "Amount": round(formatting_hours * hourly_rate, 2)
                }
            charges.append(charge)
        
        # PM charge
        if "PM" in charge_types:
            pm_hours = job_data.get("pm_hours", 0)
            if pm_hours > 0:
                pm_rate = job_data.get("pm_rate", 65.0)
                charge = self.generate_pm_charge(
                    pm_hours, pm_rate, project_code, job_id
                )
                charges.append(charge)
        
        return charges
    
    def export_charges_to_excel(
        self,
        charges_by_job: Dict[str, List[Dict[str, Any]]],
        output_path: str,
        worksheet_prefix: str = "Sub_",
        worksheet_suffix: str = "_Charges"
    ) -> Tuple[List[str], List[str]]:
        """
        Export charges to Excel with separate worksheets per job
        
        Args:
            charges_by_job: Dictionary mapping job IDs to charge lists
            output_path: Path to save Excel file
            worksheet_prefix: Prefix for worksheet names
            worksheet_suffix: Suffix for worksheet names
        
        Returns:
            Tuple of (successful_job_ids, failed_job_ids)
        """
        successful = []
        failed = []
        
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                for job_id, charges in charges_by_job.items():
                    try:
                        # Create DataFrame from charges
                        df = pd.DataFrame(charges)
                        
                        # Create worksheet name
                        ws_name = f"{worksheet_prefix}{job_id}{worksheet_suffix}"
                        ws_name = ws_name[:31]  # Excel limit
                        
                        # Write to worksheet
                        df.to_excel(writer, sheet_name=ws_name, index=False)
                        successful.append(job_id)
                    
                    except Exception as e:
                        print(f"Error exporting charges for job {job_id}: {e}")
                        failed.append(job_id)
            
            print(f"Exported charges for {len(successful)} job(s)")
            return successful, failed
        
        except Exception as e:
            print(f"Error exporting charges to Excel: {e}")
            return [], list(charges_by_job.keys())


# Convenience functions
def create_charges_engine(rates_file: Optional[str] = None) -> ChargesEngine:
    """Create a new charges engine instance"""
    return ChargesEngine(rates_file)


def generate_job_charges(
    job_data: Dict[str, Any],
    rates_file: Optional[str] = None,
    charge_types: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Generate charges for a single job"""
    engine = ChargesEngine(rates_file)
    return engine.generate_charges_for_job(job_data, charge_types)


# Example usage
if __name__ == "__main__":
    # Create engine
    engine = ChargesEngine()
    
    # Example job data
    job_data = {
        "project_code": "TEST001",
        "job_id": "12345",
        "language_pair": "en-US > fr-FR",
        "word_count": 1500,
        "tm_fuzzy_count": 200,
        "tm_exact_count": 100
    }
    
    # Generate charges
    charges = engine.generate_charges_for_job(job_data)
    
    print(f"Generated {len(charges)} charges:")
    for charge in charges:
        print(f"  - {charge['Service']}: {charge['Quantity']} {charge['Unit']} @ ${charge['Rate']} = ${charge['Amount']}")
