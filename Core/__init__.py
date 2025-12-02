"""
AutomationSuite Core Module
Shared utilities and common functionality for all projects.
"""

__version__ = '1.0.0'
__author__ = 'Your Organization'

# Import main components for easy access
from .excel_io import excel_handler, ExcelHandler
from .df_processing import df_processor, DataFrameProcessor
from .validators import validator, DataValidator

__all__ = [
    'excel_handler',
    'ExcelHandler',
    'df_processor',
    'DataFrameProcessor',
    'validator',
    'DataValidator',
]
