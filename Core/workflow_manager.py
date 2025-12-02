"""
Workflow Manager Module
Handles loading, saving, and managing workflows.
"""

import json
import os
from typing import Dict, List, Optional


class WorkflowManager:
    """Manages workflow configurations for different accounts/ratesheets."""
    
    def __init__(self, workflow_file: str = "workflows.json"):
        """
        Initialize WorkflowManager.
        
        Args:
            workflow_file: Path to the workflow JSON file
        """
        self.workflow_file = workflow_file
        self.all_workflows = self.load_workflows()
    
    def load_workflows(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Load all workflows from file.
        
        Returns:
            Dictionary mapping account names to their workflows
        """
        if os.path.exists(self.workflow_file):
            with open(self.workflow_file, "r", encoding="utf-8") as file:
                return json.load(file)
        return {}
    
    def save_workflows(self):
        """Save all workflows to file."""
        with open(self.workflow_file, "w", encoding="utf-8") as file:
            json.dump(self.all_workflows, file, indent=4)
    
    def get_workflows_for_account(self, account_key: str) -> Dict[str, List[str]]:
        """
        Get workflows for a specific account.
        
        Args:
            account_key: Account/ratesheet identifier
        
        Returns:
            Dictionary of workflow names to service lists
        """
        return self.all_workflows.get(account_key, {})
    
    def save_workflow(
        self,
        account_key: str,
        workflow_name: str,
        services: List[str]
    ) -> bool:
        """
        Save or update a workflow for an account.
        
        Args:
            account_key: Account/ratesheet identifier
            workflow_name: Name of the workflow
            services: List of service names in the workflow
        
        Returns:
            True if successful
        """
        if account_key not in self.all_workflows:
            self.all_workflows[account_key] = {}
        
        self.all_workflows[account_key][workflow_name] = services
        self.save_workflows()
        return True
    
    def delete_workflow(self, account_key: str, workflow_name: str) -> bool:
        """
        Delete a workflow from an account.
        
        Args:
            account_key: Account/ratesheet identifier
            workflow_name: Name of the workflow to delete
        
        Returns:
            True if successful, False if workflow not found
        """
        if account_key in self.all_workflows:
            workflows = self.all_workflows[account_key]
            if workflow_name in workflows:
                del workflows[workflow_name]
                self.save_workflows()
                return True
        return False
    
    def rename_workflow(
        self,
        account_key: str,
        old_name: str,
        new_name: str
    ) -> bool:
        """
        Rename a workflow.
        
        Args:
            account_key: Account/ratesheet identifier
            old_name: Current workflow name
            new_name: New workflow name
        
        Returns:
            True if successful, False if old workflow not found
        """
        if account_key in self.all_workflows:
            workflows = self.all_workflows[account_key]
            if old_name in workflows:
                workflows[new_name] = workflows.pop(old_name)
                self.save_workflows()
                return True
        return False
    
    def workflow_exists(self, account_key: str, workflow_name: str) -> bool:
        """
        Check if a workflow exists.
        
        Args:
            account_key: Account/ratesheet identifier
            workflow_name: Name of the workflow
        
        Returns:
            True if workflow exists
        """
        return (account_key in self.all_workflows and 
                workflow_name in self.all_workflows[account_key])
