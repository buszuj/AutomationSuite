"""
Service Mapping Manager
Normalizes service names across rate cards to canonical service names.
Supports per-account, per-rate-card mapping configuration.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


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
    def _normalize_alias_key(self, service_name: str) -> str:
        """
            Normalize service alias for conflict detection.
            Keeps logic intentionally simple and deterministic.
        """
        return " ".join(str(service_name).strip().lower().split())

    def get_account_service_mapping_files(self, account_name: str) -> List[Path]:
        """
        Return all mapping files for an account under service_mappings.
        """
        mapping_dir = self.core_path / "accounts" / account_name / "service_mappings"
        if not mapping_dir.exists():
            return []
        return sorted(mapping_dir.glob("*.json"))

    def detect_account_mapping_conflicts(self, account_name: str) -> Dict[str, Any]:
        """
        Detect alias conflicts across all rate-card mapping files for an account.

        Conflict definition:
        The same normalized alias maps to more than one canonical service.

        Returns:
            {
            "has_conflicts": bool,
            "conflicts": {
                "<normalized_alias>": {
                "alias_variants": [original_alias_strings],
                "canonical_services": [canonical_names],
                "sources": [
                    {"rate_card": "<rate_card_name>", "alias": "<original_alias>", "canonical": "<canonical_name>"}
                ]
                }
            },
            "scanned_files": [file_names]
            }
        """
        alias_index: Dict[str, Dict[str, Any]] = {}
        scanned_files: List[str] = []

        for mapping_file in self.get_account_service_mapping_files(account_name):
            try:
                with open(mapping_file, "r", encoding="utf-8") as f:
                    payload = json.load(f)

                mappings = payload.get("mappings", {})
                if not isinstance(mappings, dict):
                    continue

                rate_card_name = payload.get("rate_card", mapping_file.stem)
                scanned_files.append(mapping_file.name)

                for raw_alias, canonical in mappings.items():
                    alias_norm = self._normalize_alias_key(raw_alias)
                    canonical_name = str(canonical).strip()
                    alias_display = str(raw_alias).strip()

                    if not alias_norm or not canonical_name:
                        continue

                    if alias_norm not in alias_index:
                        alias_index[alias_norm] = {
                            "alias_variants": set(),
                            "canonical_services": set(),
                            "sources": []
                        }

                    alias_index[alias_norm]["alias_variants"].add(alias_display)
                    alias_index[alias_norm]["canonical_services"].add(canonical_name)
                    alias_index[alias_norm]["sources"].append({
                        "rate_card": rate_card_name,
                        "alias": alias_display,
                        "canonical": canonical_name
                    })

            except Exception as e:
                print(f"Error scanning mapping file for conflicts ({mapping_file.name}): {e}")

        conflicts: Dict[str, Any] = {}
        for alias_norm, data in alias_index.items():
            canonical_set: Set[str] = data["canonical_services"]
            if len(canonical_set) > 1:
                conflicts[alias_norm] = {
                    "alias_variants": sorted(list(data["alias_variants"])),
                    "canonical_services": sorted(list(canonical_set)),
                    "sources": data["sources"]
                }

        return {
            "has_conflicts": len(conflicts) > 0,
            "conflicts": conflicts,
            "scanned_files": scanned_files
        }         
    
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
        account_name: Optional[str] = None,
        rate_card_name: Optional[str] = None
    ) -> Tuple[Dict[str, str], List[str], Dict[str, Any]]:
        """
        Normalize rate card services to canonical names.
        
        Process:
        1. Try exact matches (case-insensitive)
        2. Load saved mappings for this account/rate-card if provided
        3. Detect mapping conflicts for the account
        4. Return unmapped services plus conflict report
        
        Args:
            rate_card_services: Services from rate card
            account_name: Optional account name to load saved mappings
            rate_card_name: Optional rate card name to load saved mappings
            
        Returns:
            Tuple of (normalized_mapping, unmapped_services, conflict_report)
            - normalized_mapping: {rate_card_service -> canonical_service}
            - unmapped_services: [services not mapped]
            - conflict_report: conflict scan result dict
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
        
        conflict_report = {
            "has_conflicts": False,
            "conflicts": {},
            "scanned_files": []
        }
        if account_name:
            conflict_report = self.detect_account_mapping_conflicts(account_name)
        
        return final_mapping, remaining_unmapped, conflict_report
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
    
    # ──────────────────────────────────────────────────────────────────────────
    # Entity Service Alias Management (entity-specific names for canonical services)
    # ──────────────────────────────────────────────────────────────────────────
    
    def get_entity_service_aliases_path(self, entity_name: str) -> Path:
        """
        Get the path for entity service aliases file.
        
        Structure: Core/entity_service_aliases/{entity_name}.json
        
        Args:
            entity_name: Entity name (e.g., "PXL", "MENARINI", etc.)
            
        Returns:
            Path to aliases file
        """
        aliases_dir = self.core_path / "entity_service_aliases"
        aliases_dir.mkdir(parents=True, exist_ok=True)
        return aliases_dir / f"{entity_name}.json"
    
    def load_entity_service_aliases(self, entity_name: str) -> Dict[str, str]:
        """
        Load service aliases for an entity.
        
        Returns:
            Dict mapping canonical_service -> entity_specific_name
        """
        aliases_file = self.get_entity_service_aliases_path(entity_name)
        try:
            if aliases_file.exists():
                with open(aliases_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("aliases", {})
            return {}
        except Exception as e:
            print(f"Error loading entity service aliases for {entity_name}: {e}")
            return {}
    
    def save_entity_service_aliases(self, entity_name: str, aliases: Dict[str, str]):
        """
        Save service aliases for an entity.
        
        Args:
            entity_name: Entity name
            aliases: Dict mapping canonical_service -> entity_specific_name
        """
        aliases_file = self.get_entity_service_aliases_path(entity_name)
        try:
            data = {
                "description": f"Service aliases for entity {entity_name}",
                "entity": entity_name,
                "aliases": aliases
            }
            aliases_file.parent.mkdir(parents=True, exist_ok=True)
            with open(aliases_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[DEBUG] Saved aliases for {entity_name}: {len(aliases)} mappings")
        except Exception as e:
            print(f"Error saving entity service aliases for {entity_name}: {e}")
    
    def add_canonical_service(self, service_name: str) -> bool:
        """
        Add a new canonical service to the master list.
        
        Args:
            service_name: New canonical service name
            
        Returns:
            True if added successfully, False if already exists
        """
        if self.is_canonical(service_name):
            print(f"Service '{service_name}' already exists in canonical services")
            return False
        
        try:
            # Load the file
            with open(self.canonical_services_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Add to list (maintain alphabetical order)
            services = data.get("canonical_services", [])
            services.append(service_name)
            services.sort()
            data["canonical_services"] = services
            
            # Save back
            with open(self.canonical_services_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Update in-memory cache
            self.canonical_services = services
            self._service_cache[service_name.lower()] = service_name
            
            print(f"[DEBUG] Added canonical service: {service_name}")
            return True
        except Exception as e:
            print(f"Error adding canonical service: {e}")
            return False
    
    def set_entity_service_alias(self, entity_name: str, canonical_service: str, entity_name_alias: str) -> bool:
        """
        Set an alias (entity-specific name) for a canonical service.
        
        Args:
            entity_name: Entity name (e.g., "PXL")
            canonical_service: Canonical service name
            entity_name_alias: Entity-specific name for this service
            
        Returns:
            True if successful
        """
        if not self.is_canonical(canonical_service):
            print(f"'{canonical_service}' is not a canonical service")
            return False
        
        # Load current aliases
        aliases = self.load_entity_service_aliases(entity_name)
        
        # Update
        aliases[canonical_service] = entity_name_alias
        
        # Save
        self.save_entity_service_aliases(entity_name, aliases)
        return True
    
    # ──────────────────────────────────────────────────────────────────────────
    # Min Fee Thresholds Management (per rate card, per account)
    # ──────────────────────────────────────────────────────────────────────────
    
    def get_min_fee_thresholds_path(self, account_name: str, rate_card_name: str) -> Path:
        """
        Get the path for min fee thresholds file.
        
        Structure: Core/accounts/{account_name}/min_fee_thresholds/{rate_card_name}.json
        
        Args:
            account_name: Account name (e.g., "PXL", "ICON")
            rate_card_name: Rate card name (e.g., "Menarini_RC")
            
        Returns:
            Path to min fee thresholds file
        """
        thresholds_dir = self.core_path / "accounts" / account_name / "min_fee_thresholds"
        thresholds_dir.mkdir(parents=True, exist_ok=True)
        return thresholds_dir / f"{rate_card_name}.json"
    
    def load_min_fee_thresholds(self, account_name: str, rate_card_name: str) -> Dict[str, float]:
        """
        Load min fee thresholds for a rate card.
        
        Returns:
            Dict with 'FT_Min' and 'BT_Min' keys (both optional)
            Example: {"FT_Min": 90.0, "BT_Min": 90.0}
        """
        thresholds_file = self.get_min_fee_thresholds_path(account_name, rate_card_name)
        try:
            if thresholds_file.exists():
                with open(thresholds_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("thresholds", {})
            return {}
        except Exception as e:
            print(f"[DEBUG] Error loading min fee thresholds: {e}")
            return {}
    
    def save_min_fee_thresholds(self, account_name: str, rate_card_name: str, thresholds: Dict[str, float]):
        """
        Save min fee thresholds for a rate card.
        
        Args:
            account_name: Account name
            rate_card_name: Rate card name
            thresholds: Dict with 'FT_Min' and/or 'BT_Min' entries
        """
        thresholds_file = self.get_min_fee_thresholds_path(account_name, rate_card_name)
        try:
            data = {
                "description": f"Min fee thresholds for {rate_card_name} in account {account_name}",
                "rate_card": rate_card_name,
                "account": account_name,
                "thresholds": thresholds
            }
            thresholds_file.parent.mkdir(parents=True, exist_ok=True)
            with open(thresholds_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[DEBUG] Saved min fee thresholds for {rate_card_name}: {thresholds}")
        except Exception as e:
            print(f"[DEBUG] Error saving min fee thresholds: {e}")
    
    def min_fee_exists(self, account_name: str, rate_card_name: str) -> bool:
        """Check if min fee thresholds are already configured for this rate card."""
        thresholds_file = self.get_min_fee_thresholds_path(account_name, rate_card_name)
        return thresholds_file.exists()

