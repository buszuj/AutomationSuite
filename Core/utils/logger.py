"""
Logging Utilities
Centralized logging configuration for all projects.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class LoggerManager:
    """Manage logging across all projects."""
    
    def __init__(self):
        self.loggers = {}
        self.default_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        self.default_level = logging.INFO
    
    def get_logger(
        self,
        name: str,
        log_file: Optional[Path] = None,
        level: int = None,
        console_output: bool = True
    ) -> logging.Logger:
        """
        Get or create a logger instance.
        
        Args:
            name: Logger name
            log_file: Optional path to log file
            level: Logging level
            console_output: Whether to output to console
            
        Returns:
            Configured logger
        """
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(level or self.default_level)
        logger.handlers.clear()
        
        formatter = logging.Formatter(self.default_format)
        
        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        self.loggers[name] = logger
        return logger
    
    def get_project_logger(
        self,
        project_name: str,
        log_dir: Optional[Path] = None,
        level: int = None
    ) -> logging.Logger:
        """
        Get logger for a specific project.
        
        Args:
            project_name: Name of the project
            log_dir: Directory for log files
            level: Logging level
            
        Returns:
            Project-specific logger
        """
        logger_name = f'AutomationSuite.{project_name}'
        
        if log_dir:
            timestamp = datetime.now().strftime('%Y%m%d')
            log_file = log_dir / f'{project_name}_{timestamp}.log'
        else:
            log_file = None
        
        return self.get_logger(logger_name, log_file, level)
    
    def set_level(self, name: str, level: int) -> None:
        """Set logging level for a specific logger."""
        if name in self.loggers:
            self.loggers[name].setLevel(level)
    
    def close_logger(self, name: str) -> None:
        """Close and remove a logger."""
        if name in self.loggers:
            logger = self.loggers[name]
            for handler in logger.handlers:
                handler.close()
                logger.removeHandler(handler)
            del self.loggers[name]
    
    def close_all(self) -> None:
        """Close all loggers."""
        for name in list(self.loggers.keys()):
            self.close_logger(name)


# Singleton instance
logger_manager = LoggerManager()


# Convenience function for quick logger access
def get_logger(name: str, **kwargs) -> logging.Logger:
    """Get a logger instance."""
    return logger_manager.get_logger(name, **kwargs)
