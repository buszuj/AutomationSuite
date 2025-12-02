"""
File Path Utilities
Centralized path management for all projects.
"""

from pathlib import Path
from typing import Union, Optional
import os


class PathManager:
    """Manage file paths across all projects."""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent.parent
        self.core_dir = self.root_dir / 'Core'
        self.ceva_dir = self.root_dir / 'CEVA_Launcher'
        self.oss_dir = self.root_dir / 'One_Stop_Shop'
        self.kp_dir = self.root_dir / 'KP_Validator'
        self.shared_ui_dir = self.root_dir / 'Shared_UI'
    
    def get_project_path(self, project_name: str) -> Path:
        """Get the root path for a specific project."""
        project_map = {
            'ceva': self.ceva_dir,
            'oss': self.oss_dir,
            'kp': self.kp_dir,
            'shared_ui': self.shared_ui_dir,
            'core': self.core_dir
        }
        return project_map.get(project_name.lower(), self.root_dir)
    
    def get_mapping_file(self, mapping_name: str) -> Path:
        """Get path to a mapping configuration file."""
        return self.core_dir / 'mappings' / f'{mapping_name}_mapping.json'
    
    def get_config_file(self, config_name: str) -> Path:
        """Get path to a configuration file."""
        return self.core_dir / 'configs' / f'{config_name}.yaml'
    
    def ensure_directory(self, path: Union[str, Path]) -> Path:
        """Ensure a directory exists, create if necessary."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_temp_dir(self) -> Path:
        """Get temporary directory for the project."""
        temp_dir = self.root_dir / 'temp'
        return self.ensure_directory(temp_dir)
    
    def get_logs_dir(self, project_name: Optional[str] = None) -> Path:
        """Get logs directory for a project or root."""
        if project_name:
            logs_dir = self.get_project_path(project_name) / 'logs'
        else:
            logs_dir = self.root_dir / 'logs'
        return self.ensure_directory(logs_dir)
    
    @staticmethod
    def normalize_path(path: Union[str, Path]) -> Path:
        """Normalize and resolve a path."""
        return Path(path).resolve()
    
    @staticmethod
    def get_relative_path(path: Union[str, Path], base: Union[str, Path]) -> Path:
        """Get relative path from base."""
        return Path(path).relative_to(base)


# Singleton instance
path_manager = PathManager()
