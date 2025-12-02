"""
Service Mapping Manager Module
Handles service to label mappings for QuoteMe and QTC inputs.
"""

import json
import os
from typing import Dict, List, Any, Optional


class ServiceMappingManager:
    """Manages service label mappings for different accounts."""
    
    def __init__(self, mapping_file: str = "service_label_mapping.json"):
        """
        Initialize ServiceMappingManager.
        
        Args:
            mapping_file: Path to the mapping JSON file
        """
        self.mapping_file = mapping_file
        self.all_mappings = self.load_all_mappings()
    
    def load_all_mappings(self) -> Dict[str, Any]:
        """
        Load all service mappings from file.
        
        Returns:
            Dictionary mapping account keys to their service mappings
        """
        if os.path.exists(self.mapping_file):
            with open(self.mapping_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def save_all_mappings(self):
        """Save all mappings to file."""
        with open(self.mapping_file, "w", encoding="utf-8") as f:
            json.dump(self.all_mappings, f, indent=2)
    
    def get_mapping_for_account(self, account_key: str) -> Dict[str, Any]:
        """
        Get service mapping for a specific account.
        
        Args:
            account_key: Account/ratesheet identifier
        
        Returns:
            Dictionary of service mappings
        """
        return self.all_mappings.get(account_key, {})
    
    def save_mapping_for_account(
        self,
        account_key: str,
        mapping: Dict[str, Any]
    ):
        """
        Save service mapping for an account.
        
        Args:
            account_key: Account/ratesheet identifier
            mapping: Service mapping dictionary
        """
        self.all_mappings[account_key] = mapping
        self.save_all_mappings()
    
    def get_service_labels(
        self,
        account_key: str,
        service: str,
        input_type: str
    ) -> List[str]:
        """
        Get mapped labels for a service.
        
        Args:
            account_key: Account/ratesheet identifier
            service: Service name
            input_type: "QuoteMe" or "QTC"
        
        Returns:
            List of label names
        """
        mapping = self.get_mapping_for_account(account_key)
        service_config = mapping.get(service, {})
        return service_config.get(input_type, [])
    
    def get_default_pm_percent(self, account_key: str) -> float:
        """
        Get default Project Management percentage.
        
        Args:
            account_key: Account/ratesheet identifier
        
        Returns:
            Default PM percentage (default: 10.0)
        """
        mapping = self.get_mapping_for_account(account_key)
        val = mapping.get("default_pm_percent", 10)
        try:
            return float(val)
        except (ValueError, TypeError):
            return 10.0
    
    def get_min_hourly_rate(self, account_key: str) -> float:
        """
        Get minimum hourly rate.
        
        Args:
            account_key: Account/ratesheet identifier
        
        Returns:
            Minimum hourly rate (default: 0.5)
        """
        mapping = self.get_mapping_for_account(account_key)
        val = mapping.get("min_hourly_rate", 0.5)
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.5
    
    def get_increment_rate(self, account_key: str) -> float:
        """
        Get increment rate for hourly services.
        
        Args:
            account_key: Account/ratesheet identifier
        
        Returns:
            Increment rate (default: 0.25)
        """
        mapping = self.get_mapping_for_account(account_key)
        val = mapping.get("increment_rate", 0.25)
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.25
