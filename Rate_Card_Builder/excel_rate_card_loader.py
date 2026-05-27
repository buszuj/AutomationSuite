"""
Excel Rate Card Loader
Converts Excel rate card files to Rate Card Builder JSON format.
Supports rate cards from TheOneBP/RateCards directory.
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
import re


class ExcelRateCardLoader:
    """Load and convert Excel rate cards to JSON format."""
    
    # Map common service column names to standardized names
    SERVICE_NAME_MAPPING = {
        'Translation': 'Translation and Proofreading',
        'Translation/Proofreading': 'Translation and Proofreading',
        'Translation and Proofreading': 'Translation and Proofreading',
        'MT': 'MT full EditProof',
        'MT full': 'MT full EditProof',
        'MT full EditProof': 'MT full EditProof',
        'MT EditProof': 'MT full EditProof',
        'TM - Fuzzy': 'TM - Fuzzy Matches',
        'TM Fuzzy': 'TM - Fuzzy Matches',
        'TM - Fuzzy Matches': 'TM - Fuzzy Matches',
        'TM - Exact Matches': 'TM - Exact Matches',
        'TM - Exact': 'TM - Exact Matches',
        'TM Exact': 'TM - Exact Matches',
        'TM - Exact Match': 'TM - Exact Matches',
        'TM - Repetitions': 'TM - Repetitions',
        'TM Repetitions': 'TM - Repetitions',
        'Fuzzy Low': 'TM - Fuzzy Match Low',
        'Fuzzy Medium': 'TM - Fuzzy Match Medium',
        'Fuzzy High': 'TM - Fuzzy Match High',
    }
    
    def __init__(self, excel_file_path: str):
        """
        Initialize the loader with an Excel file.
        
        Args:
            excel_file_path: Path to the Excel rate card file
        """
        self.file_path = Path(excel_file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_file_path}")
        
        self.xls = pd.ExcelFile(self.file_path)
        self.sponsor_name = self.file_path.stem.replace('_RC', '')
    
    def load_rate_card(self) -> Dict:
        """
        Load and convert Excel rate card to JSON format.
        
        Returns:
            Dictionary with rate card data in JSON format
        """
        # Get the first sheet (or the sponsor-named sheet if it exists)
        sheet_name = self._get_sheet_name()
        df = pd.read_excel(self.file_path, sheet_name=sheet_name)
        
        # Process the dataframe
        languages, services, iso_codes = self._process_dataframe(df)
        
        # Build rate card structure
        rate_card = {
            "name": self.sponsor_name,
            "sponsor": self.sponsor_name,
            "services": services,
            "iso_codes": iso_codes,
            "languages": languages,
            "type": "itemized",
            "source": f"Excel: {self.file_path.name}"
        }
        
        return rate_card
    
    def _get_sheet_name(self) -> str:
        """Get the appropriate sheet name from the Excel file."""
        # Try to find a sheet named after the sponsor
        for sheet in self.xls.sheet_names:
            if sheet.lower() == self.sponsor_name.lower():
                return sheet
        
        # Otherwise use the first sheet
        return self.xls.sheet_names[0]
    
    def _process_dataframe(self, df: pd.DataFrame) -> Tuple[Dict, list, Dict]:
        """
        Process the dataframe to extract languages, services, and rates.
        
        Args:
            df: DataFrame with rate card data
            
        Returns:
            Tuple of (languages_dict, services_list, iso_codes_dict)
        """
        languages = {}
        services_set = set()
        iso_codes = {}
        
        # Identify language column (usually first column with language names)
        language_col = self._identify_language_column(df)
        
        if language_col is None:
            raise ValueError("Could not identify language column in Excel file")
        
        # Extract language names and process each row
        for idx, row in df.iterrows():
            language_name = str(row[language_col]).strip()
            
            # Skip empty rows and header-like rows
            if not language_name or language_name.lower() in ['language', 'language long', 'language name']:
                continue
            
            # Extract rates for this language
            rates = {}
            for col_name in df.columns:
                if col_name == language_col:
                    continue
                
                col_name_str = str(col_name).strip()
                
                # Normalize service name
                service_name = self._normalize_service_name(col_name_str)
                
                # Skip non-rate columns
                if not service_name:
                    continue
                
                # Extract rate value
                try:
                    rate_value = str(row[col_name]).strip()
                    # Skip empty cells and non-numeric values
                    if rate_value and rate_value.lower() not in ['nan', 'none', '']:
                        rates[service_name] = rate_value
                        services_set.add(service_name)
                except:
                    pass
            
            # Only add language if it has rates
            if rates:
                iso_code = self._get_iso_code(language_name)
                languages[language_name] = {
                    "iso_code": iso_code,
                    "rates": rates
                }
                iso_codes[language_name] = iso_code
        
        # Convert services set to sorted list
        services_list = sorted(list(services_set))
        
        return languages, services_list, iso_codes
    
    def _identify_language_column(self, df: pd.DataFrame) -> Optional[str]:
        """
        Identify which column contains language names.
        
        Args:
            df: DataFrame to search
            
        Returns:
            Column name if found, None otherwise
        """
        language_indicators = ['language', 'lang', 'source', 'from', 'language long']
        
        for col in df.columns:
            col_lower = str(col).lower()
            for indicator in language_indicators:
                if indicator in col_lower:
                    return col
        
        # Check first column
        if len(df) > 0:
            first_col_name = df.columns[0]
            first_value = str(df.iloc[0][first_col_name]).strip()
            # If first value looks like a language name, use this column
            if len(first_value) > 0 and not self._is_numeric_value(first_value):
                return first_col_name
        
        return None
    
    def _normalize_service_name(self, col_name: str) -> Optional[str]:
        """
        Normalize service column name to standard format.
        
        Args:
            col_name: Original column name
            
        Returns:
            Normalized service name or None if not a service column
        """
        col_name = str(col_name).strip()
        
        # Check if this looks like a service column
        if self._is_numeric_value(col_name):
            return None
        
        # Check mapping
        for key, value in self.SERVICE_NAME_MAPPING.items():
            if key.lower() in col_name.lower():
                return value
        
        # If it looks like a service name (not a language), keep it
        if len(col_name) > 2 and 'language' not in col_name.lower():
            return col_name
        
        return None
    
    def _is_numeric_value(self, value: str) -> bool:
        """Check if a value appears to be numeric."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _get_iso_code(self, language_name: str) -> str:
        """
        Get ISO code for a language (simplified version).
        
        Args:
            language_name: Language name
            
        Returns:
            ISO code if found, empty string otherwise
        """
        # Simplified ISO code extraction from language name
        # Could be enhanced with a lookup table
        
        # Extract country code from parentheses if present
        match = re.search(r'\(([^)]+)\)$', language_name)
        if match:
            country = match.group(1).strip()
            # Map country names to ISO codes (simplified)
            country_to_iso = {
                'United States': 'en-US',
                'United Kingdom': 'en-GB',
                'Canada': 'fr-CA',
                'Mexico': 'es-MX',
                'Spain': 'es-ES',
                'France': 'fr-FR',
                'Germany': 'de-DE',
                'Italy': 'it-IT',
                'China': 'zh-CN',
                'Japan': 'ja-JP',
                'Brazil': 'pt-BR',
                'India': 'hi-IN',
            }
            if country in country_to_iso:
                return country_to_iso[country]
        
        return ""


def load_excel_rate_card(file_path: str) -> Dict:
    """
    Convenience function to load an Excel rate card.
    
    Args:
        file_path: Path to Excel rate card file
        
    Returns:
        Rate card data in JSON format
    """
    loader = ExcelRateCardLoader(file_path)
    return loader.load_rate_card()


def find_excel_rate_cards(directory: str = None) -> list:
    """
    Find all Excel rate card files in a directory.
    
    Args:
        directory: Directory to search (defaults to TheOneBP/RateCards)
        
    Returns:
        List of (filename, filepath) tuples
    """
    if directory is None:
        # Default to TheOneBP RateCards directory
        rate_cards_dir = Path("d:/BP TECH/Python apps/REPOs/TheOneBP/RateCards")
    else:
        rate_cards_dir = Path(directory)
    
    if not rate_cards_dir.exists():
        return []
    
    excel_files = []
    for file_path in rate_cards_dir.glob("*.xlsx"):
        excel_files.append((file_path.name, str(file_path)))
    
    return sorted(excel_files, key=lambda x: x[0])
