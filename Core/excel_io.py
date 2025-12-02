"""
Core Excel I/O Module
Handles reading from and writing to Excel files across all projects.
Provides comprehensive Excel operations for the AutomationSuite.
"""

import pandas as pd
import openpyxl
from pathlib import Path
from typing import Union, Dict, List, Optional, Any, Tuple
import logging

# Setup logger
logger = logging.getLogger(__name__)


class ExcelHandler:
    """Centralized Excel file operations for all AutomationSuite projects."""
    
    def __init__(self):
        self.active_workbooks: Dict[str, pd.ExcelFile] = {}
        self._cache: Dict[str, Any] = {}
    
    def read_excel(
        self, 
        file_path: Union[str, Path], 
        sheet_name: Optional[str] = None,
        **kwargs
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        Read Excel file and return DataFrame(s).
        
        Args:
            file_path: Path to Excel file
            sheet_name: Specific sheet name or None for all sheets
            **kwargs: Additional arguments for pd.read_excel
            
        Returns:
            DataFrame or dict of DataFrames
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        
        try:
            if sheet_name:
                return pd.read_excel(file_path, sheet_name=sheet_name, **kwargs)
            else:
                return pd.read_excel(file_path, sheet_name=None, **kwargs)
        except Exception as e:
            raise Exception(f"Error reading Excel file {file_path}: {str(e)}")
    
    def write_excel(
        self,
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
        file_path: Union[str, Path],
        sheet_name: str = 'Sheet1',
        **kwargs
    ) -> None:
        """
        Write DataFrame(s) to Excel file.
        
        Args:
            data: Single DataFrame or dict of DataFrames
            file_path: Output file path
            sheet_name: Sheet name (for single DataFrame)
            **kwargs: Additional arguments for pd.ExcelWriter
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl', **kwargs) as writer:
                if isinstance(data, dict):
                    for sheet, df in data.items():
                        df.to_excel(writer, sheet_name=sheet, index=False)
                else:
                    data.to_excel(writer, sheet_name=sheet_name, index=False)
        except Exception as e:
            raise Exception(f"Error writing Excel file {file_path}: {str(e)}")
    
    def read_sheet_names(self, file_path: Union[str, Path]) -> List[str]:
        """Get list of sheet names from Excel file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        
        with pd.ExcelFile(file_path) as xls:
            return xls.sheet_names
    
    def append_to_sheet(
        self,
        data: pd.DataFrame,
        file_path: Union[str, Path],
        sheet_name: str = 'Sheet1'
    ) -> None:
        """Append DataFrame to existing Excel sheet."""
        file_path = Path(file_path)
        
        if file_path.exists():
            existing_data = self.read_excel(file_path, sheet_name=sheet_name)
            combined_data = pd.concat([existing_data, data], ignore_index=True)
        else:
            combined_data = data
        
        self.write_excel(combined_data, file_path, sheet_name=sheet_name)
    
    def read_excel_range(
        self,
        file_path: Union[str, Path],
        sheet_name: str,
        start_row: int = 0,
        end_row: Optional[int] = None,
        start_col: int = 0,
        end_col: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Read specific range from Excel sheet.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name
            start_row: Starting row (0-indexed)
            end_row: Ending row (exclusive), None for all
            start_col: Starting column (0-indexed)
            end_col: Ending column (exclusive), None for all
            
        Returns:
            DataFrame with specified range
        """
        df = self.read_excel(file_path, sheet_name=sheet_name)
        
        if end_row is None:
            end_row = len(df)
        if end_col is None:
            end_col = len(df.columns)
        
        return df.iloc[start_row:end_row, start_col:end_col]
    
    def read_column(
        self,
        file_path: Union[str, Path],
        sheet_name: str,
        column: Union[str, int]
    ) -> pd.Series:
        """
        Read single column from Excel sheet.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name
            column: Column name or index
            
        Returns:
            Series with column data
        """
        df = self.read_excel(file_path, sheet_name=sheet_name)
        
        if isinstance(column, int):
            return df.iloc[:, column]
        else:
            return df[column]
    
    def read_columns(
        self,
        file_path: Union[str, Path],
        sheet_name: str,
        columns: List[Union[str, int]]
    ) -> pd.DataFrame:
        """
        Read multiple columns from Excel sheet.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name
            columns: List of column names or indices
            
        Returns:
            DataFrame with specified columns
        """
        df = self.read_excel(file_path, sheet_name=sheet_name)
        
        if all(isinstance(col, int) for col in columns):
            return df.iloc[:, columns]
        else:
            return df[columns]
    
    def read_with_filter(
        self,
        file_path: Union[str, Path],
        sheet_name: str,
        filter_column: str,
        filter_value: Any
    ) -> pd.DataFrame:
        """
        Read Excel data and filter by column value.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name
            filter_column: Column to filter on
            filter_value: Value to filter for
            
        Returns:
            Filtered DataFrame
        """
        df = self.read_excel(file_path, sheet_name=sheet_name)
        return df[df[filter_column] == filter_value]
    
    def get_cell_value(
        self,
        file_path: Union[str, Path],
        sheet_name: str,
        row: int,
        column: Union[str, int]
    ) -> Any:
        """
        Get single cell value from Excel.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name
            row: Row index (0-indexed)
            column: Column name or index
            
        Returns:
            Cell value
        """
        df = self.read_excel(file_path, sheet_name=sheet_name)
        
        if isinstance(column, int):
            return df.iloc[row, column]
        else:
            return df.loc[row, column]
    
    def get_excel_info(
        self,
        file_path: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        Get comprehensive information about Excel file.
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            Dictionary with file information
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        
        info = {
            'file_path': str(file_path),
            'file_size': file_path.stat().st_size,
            'sheets': {}
        }
        
        with pd.ExcelFile(file_path) as xls:
            info['sheet_names'] = xls.sheet_names
            
            for sheet in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet)
                info['sheets'][sheet] = {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'column_names': df.columns.tolist(),
                    'dtypes': df.dtypes.to_dict()
                }
        
        return info
    
    def validate_excel_structure(
        self,
        file_path: Union[str, Path],
        sheet_name: str,
        required_columns: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate Excel sheet has required columns.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name
            required_columns: List of required column names
            
        Returns:
            Tuple of (is_valid, missing_columns)
        """
        df = self.read_excel(file_path, sheet_name=sheet_name)
        missing = [col for col in required_columns if col not in df.columns]
        return len(missing) == 0, missing
    
    def find_sheets_by_prefix(
        self,
        file_path: Union[str, Path],
        prefix: str
    ) -> List[str]:
        """
        Find all sheets starting with specified prefix.
        
        Args:
            file_path: Path to Excel file
            prefix: Prefix to search for
            
        Returns:
            List of matching sheet names
        """
        sheets = self.read_sheet_names(file_path)
        return [sheet for sheet in sheets if sheet.startswith(prefix)]
    
    def read_multiple_sheets(
        self,
        file_path: Union[str, Path],
        sheet_names: List[str]
    ) -> Dict[str, pd.DataFrame]:
        """
        Read multiple specific sheets.
        
        Args:
            file_path: Path to Excel file
            sheet_names: List of sheet names to read
            
        Returns:
            Dictionary mapping sheet names to DataFrames
        """
        result = {}
        for sheet in sheet_names:
            result[sheet] = self.read_excel(file_path, sheet_name=sheet)
        return result
    
    def clear_cache(self):
        """Clear internal cache."""
        self._cache.clear()
        self.active_workbooks.clear()
        logger.info("Excel handler cache cleared")


# Singleton instance for global use
excel_handler = ExcelHandler()
