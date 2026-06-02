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
        
        SAFETY: Verifies that loaded mapping belongs to requested account
        to prevent cross-account data mixing.
        
        Returns:
            Dict mapping service_name -> {
                "fields": [list of field names],
                "service_type": "Word|Hourly|Fee",
                "divider": float (if hourly),
                "increment": float (if hourly),
                "minimum": float (if hourly)
            }
        """
        mapping_file = self.get_account_mapping_path(account_name)
        try:
            print(f"\n[DEBUG] Loading mapping for account '{account_name}'")
            print(f"[DEBUG] Mapping file path: {mapping_file}")
            
            if mapping_file.exists():
                print(f"[DEBUG] File exists! Loading...")
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[DEBUG] File contents keys: {list(data.keys())}")
                    
                    # SAFETY CHECK: Verify loaded mapping belongs to this account
                    # NOTE: Old files may not have 'account' field - allow them through
                    stored_account = data.get("account")
                    print(f"[DEBUG] Stored account in file: {stored_account}")
                    
                    if stored_account is not None and stored_account != account_name:
                        print(f"[DEBUG] WARNING: Account mismatch! Expected '{account_name}', got '{stored_account}'")
                        return {}
                    
                    # Support both old format (direct mappings) and new format (nested under 'mappings')
                    if "mappings" in data:
                        result = data.get("mappings", {})
                        print(f"[DEBUG] Using new format - found {len(result)} service mappings: {list(result.keys())}")
                        return result
                    else:
                        # Backward compatibility: file might be old format without 'mappings' wrapper
                        # Filter out metadata and structural keys
                        mappings = {k: v for k, v in data.items() if not k.startswith("_") and k not in ["description", "account"]}
                        print(f"[DEBUG] Using old format - found {len(mappings)} service mappings: {list(mappings.keys())}")
                        return mappings
            else:
                print(f"[DEBUG] File does not exist!")
                return {}
        except Exception as e:
            print(f"[DEBUG] ERROR loading QuoteMe value mapping for account '{account_name}': {e}")
            import traceback
            traceback.print_exc()
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
    
    def calculate_service_value(self, word_count_data, service_config: Dict[str, Any]):
        """
        Calculate a service value based on service type.
        
        Args:
            word_count_data: WordCountData object from QuoteMe parser
            service_config: Dict with keys:
                - "service_type": "Word" | "Hourly" | "Fee" (default: "Word")
                - "fields": list of QuoteMe field names
                - "divider": float (if hourly)
                - "increment": float (if hourly)
                - "minimum": float (if hourly)
            
        Returns:
            Calculated service value (int for standard word count, calculated for Hourly, 0 placeholder for Fee)
        """
        service_type = service_config.get("service_type", "Word")
        
        # Extract base value from fields
        field_names = service_config.get("fields", [])
        total = 0
        for field_name in field_names:
            internal_field = self.field_mapping.get(field_name)
            if internal_field and hasattr(word_count_data, internal_field):
                total += getattr(word_count_data, internal_field, 0)
        
        # Handle different service types
        if service_type == "Hourly":
            # Apply hourly calculations: MAX(CEILING(total/divider, increment), minimum)
            divider = service_config.get("divider", 1.0)
            increment = service_config.get("increment", 1.0)
            minimum = service_config.get("minimum", 0)
            
            if divider > 0:
                import math
                value = total / divider
                # CEILING to nearest increment
                if increment > 0:
                    value = math.ceil(value / increment) * increment
                value = max(value, minimum)
                return int(value) if value == int(value) else value
            return total
            
        elif service_type == "Fee":
            # Fee services are calculated separately based on cumulative sum of other services
            # Return 0 as placeholder - actual calculation happens in populate_service_quantities
            return 0
            
        else:  # "Word" or default
            # Standard word count (sum of selected fields)
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
