"""
Language and ISO Code Helper Module
Provides utilities to load and work with language reference data.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional


class LanguageManager:
    """Manages language and ISO code data."""
    
    def __init__(self):
        """Initialize the language manager and load language data."""
        self._languages = None
        self._load_languages()
    
    def _load_languages(self):
        """Load languages from JSON file."""
        json_path = Path(__file__).parent / "languages_iso_codes.json"
        
        if not json_path.exists():
            raise FileNotFoundError(f"Language data file not found: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self._languages = data.get('languages', [])
    
    @property
    def languages(self) -> List[Dict]:
        """Get all languages."""
        return self._languages
    
    def get_all_codes(self) -> List[str]:
        """Get all language codes."""
        return [lang['code'] for lang in self._languages]
    
    def get_all_display_names(self) -> List[str]:
        """Get all display names sorted alphabetically."""
        names = [lang['display_name'] for lang in self._languages]
        return sorted(names)
    
    def get_by_code(self, code: str) -> Optional[Dict]:
        """Get language info by ISO code."""
        for lang in self._languages:
            if lang['code'].lower() == code.lower():
                return lang
        return None
    
    def get_by_language(self, language: str) -> List[Dict]:
        """Get all variants of a language."""
        results = []
        for lang in self._languages:
            if lang['language'].lower() == language.lower():
                results.append(lang)
        return sorted(results, key=lambda x: x['code'])
    
    def get_by_country(self, country: str) -> List[Dict]:
        """Get all languages by country."""
        results = []
        for lang in self._languages:
            if country.lower() in lang['country'].lower():
                results.append(lang)
        return sorted(results, key=lambda x: x['code'])
    
    def search(self, query: str) -> List[Dict]:
        """Search languages by code, language name, country, or display name."""
        query_lower = query.lower()
        results = []
        
        for lang in self._languages:
            if (query_lower in lang['code'].lower() or
                query_lower in lang['language'].lower() or
                query_lower in lang['country'].lower() or
                query_lower in lang['display_name'].lower()):
                results.append(lang)
        
        return results
    
    def update_language_code(self, old_code: str, new_code: str) -> bool:
        """Update an ISO code. Returns True if successful."""
        for lang in self._languages:
            if lang['code'].lower() == old_code.lower():
                lang['code'] = new_code
                self._save_languages()
                return True
        return False
    
    def update_language_name(self, code: str, new_name: str) -> bool:
        """Update a language name. Returns True if successful."""
        for lang in self._languages:
            if lang['code'].lower() == code.lower():
                lang['language'] = new_name
                # Also update display_name if it was derived from language name
                lang['display_name'] = f"{new_name} ({lang['country']})"
                self._save_languages()
                return True
        return False

    def add_or_update_language(self, code: str, language: str, country: str = "", display_name: Optional[str] = None) -> bool:
        """Add a new ISO record or update an existing one by code."""
        normalized_code = code.strip()
        normalized_language = language.strip()
        normalized_country = country.strip()
        normalized_display_name = display_name.strip() if display_name else ""

        if not normalized_code or not normalized_language:
            return False

        if not normalized_display_name:
            normalized_display_name = f"{normalized_language} ({normalized_country})" if normalized_country else normalized_language

        for lang in self._languages:
            if lang['code'].lower() == normalized_code.lower():
                lang['language'] = normalized_language
                lang['country'] = normalized_country
                lang['display_name'] = normalized_display_name
                self._save_languages()
                return True

        self._languages.append({
            'code': normalized_code,
            'language': normalized_language,
            'country': normalized_country,
            'display_name': normalized_display_name,
        })
        self._save_languages()
        return True
    
    def _save_languages(self):
        """Save languages back to JSON file."""
        json_path = Path(__file__).parent / "languages_iso_codes.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            data = {'languages': self._languages}
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_unique_languages(self) -> List[str]:
        """Get list of unique base languages."""
        languages = set()
        for lang in self._languages:
            languages.add(lang['language'])
        return sorted(languages)
    
    def get_unique_countries(self) -> List[str]:
        """Get list of unique countries."""
        countries = set()
        for lang in self._languages:
            if lang['country']:  # Skip empty countries
                countries.add(lang['country'])
        return sorted(countries)


# Create a singleton instance
_language_manager = None


def get_language_manager() -> LanguageManager:
    """Get or create the singleton language manager instance."""
    global _language_manager
    if _language_manager is None:
        _language_manager = LanguageManager()
    return _language_manager
