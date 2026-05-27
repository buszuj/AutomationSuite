"""
Language Normalization Layer
Maps language names from different sources (QuoteMe, Rate Cards) to standardized formats
Supports ISO codes and custom user-defined mappings
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class LanguageNormalizer:
    """Normalizes language names across different data sources"""
    
    def __init__(self):
        self.core_path = Path(__file__).parent
        self.iso_codes_file = self.core_path / "languages_iso_codes.json"
        self.mapping_config_file = self.core_path / "language_mapping.json"
        
        # Load ISO codes and custom mappings
        self.iso_languages = self._load_iso_languages()
        self.custom_mappings = self._load_custom_mappings()
        
        # Build lookup tables
        self.name_to_iso = {}  # "Polish" → "pl-PL"
        self.iso_to_name = {}  # "pl-PL" → "Polish"
        self.display_name_to_iso = {}  # "Polish (Poland)" → "pl-PL"
        self._build_lookup_tables()
    
    def _load_iso_languages(self) -> list:
        """Load ISO language codes from JSON"""
        try:
            if self.iso_codes_file.exists():
                with open(self.iso_codes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("languages", [])
            return []
        except Exception as e:
            print(f"Error loading ISO languages: {e}")
            return []
    
    def _load_custom_mappings(self) -> dict:
        """Load custom user-defined language mappings"""
        try:
            if self.mapping_config_file.exists():
                with open(self.mapping_config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("custom_mappings", {})
            return {}
        except Exception as e:
            print(f"Error loading custom mappings: {e}")
            return {}
    
    def _build_lookup_tables(self):
        """Build lookup tables from ISO data"""
        for lang_entry in self.iso_languages:
            code = lang_entry.get("code", "")
            language = lang_entry.get("language", "")
            display_name = lang_entry.get("display_name", "")
            
            if code and language:
                # Map language name to ISO code (prefer country-specific versions)
                if language not in self.name_to_iso:
                    self.name_to_iso[language] = code
                
                # Map ISO code to language name
                self.iso_to_name[code] = language
                
                # Map display name (with country) to ISO code
                if display_name:
                    self.display_name_to_iso[display_name] = code
    
    def normalize(self, language_input: str, source_type: str = "auto") -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Normalize a language name to standard format.
        
        Args:
            language_input: Language name from any source (e.g., "Polish", "Polish (Poland)", "pl", "pl-PL")
            source_type: Type of source - "auto", "quoteme", "ratecard", "iso"
            
        Returns:
            Tuple of (iso_code, language_name, display_name) or (None, None, None) if not found
        """
        if not language_input or not language_input.strip():
            return None, None, None
        
        language_input = language_input.strip()
        
        # Check custom mappings first
        if language_input in self.custom_mappings:
            mapping = self.custom_mappings[language_input]
            return (
                mapping.get("iso_code"),
                mapping.get("language_name"),
                mapping.get("display_name")
            )
        
        # Try exact match on display_name (e.g., "Polish (Poland)")
        if language_input in self.display_name_to_iso:
            iso_code = self.display_name_to_iso[language_input]
            lang_entry = self._get_iso_entry(iso_code)
            if lang_entry:
                return (
                    iso_code,
                    lang_entry.get("language"),
                    lang_entry.get("display_name")
                )
        
        # Try exact match on language name (e.g., "Polish")
        if language_input in self.name_to_iso:
            iso_code = self.name_to_iso[language_input]
            lang_entry = self._get_iso_entry(iso_code)
            if lang_entry:
                return (
                    iso_code,
                    lang_entry.get("language"),
                    lang_entry.get("display_name")
                )
        
        # Try ISO code match (e.g., "pl", "pl-PL")
        if language_input in self.iso_to_name:
            iso_code = language_input
            lang_entry = self._get_iso_entry(iso_code)
            if lang_entry:
                return (
                    iso_code,
                    lang_entry.get("language"),
                    lang_entry.get("display_name")
                )
        
        # Try fuzzy matching: strip country part and match
        if "(" in language_input and ")" in language_input:
            # Input like "Polish (Poland)" - try just "Polish"
            base_name = language_input.split("(")[0].strip()
            if base_name in self.name_to_iso:
                iso_code = self.name_to_iso[base_name]
                lang_entry = self._get_iso_entry(iso_code)
                if lang_entry:
                    return (
                        iso_code,
                        lang_entry.get("language"),
                        lang_entry.get("display_name")
                    )
        
        # Try case-insensitive match
        for display_name, iso_code in self.display_name_to_iso.items():
            if display_name.lower() == language_input.lower():
                lang_entry = self._get_iso_entry(iso_code)
                if lang_entry:
                    return (
                        iso_code,
                        lang_entry.get("language"),
                        lang_entry.get("display_name")
                    )
        
        return None, None, None
    
    def _get_iso_entry(self, iso_code: str) -> Optional[dict]:
        """Get ISO language entry by code"""
        for entry in self.iso_languages:
            if entry.get("code") == iso_code:
                return entry
        return None
    
    def get_all_languages(self) -> List[Dict]:
        """Get all available language options (display names)"""
        result = []
        seen = set()
        
        for lang_entry in self.iso_languages:
            display_name = lang_entry.get("display_name", "")
            if display_name and display_name not in seen:
                seen.add(display_name)
                result.append({
                    "iso_code": lang_entry.get("code"),
                    "language_name": lang_entry.get("language"),
                    "display_name": display_name
                })
        
        return sorted(result, key=lambda x: x["display_name"])
    
    def add_custom_mapping(self, input_name: str, iso_code: str, language_name: str, display_name: str) -> bool:
        """
        Add or update a custom language mapping
        
        Args:
            input_name: The input string to map from (e.g., "Polish", "pl-PL")
            iso_code: ISO language code
            language_name: Base language name
            display_name: Display name with country
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.custom_mappings[input_name] = {
                "iso_code": iso_code,
                "language_name": language_name,
                "display_name": display_name
            }
            self._save_custom_mappings()
            return True
        except Exception as e:
            print(f"Error adding custom mapping: {e}")
            return False
    
    def remove_custom_mapping(self, input_name: str) -> bool:
        """Remove a custom mapping"""
        try:
            if input_name in self.custom_mappings:
                del self.custom_mappings[input_name]
                self._save_custom_mappings()
                return True
            return False
        except Exception as e:
            print(f"Error removing custom mapping: {e}")
            return False
    
    def _save_custom_mappings(self):
        """Save custom mappings to JSON file"""
        try:
            data = {
                "description": "Custom language mappings for QuoteMe and Rate Card normalization",
                "custom_mappings": self.custom_mappings
            }
            with open(self.mapping_config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving custom mappings: {e}")
    
    def get_custom_mappings(self) -> Dict:
        """Get all custom mappings"""
        return self.custom_mappings.copy()
    
    def normalize_quoteme_language_pair(self, quoteme_lp: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        """
        Normalize a QuoteMe language pair like "English (United States) > Polish (Poland)"
        
        Returns:
            Tuple of (source_iso, source_display, target_iso, target_display)
        """
        if ">" not in quoteme_lp:
            return None, None, None, None
        
        source_str, target_str = quoteme_lp.split(">", 1)
        source_str = source_str.strip()
        target_str = target_str.strip()
        
        source_iso, source_lang, source_display = self.normalize(source_str)
        target_iso, target_lang, target_display = self.normalize(target_str)
        
        return source_iso, source_display, target_iso, target_display


if __name__ == "__main__":
    # Test the normalizer
    normalizer = LanguageNormalizer()
    
    print("Testing Language Normalizer:")
    print()
    
    test_cases = [
        "Polish",
        "Polish (Poland)",
        "pl",
        "pl-PL",
        "English (United States)",
        "German (Germany)",
        "Spanish",
        "Chinese (Simplified)"
    ]
    
    for test in test_cases:
        iso, lang, display = normalizer.normalize(test)
        print(f"{test:30} → ISO: {iso:8} | Lang: {lang:20} | Display: {display}")
    
    print("\nTesting Language Pair Normalization:")
    lp = "English (United States) > Polish (Poland)"
    s_iso, s_disp, t_iso, t_disp = normalizer.normalize_quoteme_language_pair(lp)
    print(f"{lp}")
    print(f"  Source: {s_iso} - {s_disp}")
    print(f"  Target: {t_iso} - {t_disp}")
