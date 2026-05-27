"""
Service Mapping Manager
Normalizes service names across rate cards to canonical service names.
Supports per-account, per-rate-card mapping configuration.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ServiceMapper:
    """Manages mapping of rate card services to canonical service names"""
    
    def __init__(self):
        self.core_path = Path(__file__).parent
        self.canonical_services_file = self.core_path / "canonical_services.json"
        self._service_cache = {}  # Initialize cache FIRST before loading
        self.canonical_services = self._load_canonical_services()
    
    def _load_canonical_services(self) -> List[str]:
        """Load canonical service names from JSON"""
        try:
            if self.canonical_services_file.exists():
                with open(self.canonical_services_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    services = data.get("canonical_services", [])
                    # Build cache for fast lookup (case-insensitive)
                    for service in services:
                        self._service_cache[service.lower()] = service
                    return services
            return []
        except Exception as e:
            print(f"Error loading canonical services: {e}")
            return []
    
    def is_canonical(self, service_name: str) -> bool:
        """Check if a service name is already canonical"""
        return service_name.lower() in self._service_cache
    
    def get_canonical_name(self, service_name: str) -> Optional[str]:
        """
        Get the canonical name for a service (case-insensitive).
        
        Returns:
            Canonical service name if found, None otherwise
        """
        return self._service_cache.get(service_name.lower())
    
    def find_exact_matches(self, rate_card_services: List[str]) -> Tuple[Dict[str, str], List[str]]:
        """
        Find exact matches between rate card services and canonical services.
        
        Args:
            rate_card_services: List of services from rate card
            
        Returns:
            Tuple of (matched_dict, unmapped_list)
            - matched_dict: {rate_card_service -> canonical_service}
            - unmapped_list: [rate_card_services with no match]
        """
        matched = {}
        unmapped = []
        
        for rc_service in rate_card_services:
            canonical = self.get_canonical_name(rc_service)
            if canonical:
                matched[rc_service] = canonical
            else:
                unmapped.append(rc_service)
        
        return matched, unmapped
    
    def get_account_mapping_path(self, account_name: str, rate_card_name: str) -> Path:
        """
        Get the path for account-specific service mapping file.
        
        Structure: Core/accounts/{account}/service_mappings/{rate_card_name}.json
        
        Args:
            account_name: Account name (e.g., "PXL")
            rate_card_name: Rate card name (e.g., "Menarini_RC")
            
        Returns:
            Path to mapping file
        """
        mapping_dir = self.core_path / "accounts" / account_name / "service_mappings"
        mapping_dir.mkdir(parents=True, exist_ok=True)
        return mapping_dir / f"{rate_card_name}.json"
    
    def load_mapping(self, account_name: str, rate_card_name: str) -> Dict[str, str]:
        """
        Load service mapping for a specific account and rate card.
        
        Returns:
            Dict mapping rate_card_service -> canonical_service
        """
        mapping_file = self.get_account_mapping_path(account_name, rate_card_name)
        try:
            if mapping_file.exists():
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("mappings", {})
            return {}
        except Exception as e:
            print(f"Error loading service mapping: {e}")
            return {}
    
    def save_mapping(self, account_name: str, rate_card_name: str, mapping: Dict[str, str]):
        """
        Save service mapping for a specific account and rate card.
        
        Args:
            account_name: Account name
            rate_card_name: Rate card name
            mapping: Dict of {rate_card_service -> canonical_service}
        """
        mapping_file = self.get_account_mapping_path(account_name, rate_card_name)
        try:
            data = {
                "description": f"Service mapping for {rate_card_name} under account {account_name}",
                "account": account_name,
                "rate_card": rate_card_name,
                "mappings": mapping
            }
            mapping_file.parent.mkdir(parents=True, exist_ok=True)
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving service mapping: {e}")
    
    def normalize_services(
        self, 
        rate_card_services: List[str],
        account_name: str = None,
        rate_card_name: str = None
    ) -> Tuple[Dict[str, str], List[str]]:
        """
        Normalize rate card services to canonical names.
        
        Process:
        1. Try exact matches (case-insensitive)
        2. Load saved mappings for this account/rate-card if provided
        3. Return unmapped services
        
        Args:
            rate_card_services: Services from rate card
            account_name: Optional account name to load saved mappings
            rate_card_name: Optional rate card name to load saved mappings
            
        Returns:
            Tuple of (normalized_mapping, unmapped_services)
            - normalized_mapping: {rate_card_service -> canonical_service}
            - unmapped_services: [services not mapped]
        """
        # First, find exact matches
        matched, unmapped = self.find_exact_matches(rate_card_services)
        
        # If account and rate card provided, load saved mappings
        saved_mapping = {}
        if account_name and rate_card_name:
            saved_mapping = self.load_mapping(account_name, rate_card_name)
        
        # Apply saved mappings to unmapped services
        final_mapping = matched.copy()
        remaining_unmapped = []
        
        for service in unmapped:
            if service in saved_mapping:
                final_mapping[service] = saved_mapping[service]
            else:
                remaining_unmapped.append(service)
        
        return final_mapping, remaining_unmapped
    
    def apply_service_mapping(self, rate_card: dict, mapping: Dict[str, str]) -> dict:
        """
        Apply service mapping to a rate card, renaming all services to canonical names.
        Also filters out metadata columns like "Iso Code".
        
        Args:
            rate_card: Rate card dict with languages and rates
            mapping: Dict of {old_service_name -> canonical_service_name}
            
        Returns:
            Modified rate card with normalized service names (metadata columns removed)
        """
        if "languages" not in rate_card:
            return rate_card
        
        # Columns to ignore (metadata, not services)
        ignore_columns = {"Iso Code", "iso code", "ISO Code", "ISO CODE"}
        
        mapped_card = rate_card.copy()
        mapped_languages = {}
        
        for language, lang_data in rate_card.get("languages", {}).items():
            if isinstance(lang_data, dict) and "rates" in lang_data:
                mapped_rates = {}
                for old_service, rate_value in lang_data["rates"].items():
                    # Skip ignored columns
                    if old_service in ignore_columns:
                        continue
                    # Use mapping if available, otherwise keep original
                    canonical_service = mapping.get(old_service, old_service)
                    mapped_rates[canonical_service] = rate_value
                
                mapped_languages[language] = {
                    **lang_data,
                    "rates": mapped_rates
                }
            else:
                mapped_languages[language] = lang_data
        
        mapped_card["languages"] = mapped_languages
        return mapped_card
    
    def get_unmapped_canonical_services(self) -> List[str]:
        """Get list of all canonical services that are not mapped yet"""
        return self.canonical_services.copy()
