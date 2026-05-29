"""
QuoteMe Value Mapper
Maps QuoteMe word count fields (context, fuzzy_100, etc.) to workflow services.
Supports combining multiple QuoteMe fields for a single service.
Per-account mapping configuration (shared across all workflows).
Supports hourly services with dividers, increments, and minimum values.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class QuoteMeValueMapper:
    """Manages mapping of QuoteMe word count fields to workflow services at account level"""
    
    def __init__(self):
        self.core_path = Path(__file__).parent
        
        # Available QuoteMe fields that can be mapped
        self.available_fields = [
            "Context Matches",
            "100% Matches",
            "Fuzzy Matches",
            "Repetitions",
            "New Words"
        ]
        
        # Internal field names (matching WordCountData attributes)
        self.field_mapping = {
            "Context Matches": "context",
            "100% Matches": "fuzzy_100",
            "Fuzzy Matches": "fuzzy_matches",
            "Repetitions": "repetitions",
            "New Words": "new_words"
        }
    
    def get_account_mapping_path(self, account_name: str) -> Path:
        """
        Get the path for account-level QuoteMe value mapping file.
        Mappings are shared across all workflows in the account.
        
        Structure: Core/accounts/{account}/quoteme_mappings.json
        
        Args:
            account_name: Account name (e.g., "PXL")
            
        Returns:
            Path to mapping file
        """
        mapping_dir = self.core_path / "accounts" / account_name
        mapping_dir.mkdir(parents=True, exist_ok=True)
        return mapping_dir / "quoteme_mappings.json"
    
    def load_mapping(self, account_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Load QuoteMe value mapping for a specific account.
        Mappings are shared across all workflows.
        
        Returns:
            Dict mapping service_name -> {
                "fields": [list of field names],
                "hourly": bool,
                "divider": float (if hourly),
                "increment": float (if hourly),
                "minimum": int (if hourly)
            }
        """
        mapping_file = self.get_account_mapping_path(account_name)
        try:
            if mapping_file.exists():
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("mappings", {})
            return {}
        except Exception as e:
            print(f"Error loading QuoteMe value mapping: {e}")
            return {}
    
    def save_mapping(self, account_name: str, mapping: Dict[str, Dict[str, Any]]):
        """
        Save QuoteMe value mapping for a specific account.
        Mappings are shared across all workflows.
        
        Args:
            account_name: Account name
            mapping: Dict of {
                service_name -> {
                    "fields": [field names],
                    "hourly": bool,
                    "divider": float,
                    "increment": float,
                    "minimum": int
                }
            }
        """
        mapping_file = self.get_account_mapping_path(account_name)
        try:
            data = {
                "description": f"QuoteMe value mapping for account {account_name} (shared across all workflows)",
                "account": account_name,
                "mappings": mapping
            }
            mapping_file.parent.mkdir(parents=True, exist_ok=True)
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving QuoteMe value mapping: {e}")
    
    def calculate_service_value(self, word_count_data, service_config: Dict[str, Any]) -> int:
        """
        Calculate a service value by summing specified QuoteMe fields.
        Applies hourly calculations if configured.
        
        Args:
            word_count_data: WordCountData object from QuoteMe parser
            service_config: Dict with keys:
                - "fields": list of QuoteMe field names
                - "hourly": bool (optional)
                - "divider": float (if hourly)
                - "increment": float (if hourly)
                - "minimum": int (if hourly)
            
        Returns:
            Calculated service value
        """
        # Extract base value from fields
        field_names = service_config.get("fields", [])
        total = 0
        for field_name in field_names:
            internal_field = self.field_mapping.get(field_name)
            if internal_field and hasattr(word_count_data, internal_field):
                total += getattr(word_count_data, internal_field, 0)
        
        # Apply hourly calculations if configured
        if service_config.get("hourly", False):
            divider = service_config.get("divider", 1.0)
            increment = service_config.get("increment", 1.0)
            minimum = service_config.get("minimum", 0)
            
            # Calculate: (base / divider) rounded to increment, with minimum
            if divider > 0:
                value = total / divider
                if increment > 0:
                    value = round(value / increment) * increment
                value = max(value, minimum)
                return int(value) if value == int(value) else value
        
        return total
    
    def get_service_config(self, account_name: str, service_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific service in an account"""
        mapping = self.load_mapping(account_name)
        return mapping.get(service_name)
    
    def update_service_config(self, account_name: str, service_name: str, config: Dict[str, Any]):
        """Update configuration for a specific service"""
        mapping = self.load_mapping(account_name)
        mapping[service_name] = config
        self.save_mapping(account_name, mapping)
