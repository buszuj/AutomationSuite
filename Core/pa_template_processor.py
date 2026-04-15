"""
PA Template Processor - Core Module
Applies PA template mappings to DataFrames to generate Integration worksheets

This module:
1. Takes a DataFrame and PA template configuration
2. Applies field mappings (direct, static, calculated, concatenate)
3. Formats data according to template specifications
4. Creates 2-column output (Key, Value) for PA import

Author: AutomationSuite Team
Date: December 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import re

from pa_template_manager import PATemplateManager


class PATemplateProcessor:
    """
    Processes DataFrames using PA template configurations
    
    Converts raw job data into PA-ready 2-column format:
    | Field Name     | Value           |
    |----------------|-----------------|
    | Project Code   | HAB12345        |
    | Job ID         | 98765           |
    | Language Pair  | en-US > fr-FR   |
    | ...            | ...             |
    """
    
    def __init__(self, template_manager: Optional[PATemplateManager] = None):
        """Initialize PA Template Processor"""
        self.template_manager = template_manager or PATemplateManager()
    
    def process_dataframe(
        self,
        df: pd.DataFrame,
        account_name: str,
        row_index: Optional[int] = None
    ) -> Optional[pd.DataFrame]:
        """
        Process a DataFrame using account's PA template
        
        Args:
            df: Source DataFrame with job data
            account_name: Account identifier to get template
            row_index: Specific row index to process (if None, processes first row)
        
        Returns:
            2-column DataFrame ready for PA import, or None if error
        """
        # Get template for account
        template = self.template_manager.get_template(account_name)
        if not template:
            print(f"Error: No PA template found for account '{account_name}'")
            return None
        
        # Get the row to process
        if row_index is None:
            row_index = 0
        
        if row_index >= len(df):
            print(f"Error: Row index {row_index} out of range (DataFrame has {len(df)} rows)")
            return None
        
        row_data = df.iloc[row_index]
        
        # Extract template configuration
        key_column_name = template.get("key_column_name", "Field Name")
        data_column_name = template.get("data_column_name", "Value")
        mappings = template.get("mappings", [])
        
        # Process each mapping
        result_data = []
        for mapping in mappings:
            key = mapping.get("key", "")
            value = self._apply_mapping(row_data, df, mapping, row_index)
            
            result_data.append({
                key_column_name: key,
                data_column_name: value
            })
        
        # Create result DataFrame
        result_df = pd.DataFrame(result_data)
        return result_df
    
    def process_multiple_rows(
        self,
        df: pd.DataFrame,
        account_name: str,
        group_by_column: Optional[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Process multiple rows from DataFrame, grouped by a column
        
        Args:
            df: Source DataFrame with job data
            account_name: Account identifier to get template
            group_by_column: Column to group by (e.g., "Sub_ID")
        
        Returns:
            Dictionary mapping group value to processed DataFrame
            Example: {"12345": df1, "12346": df2, ...}
        """
        results = {}
        
        if group_by_column and group_by_column in df.columns:
            # Group by column and process each group
            grouped = df.groupby(group_by_column)
            
            for group_value, group_df in grouped:
                # Process first row of each group (or merge data as needed)
                processed_df = self.process_dataframe(
                    group_df.reset_index(drop=True),
                    account_name,
                    row_index=0
                )
                if processed_df is not None:
                    results[str(group_value)] = processed_df
        else:
            # Process each row individually
            for idx in range(len(df)):
                processed_df = self.process_dataframe(df, account_name, row_index=idx)
                if processed_df is not None:
                    results[f"row_{idx}"] = processed_df
        
        return results
    
    def _apply_mapping(
        self,
        row_data: pd.Series,
        full_df: pd.DataFrame,
        mapping: Dict[str, Any],
        row_index: int
    ) -> Any:
        """
        Apply a single field mapping to row data
        
        Args:
            row_data: Single row as pandas Series
            full_df: Full DataFrame (for calculated mappings)
            mapping: Mapping configuration
            row_index: Current row index in full DataFrame
        
        Returns:
            Mapped value
        """
        mapping_type = mapping.get("mapping_type", "direct")
        
        try:
            if mapping_type == "direct":
                return self._apply_direct_mapping(row_data, full_df, mapping)
            
            elif mapping_type == "static":
                return self._apply_static_mapping(mapping)
            
            elif mapping_type == "calculated":
                return self._apply_calculated_mapping(row_data, full_df, mapping, row_index)
            
            elif mapping_type == "concatenate":
                return self._apply_concatenate_mapping(row_data, mapping)
            
            else:
                print(f"Warning: Unknown mapping type '{mapping_type}'")
                return ""
        
        except Exception as e:
            print(f"Error applying mapping for key '{mapping.get('key')}': {e}")
            return ""
    
    def _apply_direct_mapping(self, row_data: pd.Series, full_df: pd.DataFrame, mapping: Dict[str, Any]) -> Any:
        """
        Apply direct column mapping
        
        Args:
            row_data: Row data as Series
            mapping: Mapping configuration
        
        Returns:
            Column value with optional formatting
        """
        source_column = mapping.get("source_column")
        if not source_column:
            return ""

        # Try exact match, then case/whitespace-insensitive match
        if source_column not in row_data:
            normalized = {str(col).strip().lower(): col for col in row_data.index}
            match = normalized.get(str(source_column).strip().lower())
            if match:
                source_column = match
            else:
                return ""

        value = row_data[source_column]

        # If value is missing or looks like a header, try to map by job/portal ID
        if (pd.isna(value) or str(value).strip() == "" or (isinstance(value, str) and value.strip() == str(source_column).strip())):
            id_columns = [
                "GL Portal No",
                "GL Portal Number",
                "Job ID",
                "Job_ID",
                "Sub_ID",
                "Submission ID",
            ]
            id_col = next((c for c in id_columns if c in row_data.index), None)
            if id_col is not None:
                id_value = row_data.get(id_col)
                if pd.notna(id_value):
                    matches = full_df[full_df[id_col] == id_value]
                    if not matches.empty:
                        candidate_series = matches[source_column].dropna()
                        candidate_series = candidate_series[candidate_series.astype(str).str.strip() != ""]
                        if not candidate_series.empty:
                            candidate = candidate_series.iloc[0]
                            if str(candidate).strip() != str(source_column).strip():
                                value = candidate
        
        # Apply formatting if specified
        format_type = mapping.get("format")
        if format_type:
            value = self._format_value(value, format_type)
        
        return value
    
    def _apply_static_mapping(self, mapping: Dict[str, Any]) -> Any:
        """
        Apply static value mapping
        
        Args:
            mapping: Mapping configuration
        
        Returns:
            Static value
        """
        return mapping.get("static_value", "")
    
    def _apply_calculated_mapping(
        self,
        row_data: pd.Series,
        full_df: pd.DataFrame,
        mapping: Dict[str, Any],
        row_index: int
    ) -> Any:
        """
        Apply calculated formula mapping
        
        Args:
            row_data: Row data as Series
            full_df: Full DataFrame
            mapping: Mapping configuration
            row_index: Current row index
        
        Returns:
            Calculated value
        """
        formula = mapping.get("formula", "")
        if not formula:
            return ""
        
        try:
            # Create evaluation context with row data and common functions
            eval_context = {
                'row': row_data,
                'df': full_df,
                'idx': row_index,
                'pd': pd,
                'np': np,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'round': round,
                'sum': sum,
                'max': max,
                'min': min
            }
            
            # Evaluate formula
            result = eval(formula, {"__builtins__": {}}, eval_context)
            
            # Apply formatting if specified
            format_type = mapping.get("format")
            if format_type:
                result = self._format_value(result, format_type)
            
            return result
        
        except Exception as e:
            print(f"Error evaluating formula '{formula}': {e}")
            return ""
    
    def _apply_concatenate_mapping(self, row_data: pd.Series, mapping: Dict[str, Any]) -> str:
        """
        Apply concatenate mapping (join multiple columns)
        
        Args:
            row_data: Row data as Series
            mapping: Mapping configuration
        
        Returns:
            Concatenated string
        """
        source_column = mapping.get("source_column", "")
        if not source_column:
            return ""
        
        # Parse comma-separated column names
        column_names = [col.strip() for col in source_column.split(",")]
        
        # Get separator (default to space)
        separator = mapping.get("separator", " ")
        
        # Collect values
        values = []
        for col in column_names:
            if col in row_data:
                value = row_data[col]
                if pd.notna(value) and str(value).strip():
                    values.append(str(value))
        
        result = separator.join(values)
        
        # Apply formatting if specified
        format_type = mapping.get("format")
        if format_type:
            result = self._format_value(result, format_type)
        
        return result
    
    def _format_value(self, value: Any, format_type: str) -> Any:
        """
        Format value according to specified format type
        
        Args:
            value: Value to format
            format_type: Format type (date, number, text, etc.)
        
        Returns:
            Formatted value
        """
        if pd.isna(value):
            return ""
        
        try:
            if format_type == "date":
                # Try to parse as date
                if isinstance(value, (datetime, pd.Timestamp)):
                    return value.strftime("%m/%d/%Y")
                else:
                    dt = pd.to_datetime(value, errors='coerce')
                    if pd.notna(dt):
                        return dt.strftime("%m/%d/%Y")
                    return str(value)
            
            elif format_type == "datetime":
                # Full datetime format
                if isinstance(value, (datetime, pd.Timestamp)):
                    return value.strftime("%m/%d/%Y %H:%M:%S")
                else:
                    dt = pd.to_datetime(value, errors='coerce')
                    if pd.notna(dt):
                        return dt.strftime("%m/%d/%Y %H:%M:%S")
                    return str(value)
            
            elif format_type == "number":
                # Format as number with 2 decimal places
                try:
                    num = float(value)
                    return round(num, 2)
                except (ValueError, TypeError):
                    return value
            
            elif format_type == "integer":
                # Format as integer
                try:
                    return int(float(value))
                except (ValueError, TypeError):
                    return value
            
            elif format_type == "currency":
                # Format as currency
                try:
                    num = float(value)
                    return f"${num:,.2f}"
                except (ValueError, TypeError):
                    return value
            
            elif format_type == "percentage":
                # Format as percentage
                try:
                    num = float(value)
                    return f"{num * 100:.2f}%"
                except (ValueError, TypeError):
                    return value
            
            elif format_type == "text":
                # Convert to string and strip whitespace
                return str(value).strip()
            
            elif format_type == "upper":
                # Convert to uppercase
                return str(value).upper()
            
            elif format_type == "lower":
                # Convert to lowercase
                return str(value).lower()
            
            elif format_type == "title":
                # Convert to title case
                return str(value).title()
            
            else:
                # Unknown format, return as-is
                return value
        
        except Exception as e:
            print(f"Error formatting value '{value}' with format '{format_type}': {e}")
            return value
    
    def export_to_excel(
        self,
        processed_data: Dict[str, pd.DataFrame],
        output_path: str,
        worksheet_prefix: str = "Sub_"
    ) -> bool:
        """
        Export processed data to Excel with multiple worksheets
        
        Args:
            processed_data: Dictionary mapping IDs to processed DataFrames
            output_path: Path to save Excel file
            worksheet_prefix: Prefix for worksheet names (e.g., "Sub_")
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for identifier, df in processed_data.items():
                    # Create worksheet name (limit to 31 characters for Excel)
                    ws_name = f"{worksheet_prefix}{identifier}"
                    ws_name = ws_name[:31]
                    
                    # Write DataFrame to worksheet
                    df.to_excel(writer, sheet_name=ws_name, index=False)
            
            print(f"Exported {len(processed_data)} worksheet(s) to {output_path}")
            return True
        
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return False
    
    def validate_template_compatibility(
        self,
        df: pd.DataFrame,
        account_name: str
    ) -> Dict[str, Any]:
        """
        Validate if DataFrame is compatible with account's template
        
        Args:
            df: DataFrame to validate
            account_name: Account identifier
        
        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "missing_columns": list,
                "warnings": list
            }
        """
        template = self.template_manager.get_template(account_name)
        if not template:
            return {
                "valid": False,
                "missing_columns": [],
                "warnings": [f"No template found for account '{account_name}'"]
            }
        
        mappings = template.get("mappings", [])
        required_columns = set()
        
        # Collect required columns from mappings
        for mapping in mappings:
            mapping_type = mapping.get("mapping_type")
            
            if mapping_type in ["direct", "concatenate"]:
                source_column = mapping.get("source_column", "")
                if source_column:
                    if mapping_type == "concatenate":
                        # Parse comma-separated columns
                        cols = [c.strip() for c in source_column.split(",")]
                        required_columns.update(cols)
                    else:
                        required_columns.add(source_column)
        
        # Check which columns are missing
        df_columns = set(df.columns)
        missing_columns = required_columns - df_columns
        
        warnings = []
        if missing_columns:
            warnings.append(f"Missing {len(missing_columns)} required column(s)")
        
        return {
            "valid": len(missing_columns) == 0,
            "missing_columns": list(missing_columns),
            "warnings": warnings
        }


# Convenience functions
def process_dataframe_with_template(
    df: pd.DataFrame,
    account_name: str,
    row_index: Optional[int] = None
) -> Optional[pd.DataFrame]:
    """Process a DataFrame using account's PA template"""
    processor = PATemplateProcessor()
    return processor.process_dataframe(df, account_name, row_index)


def process_multiple_rows_with_template(
    df: pd.DataFrame,
    account_name: str,
    group_by_column: Optional[str] = None
) -> Dict[str, pd.DataFrame]:
    """Process multiple rows from DataFrame with grouping"""
    processor = PATemplateProcessor()
    return processor.process_multiple_rows(df, account_name, group_by_column)


def validate_dataframe_for_template(
    df: pd.DataFrame,
    account_name: str
) -> Dict[str, Any]:
    """Validate DataFrame compatibility with template"""
    processor = PATemplateProcessor()
    return processor.validate_template_compatibility(df, account_name)


# Example usage
if __name__ == "__main__":
    # Create sample DataFrame
    sample_data = {
        "Sub_ID": ["12345", "12346"],
        "Project_Code": ["HAB12345", "HAB12346"],
        "Language_Pair": ["en-US > fr-FR", "en-US > de-DE"],
        "Word_Count": [1500, 2000],
        "Due_Date": ["2025-01-15", "2025-01-20"],
        "Status": ["In Progress", "Ready"]
    }
    df = pd.DataFrame(sample_data)
    
    # Process with template (assuming CEVA template exists)
    processor = PATemplateProcessor()
    
    # Validate compatibility
    validation = processor.validate_template_compatibility(df, "CEVA")
    print(f"Validation: {validation}")
    
    # Process single row
    result = processor.process_dataframe(df, "CEVA", row_index=0)
    if result is not None:
        print("\nProcessed single row:")
        print(result)
    
    # Process multiple rows grouped by Sub_ID
    results = processor.process_multiple_rows(df, "CEVA", group_by_column="Sub_ID")
    print(f"\nProcessed {len(results)} groups")
    for sub_id, processed_df in results.items():
        print(f"\nSub_ID {sub_id}:")
        print(processed_df.head())
