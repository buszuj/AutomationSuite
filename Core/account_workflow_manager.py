"""
Account & Workflow Manager
Manages accounts and their workflows (replaces workflow_translator.py for account management)
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional


class AccountWorkflowManager:
    """Manages accounts and their workflows"""
    
    def __init__(self):
        self.data_file = Path(__file__).parent / "accounts_workflows.json"
        self.services_file = Path(__file__).parent / "entity_services.json"
        self.accounts = self.load_accounts()
        self.tpus_services = self.load_tpus_services()
    
    def load_accounts(self) -> dict:
        """Load accounts and workflows from JSON"""
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("accounts", {})
        return {}
    
    def save_accounts(self):
        """Save accounts and workflows to JSON"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump({"accounts": self.accounts}, f, indent=2, ensure_ascii=False)
    
    def load_tpus_services(self) -> List[str]:
        """Load TPUS service names for selection"""
        if self.services_file.exists():
            with open(self.services_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                tpus_services = data.get("TPUS", [])
                # Skip header, extract service names (column 2)
                return [row[2] for row in tpus_services[1:] if len(row) > 2]
        return []
    
    # Account Management
    def create_account(self, account_name: str) -> bool:
        """Create a new account"""
        if account_name in self.accounts:
            return False
        
        self.accounts[account_name] = {
            "workflows": {}
        }
        self.save_accounts()
        return True
    
    def delete_account(self, account_name: str) -> bool:
        """Delete an account, workflows, and all persisted account artifacts."""
        if account_name not in self.accounts:
            return False

        account_dir = Path(__file__).parent / "accounts" / account_name
        if account_dir.exists():
            try:
                shutil.rmtree(account_dir)
            except Exception:
                # Keep failure visible to caller so UI can report delete failure.
                return False

        del self.accounts[account_name]
        self.save_accounts()

        return True
    
    def rename_account(self, old_name: str, new_name: str) -> bool:
        """Rename an account"""
        if old_name not in self.accounts or new_name in self.accounts:
            return False
        
        self.accounts[new_name] = self.accounts.pop(old_name)
        self.save_accounts()
        return True
    
    def get_accounts(self) -> List[str]:
        """Get list of all account names"""
        return list(self.accounts.keys())
    
    # Workflow Management
    def create_workflow(self, account_name: str, workflow_name: str, services: List[str], quoteme_mapping: Optional[Dict] = None) -> bool:
        """Create a new workflow for an account"""
        if account_name not in self.accounts:
            return False
        
        if workflow_name in self.accounts[account_name]["workflows"]:
            return False
        
        # Store workflow with new structure
        self.accounts[account_name]["workflows"][workflow_name] = {
            "services": services,
            "quoteme_mapping": quoteme_mapping or {}
        }
        self.save_accounts()
        return True
    
    def update_workflow(self, account_name: str, workflow_name: str, services: List[str] = None, quoteme_mapping: Optional[Dict] = None) -> bool:
        """Update an existing workflow"""
        if account_name not in self.accounts:
            return False
        
        if workflow_name not in self.accounts[account_name]["workflows"]:
            return False
        
        workflow_data = self.accounts[account_name]["workflows"][workflow_name]
        
        # Handle both old format (list) and new format (dict)
        if isinstance(workflow_data, list):
            # Old format - convert to new format
            workflow_data = {"services": workflow_data, "quoteme_mapping": {}}
        
        if services is not None:
            workflow_data["services"] = services
        if quoteme_mapping is not None:
            workflow_data["quoteme_mapping"] = quoteme_mapping
        
        self.accounts[account_name]["workflows"][workflow_name] = workflow_data
        self.save_accounts()
        return True
    
    def delete_workflow(self, account_name: str, workflow_name: str) -> bool:
        """Delete a workflow from an account"""
        if account_name not in self.accounts:
            return False
        
        if workflow_name not in self.accounts[account_name]["workflows"]:
            return False
        
        del self.accounts[account_name]["workflows"][workflow_name]
        self.save_accounts()
        return True
    
    def rename_workflow(self, account_name: str, old_name: str, new_name: str) -> bool:
        """Rename a workflow"""
        if account_name not in self.accounts:
            return False
        
        workflows = self.accounts[account_name]["workflows"]
        if old_name not in workflows or new_name in workflows:
            return False
        
        workflows[new_name] = workflows.pop(old_name)
        self.save_accounts()
        return True
    
    def get_workflows(self, account_name: str) -> Dict[str, Dict]:
        """Get all workflows for an account"""
        if account_name not in self.accounts:
            return {}
        workflows = self.accounts[account_name]["workflows"]
        
        # Convert old format to new format for consistency
        result = {}
        for name, data in workflows.items():
            if isinstance(data, list):
                result[name] = {"services": data, "quoteme_mapping": {}}
            else:
                result[name] = data
        return result
    
    def get_workflow_services(self, account_name: str, workflow_name: str) -> Optional[List[str]]:
        """Get services for a specific workflow"""
        if account_name not in self.accounts:
            return None
        
        workflows = self.accounts[account_name]["workflows"]
        workflow_data = workflows.get(workflow_name)
        
        if workflow_data is None:
            return None
        
        # Handle both old format (list) and new format (dict)
        if isinstance(workflow_data, list):
            return workflow_data
        elif isinstance(workflow_data, dict):
            return workflow_data.get("services", [])
        
        return None
    
    def get_quoteme_mapping(self, account_name: str, workflow_name: str) -> Optional[Dict]:
        """Get QuoteMe mapping for a specific workflow"""
        if account_name not in self.accounts:
            return None
        
        workflows = self.accounts[account_name]["workflows"]
        workflow_data = workflows.get(workflow_name)
        
        if workflow_data is None:
            return None
        
        # Handle both old format (list) and new format (dict)
        if isinstance(workflow_data, list):
            return {}
        elif isinstance(workflow_data, dict):
            return workflow_data.get("quoteme_mapping", {})
        
        return None
    
    def set_quoteme_mapping(self, account_name: str, workflow_name: str, quoteme_mapping: Dict) -> bool:
        """Update QuoteMe mapping for a workflow"""
        return self.update_workflow(account_name, workflow_name, quoteme_mapping=quoteme_mapping)
    
    def clone_workflow(self, source_account: str, workflow_name: str, target_account: str, new_workflow_name: Optional[str] = None) -> bool:
        """Clone a workflow from one account to another"""
        # Validate source
        if source_account not in self.accounts:
            return False
        
        if workflow_name not in self.accounts[source_account]["workflows"]:
            return False
        
        # Validate target
        if target_account not in self.accounts:
            return False
        
        # Get services from source workflow
        services = self.accounts[source_account]["workflows"][workflow_name].copy()
        
        # Use same name if not specified
        target_name = new_workflow_name if new_workflow_name else workflow_name
        
        # Check if workflow already exists in target
        if target_name in self.accounts[target_account]["workflows"]:
            return False
        
        # Create workflow in target account
        self.accounts[target_account]["workflows"][target_name] = services
        self.save_accounts()
        return True
    
    # Service Attributes (Used_when)
    def get_workflow_services_with_attributes(self, account_name: str, workflow_name: str) -> Optional[List[Dict]]:
        """Get services with their attributes for a workflow"""
        services = self.get_workflow_services(account_name, workflow_name)
        if services is None:
            return None
        
        # Convert simple list to list of dicts if needed
        result = []
        for service in services:
            if isinstance(service, dict):
                # Already has attributes
                result.append(service)
            else:
                # Convert string to dict (backward compatibility)
                result.append({
                    "name": service,
                    "used_when": []  # Default: no filters
                })
        return result
    
    def update_service_attribute(self, account_name: str, workflow_name: str, service_name: str, used_when: List[str]) -> bool:
        """Update Used_when attribute for a service in a workflow"""
        if account_name not in self.accounts:
            return False
        
        workflow_data = self.accounts[account_name]["workflows"].get(workflow_name)
        if not workflow_data:
            return False
        
        # Ensure services is a list of dicts
        services = workflow_data.get("services", []) if isinstance(workflow_data, dict) else workflow_data
        
        # Convert to list of dicts if needed
        services_list = []
        for service in services:
            if isinstance(service, dict):
                services_list.append(service)
            else:
                services_list.append({"name": service, "used_when": []})
        
        # Update the specific service
        for service in services_list:
            if service["name"] == service_name:
                service["used_when"] = used_when
                break
        
        # Save back
        if isinstance(workflow_data, dict):
            workflow_data["services"] = services_list
        else:
            self.accounts[account_name]["workflows"][workflow_name] = {
                "services": services_list,
                "quoteme_mapping": {}
            }
        
        self.save_accounts()
        return True
    
    def get_service_attributes(self, account_name: str, workflow_name: str, service_name: str) -> List[str]:
        """Get Used_when attributes for a specific service"""
        services = self.get_workflow_services_with_attributes(account_name, workflow_name)
        if not services:
            return []
        
        for service in services:
            if service["name"] == service_name:
                return service.get("used_when", [])
        
        return []
    
    # Utility
    def get_account_summary(self, account_name: str) -> Optional[dict]:
        """Get summary of an account"""
        if account_name not in self.accounts:
            return None
        
        workflows = self.accounts[account_name]["workflows"]
        return {
            "name": account_name,
            "workflow_count": len(workflows),
            "workflows": list(workflows.keys())
        }
    
    def get_all_summaries(self) -> List[dict]:
        """Get summaries of all accounts"""
        return [self.get_account_summary(name) for name in self.accounts.keys()]


if __name__ == "__main__":
    # Test the workflow manager
    manager = AccountWorkflowManager()
    
    print("Available TPUS Services:")
    for i, service in enumerate(manager.tpus_services, 1):
        print(f"  {i}. {service}")
    
    print("\nCreating test account...")
    manager.create_account("Test Account")
    
    print("Creating workflows...")
    manager.create_workflow("Test Account", "Standard Translation", [
        "Translation and Proofreading",
        "Proofreading"
    ])
    manager.create_workflow("Test Account", "Full Service", [
        "Translation and Proofreading",
        "Desktop Publishing",
        "Proofreading"
    ])
    
    print("\nAccount Summary:")
    summary = manager.get_account_summary("Test Account")
    print(f"  Account: {summary['name']}")
    print(f"  Workflows: {summary['workflow_count']}")
    for wf in summary['workflows']:
        services = manager.get_workflow_services("Test Account", wf)
        print(f"    - {wf}: {len(services)} services")
        for svc in services:
            print(f"        • {svc}")
