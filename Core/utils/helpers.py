"""
Helper Utilities
Common helper functions used across all projects.
"""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Union, Optional
from datetime import datetime, timedelta
import re


def load_json(file_path: Union[str, Path]) -> Dict:
    """Load JSON file and return as dictionary."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Dict, file_path: Union[str, Path], indent: int = 2) -> None:
    """Save dictionary to JSON file."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_yaml(file_path: Union[str, Path]) -> Dict:
    """Load YAML file and return as dictionary."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_yaml(data: Dict, file_path: Union[str, Path]) -> None:
    """Save dictionary to YAML file."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename."""
    # Remove invalid characters for Windows filenames
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    return sanitized.strip()


def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format number as currency string."""
    if currency == 'USD':
        return f'${amount:,.2f}'
    elif currency == 'EUR':
        return f'€{amount:,.2f}'
    else:
        return f'{amount:,.2f} {currency}'


def parse_date(date_string: str, format_string: str = '%Y-%m-%d') -> Optional[datetime]:
    """Parse date string to datetime object."""
    try:
        return datetime.strptime(date_string, format_string)
    except ValueError:
        return None


def format_date(date_obj: datetime, format_string: str = '%Y-%m-%d') -> str:
    """Format datetime object to string."""
    return date_obj.strftime(format_string)


def calculate_deadline(
    start_date: Union[datetime, str],
    days: int,
    format_string: str = '%Y-%m-%d'
) -> str:
    """Calculate deadline from start date and number of days."""
    if isinstance(start_date, str):
        start_date = parse_date(start_date, format_string)
    
    deadline = start_date + timedelta(days=days)
    return format_date(deadline, format_string)


def flatten_dict(d: Dict, parent_key: str = '', separator: str = '.') -> Dict:
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f'{parent_key}{separator}{k}' if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, separator).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def remove_duplicates(lst: List, key: Optional[str] = None) -> List:
    """Remove duplicates from list, optionally by key for list of dicts."""
    if not lst:
        return []
    
    if key and isinstance(lst[0], dict):
        seen = set()
        result = []
        for item in lst:
            if item.get(key) not in seen:
                seen.add(item.get(key))
                result.append(item)
        return result
    else:
        return list(dict.fromkeys(lst))


def safe_get(d: Dict, key_path: str, default: Any = None, separator: str = '.') -> Any:
    """
    Safely get value from nested dictionary using dot notation.
    
    Example: safe_get(data, 'user.profile.email', 'N/A')
    """
    keys = key_path.split(separator)
    value = d
    
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
            if value is None:
                return default
        else:
            return default
    
    return value if value is not None else default


def merge_dicts(*dicts: Dict) -> Dict:
    """Merge multiple dictionaries, later ones override earlier ones."""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def percentage(part: float, whole: float, decimals: int = 2) -> float:
    """Calculate percentage with error handling."""
    if whole == 0:
        return 0.0
    return round((part / whole) * 100, decimals)


def truncate_string(text: str, max_length: int, suffix: str = '...') -> str:
    """Truncate string to max length with suffix."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
