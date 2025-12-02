"""
Language Pair Manager Module
Handles language pair operations and validation.
"""

from typing import List, Tuple, Optional


class LanguagePairManager:
    """Manages language pairs (LPs) for translation projects."""
    
    def __init__(self):
        """Initialize LanguagePairManager."""
        self.language_pairs: List[str] = []
    
    def add_language_pair(
        self,
        source_language: str,
        target_language: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Add a language pair.
        
        Args:
            source_language: Source language
            target_language: Target language
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        # Validate inputs
        if not source_language or source_language == "Select Source Language":
            return False, "Please select a valid source language."
        
        if not target_language or target_language == "Select Target Language":
            return False, "Please select a valid target language."
        
        # Create LP string
        lp = f"{source_language} into {target_language}"
        
        # Check for duplicates
        if lp in self.language_pairs:
            return False, f"The language pair '{lp}' already exists."
        
        # Add to list
        self.language_pairs.append(lp)
        return True, None
    
    def remove_language_pair(self, index: int) -> bool:
        """
        Remove a language pair by index.
        
        Args:
            index: Index of the language pair to remove
        
        Returns:
            True if successful, False if index out of range
        """
        if 0 <= index < len(self.language_pairs):
            self.language_pairs.pop(index)
            return True
        return False
    
    def get_language_pair(self, index: int) -> Optional[str]:
        """
        Get a language pair by index.
        
        Args:
            index: Index of the language pair
        
        Returns:
            Language pair string or None if index out of range
        """
        if 0 <= index < len(self.language_pairs):
            return self.language_pairs[index]
        return None
    
    def parse_language_pair(self, lp: str) -> Tuple[str, str]:
        """
        Parse a language pair string into source and target languages.
        
        Args:
            lp: Language pair string (e.g., "English (GB) into French (France)")
        
        Returns:
            Tuple of (source_language, target_language)
        """
        parts = lp.split(" into ")
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        return "", ""
    
    def clear_all(self):
        """Clear all language pairs."""
        self.language_pairs.clear()
    
    def get_all_language_pairs(self) -> List[str]:
        """
        Get all language pairs.
        
        Returns:
            List of language pair strings
        """
        return self.language_pairs.copy()
    
    def get_count(self) -> int:
        """
        Get the count of language pairs.
        
        Returns:
            Number of language pairs
        """
        return len(self.language_pairs)
    
    def get_numbered_list(self) -> List[str]:
        """
        Get a numbered list of language pairs.
        
        Returns:
            List of strings formatted as "1. English into French"
        """
        return [f"{idx + 1}. {lp}" for idx, lp in enumerate(self.language_pairs)]
