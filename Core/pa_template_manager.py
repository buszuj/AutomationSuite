"""
PA Template Manager - Core Module
Manages PA (ProjectA) template configurations for multiple accounts

This module:
1. Stores template configurations per account in JSON format
2. Supports 2-column template structure: Keys column + Data/Mapping column
3. Handles CRUD operations for templates
4. Validates template structures

Author: AutomationSuite Team
Date: December 2025
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path


# Default template storage file
TEMPLATE_CONFIG_FILE = os.path.join(
    os.path.dirname(__file__), 
    "pa_template_configs.json"
)


class PATemplateManager:
    """
    Manages PA template configurations for accounts
    
    Template Structure:
    {
        "account_name": {
            "template_name": "Integration Template v1",
            "description": "Standard PA import template",
            "key_column_name": "Field Name",
            "data_column_name": "Value",
            "mappings": [
                {
                    "key": "Project Code",
                    "source_column": "Project_Code",
                    "mapping_type": "direct",  # direct, static, calculated, concatenate
                    "static_value": null,
                    "formula": null,
                    "format": null  # date, number, text
                },
                {
                    "key": "Job ID",
                    "source_column": "Sub_ID",
                    "mapping_type": "direct",
                    "static_value": null,
                    "formula": null,
                    "format": "text"
                },
                ...
            ]
        }
    }
    """
    
    def __init__(self, config_file: str = TEMPLATE_CONFIG_FILE):
        """Initialize PA Template Manager"""
        self.config_file = config_file
        self.templates: Dict[str, Any] = {}
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load templates from JSON file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
                print(f"Loaded {len(self.templates)} PA template(s)")
            except Exception as e:
                print(f"Error loading PA templates: {e}")
                self.templates = {}
        else:
            print(f"No existing PA template config found, creating new one")
            self.templates = {}
            self._save_templates()
    
    def _save_templates(self) -> bool:
        """Save templates to JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving PA templates: {e}")
            return False
    
    def create_template(
        self, 
        account_name: str,
        template_name: str = "Integration Template",
        description: str = "",
        key_column_name: str = "Field Name",
        data_column_name: str = "Value",
        mappings: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Create a new PA template for an account
        
        Args:
            account_name: Account identifier
            template_name: Name of the template
            description: Template description
            key_column_name: Name for the keys column (default: "Field Name")
            data_column_name: Name for the data column (default: "Value")
            mappings: List of field mappings
        
        Returns:
            True if successful, False otherwise
        """
        if not account_name:
            print("Error: Account name is required")
            return False
        
        if mappings is None:
            mappings = []
        
        # Validate mappings structure
        for mapping in mappings:
            if not self._validate_mapping(mapping):
                print(f"Error: Invalid mapping structure: {mapping}")
                return False
        
        self.templates[account_name] = {
            "template_name": template_name,
            "description": description,
            "key_column_name": key_column_name,
            "data_column_name": data_column_name,
            "mappings": mappings
        }
        
        return self._save_templates()
    
    def update_template(
        self,
        account_name: str,
        **kwargs
    ) -> bool:
        """
        Update an existing PA template
        
        Args:
            account_name: Account identifier
            **kwargs: Fields to update (template_name, description, mappings, etc.)
        
        Returns:
            True if successful, False otherwise
        """
        if account_name not in self.templates:
            print(f"Error: Template for account '{account_name}' not found")
            return False
        
        # Update specified fields
        for key, value in kwargs.items():
            if key in self.templates[account_name]:
                self.templates[account_name][key] = value
        
        return self._save_templates()
    
    def delete_template(self, account_name: str) -> bool:
        """
        Delete a PA template
        
        Args:
            account_name: Account identifier
        
        Returns:
            True if successful, False otherwise
        """
        if account_name not in self.templates:
            print(f"Error: Template for account '{account_name}' not found")
            return False
        
        del self.templates[account_name]
        return self._save_templates()
    
    def get_template(self, account_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a PA template by account name
        
        Args:
            account_name: Account identifier
        
        Returns:
            Template dictionary or None if not found
        """
        return self.templates.get(account_name)
    
    def get_all_templates(self) -> Dict[str, Any]:
        """
        Get all PA templates
        
        Returns:
            Dictionary of all templates
        """
        return self.templates.copy()
    
    def get_template_mappings(self, account_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get mappings for a specific template
        
        Args:
            account_name: Account identifier
        
        Returns:
            List of mappings or None if not found
        """
        template = self.get_template(account_name)
        return template.get("mappings") if template else None
    
    def add_mapping(
        self,
        account_name: str,
        key: str,
        source_column: Optional[str] = None,
        mapping_type: str = "direct",
        static_value: Optional[str] = None,
        formula: Optional[str] = None,
        format_type: Optional[str] = None
    ) -> bool:
        """
        Add a new field mapping to a template
        
        Args:
            account_name: Account identifier
            key: Key name in the template (e.g., "Project Code")
            source_column: Source DataFrame column name
            mapping_type: Type of mapping (direct, static, calculated, concatenate)
            static_value: Static value for static mappings
            formula: Formula for calculated mappings
            format_type: Format type (date, number, text)
        
        Returns:
            True if successful, False otherwise
        """
        if account_name not in self.templates:
            print(f"Error: Template for account '{account_name}' not found")
            return False
        
        mapping = {
            "key": key,
            "source_column": source_column,
            "mapping_type": mapping_type,
            "static_value": static_value,
            "formula": formula,
            "format": format_type
        }
        
        if not self._validate_mapping(mapping):
            print(f"Error: Invalid mapping structure: {mapping}")
            return False
        
        self.templates[account_name]["mappings"].append(mapping)
        return self._save_templates()
    
    def remove_mapping(self, account_name: str, key: str) -> bool:
        """
        Remove a field mapping from a template
        
        Args:
            account_name: Account identifier
            key: Key name to remove
        
        Returns:
            True if successful, False otherwise
        """
        if account_name not in self.templates:
            print(f"Error: Template for account '{account_name}' not found")
            return False
        
        mappings = self.templates[account_name]["mappings"]
        self.templates[account_name]["mappings"] = [
            m for m in mappings if m.get("key") != key
        ]
        
        return self._save_templates()
    
    def update_mapping(
        self,
        account_name: str,
        key: str,
        **kwargs
    ) -> bool:
        """
        Update a specific field mapping
        
        Args:
            account_name: Account identifier
            key: Key name to update
            **kwargs: Fields to update in the mapping
        
        Returns:
            True if successful, False otherwise
        """
        if account_name not in self.templates:
            print(f"Error: Template for account '{account_name}' not found")
            return False
        
        mappings = self.templates[account_name]["mappings"]
        for mapping in mappings:
            if mapping.get("key") == key:
                for field, value in kwargs.items():
                    mapping[field] = value
                return self._save_templates()
        
        print(f"Error: Mapping with key '{key}' not found")
        return False
    
    def _validate_mapping(self, mapping: Dict[str, Any]) -> bool:
        """
        Validate mapping structure
        
        Args:
            mapping: Mapping dictionary to validate
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["key", "mapping_type"]
        for field in required_fields:
            if field not in mapping:
                print(f"Error: Missing required field '{field}' in mapping")
                return False
        
        valid_mapping_types = ["direct", "static", "calculated", "concatenate"]
        if mapping["mapping_type"] not in valid_mapping_types:
            print(f"Error: Invalid mapping_type '{mapping['mapping_type']}'")
            return False
        
        # Validate based on mapping type
        if mapping["mapping_type"] == "direct":
            if not mapping.get("source_column"):
                print("Error: 'direct' mapping requires source_column")
                return False
        
        elif mapping["mapping_type"] == "static":
            if not mapping.get("static_value"):
                print("Error: 'static' mapping requires static_value")
                return False
        
        elif mapping["mapping_type"] == "calculated":
            if not mapping.get("formula"):
                print("Error: 'calculated' mapping requires formula")
                return False
        
        elif mapping["mapping_type"] == "concatenate":
            if not mapping.get("source_column"):
                print("Error: 'concatenate' mapping requires source_column (comma-separated list)")
                return False
        
        return True
    
    def export_template_to_excel(self, account_name: str, output_path: str) -> bool:
        """
        Export template configuration to Excel for documentation
        
        Args:
            account_name: Account identifier
            output_path: Path to save Excel file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            import pandas as pd
            
            template = self.get_template(account_name)
            if not template:
                print(f"Error: Template for account '{account_name}' not found")
                return False
            
            # Create DataFrame from mappings
            df = pd.DataFrame(template["mappings"])
            
            # Add metadata sheet
            metadata = {
                "Property": ["Template Name", "Description", "Key Column", "Data Column"],
                "Value": [
                    template.get("template_name", ""),
                    template.get("description", ""),
                    template.get("key_column_name", ""),
                    template.get("data_column_name", "")
                ]
            }
            metadata_df = pd.DataFrame(metadata)
            
            # Write to Excel with multiple sheets
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                metadata_df.to_excel(writer, sheet_name='Template Info', index=False)
                df.to_excel(writer, sheet_name='Mappings', index=False)
            
            print(f"Template exported to {output_path}")
            return True
        
        except Exception as e:
            print(f"Error exporting template to Excel: {e}")
            return False


# Convenience functions for direct use
def create_pa_template(account_name: str, **kwargs) -> bool:
    """Create a new PA template"""
    manager = PATemplateManager()
    return manager.create_template(account_name, **kwargs)


def get_pa_template(account_name: str) -> Optional[Dict[str, Any]]:
    """Get a PA template by account name"""
    manager = PATemplateManager()
    return manager.get_template(account_name)


def update_pa_template(account_name: str, **kwargs) -> bool:
    """Update an existing PA template"""
    manager = PATemplateManager()
    return manager.update_template(account_name, **kwargs)


def delete_pa_template(account_name: str) -> bool:
    """Delete a PA template"""
    manager = PATemplateManager()
    return manager.delete_template(account_name)


def list_pa_templates() -> List[str]:
    """List all PA template account names"""
    manager = PATemplateManager()
    return list(manager.get_all_templates().keys())


# Example usage
if __name__ == "__main__":
    # Initialize manager
    manager = PATemplateManager()
    
    # Create example CEVA template
    ceva_mappings = [
        {
            "key": "Project Code",
            "source_column": "Project_Code",
            "mapping_type": "direct",
            "static_value": None,
            "formula": None,
            "format": "text"
        },
        {
            "key": "Job ID",
            "source_column": "Sub_ID",
            "mapping_type": "direct",
            "static_value": None,
            "formula": None,
            "format": "text"
        },
        {
            "key": "Language Pair",
            "source_column": "Language_Pair",
            "mapping_type": "direct",
            "static_value": None,
            "formula": None,
            "format": "text"
        },
        {
            "key": "Word Count",
            "source_column": "Word_Count",
            "mapping_type": "direct",
            "static_value": None,
            "formula": None,
            "format": "number"
        },
        {
            "key": "Status",
            "source_column": None,
            "mapping_type": "static",
            "static_value": "Ready for Import",
            "formula": None,
            "format": "text"
        }
    ]
    
    success = manager.create_template(
        account_name="CEVA",
        template_name="CEVA Integration Template",
        description="Standard template for CEVA PA imports",
        key_column_name="Field Name",
        data_column_name="Value",
        mappings=ceva_mappings
    )
    
    if success:
        print("CEVA template created successfully!")
        
        # Retrieve and display
        template = manager.get_template("CEVA")
        print(f"\nTemplate: {template['template_name']}")
        print(f"Mappings: {len(template['mappings'])} fields")
