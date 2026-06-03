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
import re


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
        
        # Load service classification (FT vs BT vs Fee)
        self._ft_services = set()
        self._bt_services = set()
        self._fee_services = set()
        self._load_service_classification()
    
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
                    else:
                        # Backward compatibility: file might be old format without 'mappings' wrapper
                        # Filter out metadata and structural keys
                        result = {k: v for k, v in data.items() if not k.startswith("_") and k not in ["description", "account"]}
                        print(f"[DEBUG] Using old format - found {len(result)} service mappings: {list(result.keys())}")
                    
                    # Apply Hourly defaults: Div=1000, Inc=0.5, Min=1
                    for service_name, config in result.items():
                        if config.get("service_type") == "Hourly":
                            # Set defaults only if not already specified
                            if "divider" not in config or config["divider"] is None:
                                config["divider"] = 1000
                            if "increment" not in config or config["increment"] is None:
                                config["increment"] = 0.5
                            if "minimum" not in config or config["minimum"] is None:
                                config["minimum"] = 1
                            print(f"[DEBUG] Applied Hourly defaults to '{service_name}': Div={config['divider']}, Inc={config['increment']}, Min={config['minimum']}")
                    
                    return result
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
        return self.get_service_config_from_mapping(mapping, service_name)

    def get_service_config_from_mapping(self, mapping: Dict[str, Dict[str, Any]], service_name: str) -> Optional[Dict[str, Any]]:
        """Get service config from an already-loaded mapping using resilient key matching."""
        resolved_key = self.resolve_mapping_key(mapping, service_name)
        if resolved_key:
            return mapping.get(resolved_key)
        return None

    def resolve_mapping_key(self, mapping: Dict[str, Dict[str, Any]], service_name: str) -> Optional[str]:
        """
        Resolve a workflow service name to a key in account mapping.
        Handles exact/case-insensitive matches, canonical-name matches, and normalized token matches.
        """
        if not mapping or not service_name:
            return None

        # 1) Exact key match
        if service_name in mapping:
            return service_name

        candidate_keys = [k for k in mapping.keys() if not str(k).startswith("_")]
        service_lower = service_name.lower().strip()

        # 2) Case-insensitive exact match
        for key in candidate_keys:
            if key.lower().strip() == service_lower:
                return key

        # 3) Canonical match (best signal when naming variants differ)
        service_canonical = self._find_canonical_service_name(service_name)
        if service_canonical:
            for key in candidate_keys:
                key_canonical = self._find_canonical_service_name(key)
                if key_canonical and key_canonical == service_canonical:
                    return key

        # 4) Normalized token match (remove punctuation/spaces/casing)
        service_norm = re.sub(r"[^a-z0-9]", "", service_lower)
        if service_norm:
            for key in candidate_keys:
                key_norm = re.sub(r"[^a-z0-9]", "", key.lower().strip())
                if key_norm == service_norm:
                    return key

        # 5) Last-resort containment checks on normalized strings
        for key in candidate_keys:
            key_norm = re.sub(r"[^a-z0-9]", "", key.lower().strip())
            if service_norm and key_norm and (service_norm in key_norm or key_norm in service_norm):
                return key

        return None
    
    def update_service_config(self, account_name: str, service_name: str, config: Dict[str, Any]):
        """Update configuration for a specific service"""
        mapping = self.load_mapping(account_name)
        mapping[service_name] = config
        self.save_mapping(account_name, mapping)
    
    # ──────────────────────────────────────────────────────────────────────────
    # Min Fee Helper Methods
    # ──────────────────────────────────────────────────────────────────────────
    
    def is_ft_service(self, service_name: str) -> bool:
        """
        Check if a service is a Front Translation (FT) service.
        Uses canonical service classification for reliable matching.
        """
        # Try to find matching canonical service
        canonical_name = self._find_canonical_service_name(service_name)
        if canonical_name and canonical_name in self._ft_services:
            return True
        return False
    
    def is_bt_service(self, service_name: str) -> bool:
        """
        Check if a service is a Back Translation (BT) service.
        Uses canonical service classification for reliable matching.
        """
        # Try to find matching canonical service
        canonical_name = self._find_canonical_service_name(service_name)
        if canonical_name and canonical_name in self._bt_services:
            return True
        return False
    
    def is_fee_service(self, service_name: str) -> bool:
        """
        Check if a service is a Fee service.
        Uses canonical service classification for reliable matching.
        """
        # Try to find matching canonical service
        canonical_name = self._find_canonical_service_name(service_name)
        if canonical_name and canonical_name in self._fee_services:
            return True
        return False
    
    def _load_service_classification(self):
        """Load service classification (FT/BT/Fee) from canonical mapping file"""
        classification_file = self.core_path / "service_classification.json"
        
        try:
            if classification_file.exists():
                with open(classification_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._ft_services = set(data.get("ft_services", []))
                    self._bt_services = set(data.get("bt_services", []))
                    self._fee_services = set(data.get("fee_services", []))
                    print(f"[DEBUG] Loaded service classification: {len(self._ft_services)} FT, {len(self._bt_services)} BT, {len(self._fee_services)} Fee")
            else:
                print(f"[DEBUG] WARNING: service_classification.json not found at {classification_file}")
                # Fallback to empty sets
                self._ft_services = set()
                self._bt_services = set()
                self._fee_services = set()
        except Exception as e:
            print(f"[DEBUG] ERROR loading service_classification.json: {e}")
            self._ft_services = set()
            self._bt_services = set()
            self._fee_services = set()
    
    def _find_canonical_service_name(self, service_name: str) -> Optional[str]:
        """
        Find the canonical service name that matches the given service name.
        Handles variations like 'MT full EditProof' vs 'MT Full EditProof'
        Uses case-insensitive and partial matching.
        
        Args:
            service_name: The service name to match (from rate card or workflow)
            
        Returns:
            Canonical service name if found, None otherwise
        """
        if not service_name:
            return None
        
        service_lower = service_name.lower().strip()
        
        # First try exact match (case-insensitive)
        for canonical in self._ft_services | self._bt_services | self._fee_services:
            if canonical.lower() == service_lower:
                return canonical
        
        # Then try partial matching with common variations
        # Remove extra spaces and check for substring matches
        service_normalized = ' '.join(service_lower.split())
        
        for canonical in self._ft_services | self._bt_services | self._fee_services:
            canonical_lower = canonical.lower()
            # Exact match after normalization
            if service_normalized == canonical_lower:
                return canonical
            # Substring match (service name contains canonical or vice versa)
            if canonical_lower in service_normalized or service_normalized in canonical_lower:
                return canonical
        
        return None
    
    def get_min_fee_threshold_from_file(self, account_name: str, rate_card_name: str, min_fee_type: str) -> Optional[float]:
        """
        Load min fee threshold from file.
        
        Args:
            account_name: Account name
            rate_card_name: Rate card name
            min_fee_type: "FT_Min" or "BT_Min"
            
        Returns:
            Min fee threshold value or None if not set
        """
        try:
            from service_mapper import ServiceMapper
            mapper = ServiceMapper()
            thresholds = mapper.load_min_fee_thresholds(account_name, rate_card_name)
            return thresholds.get(min_fee_type)
        except Exception as e:
            print(f"[DEBUG] Error loading min fee threshold: {e}")
            return None

