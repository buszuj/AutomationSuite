"""
Core Validation Module
Common validation functions for data integrity across all projects.
"""

import re
from pathlib import Path
from typing import Any, List, Optional, Union
from datetime import datetime


class DataValidator:
    """Centralized validation operations for data integrity."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_file_path(file_path: Union[str, Path], must_exist: bool = False) -> bool:
        """
        Validate file path.
        
        Args:
            file_path: Path to validate
            must_exist: If True, check if file exists
            
        Returns:
            True if valid
        """
        try:
            path = Path(file_path)
            if must_exist:
                return path.exists() and path.is_file()
            return True
        except Exception:
            return False
    
    @staticmethod
    def validate_date_format(date_string: str, format_string: str = '%Y-%m-%d') -> bool:
        """
        Validate date string against format.
        
        Args:
            date_string: Date string to validate
            format_string: Expected date format
            
        Returns:
            True if valid
        """
        try:
            datetime.strptime(date_string, format_string)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_numeric_range(
        value: Union[int, float],
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None
    ) -> bool:
        """
        Validate numeric value within range.
        
        Args:
            value: Value to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            True if valid
        """
        if min_value is not None and value < min_value:
            return False
        if max_value is not None and value > max_value:
            return False
        return True
    
    @staticmethod
    def validate_required_fields(data: dict, required_fields: List[str]) -> tuple[bool, List[str]]:
        """
        Validate that required fields exist and are not empty.
        
        Args:
            data: Dictionary to validate
            required_fields: List of required field names
            
        Returns:
            Tuple of (is_valid, list_of_missing_fields)
        """
        missing_fields = []
        
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                missing_fields.append(field)
        
        return len(missing_fields) == 0, missing_fields
    
    @staticmethod
    def validate_language_code(lang_code: str) -> bool:
        """
        Validate language code format (ISO 639-1 or custom).
        
        Args:
            lang_code: Language code to validate
            
        Returns:
            True if valid format
        """
        # Accept 2-letter codes, 5-character codes (en-US), or 3-letter codes
        pattern = r'^[a-z]{2}(-[A-Z]{2})?$|^[a-z]{3}$'
        return bool(re.match(pattern, lang_code, re.IGNORECASE))
    
    @staticmethod
    def validate_job_id(job_id: str, pattern: Optional[str] = None) -> bool:
        """
        Validate job ID format.
        
        Args:
            job_id: Job ID to validate
            pattern: Optional regex pattern for validation
            
        Returns:
            True if valid
        """
        if pattern:
            return bool(re.match(pattern, str(job_id)))
        
        # Default: alphanumeric with hyphens, underscores
        default_pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(default_pattern, str(job_id)))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        pattern = r'^https?://[^\s]+$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def validate_positive_number(value: Any) -> bool:
        """Validate that value is a positive number."""
        try:
            num = float(value)
            return num > 0
        except (ValueError, TypeError):
            return False


# Singleton instance
validator = DataValidator()
