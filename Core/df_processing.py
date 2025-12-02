"""
Core DataFrame Processing Module
Common data processing operations shared across all projects.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Union, Any, Callable


class DataFrameProcessor:
    """Centralized DataFrame processing operations."""
    
    @staticmethod
    def clean_dataframe(
        df: pd.DataFrame,
        drop_na: bool = False,
        fill_value: Any = None,
        strip_strings: bool = True
    ) -> pd.DataFrame:
        """
        Clean DataFrame with common operations.
        
        Args:
            df: Input DataFrame
            drop_na: Whether to drop rows with NA values
            fill_value: Value to fill NAs with (if drop_na is False)
            strip_strings: Strip whitespace from string columns
            
        Returns:
            Cleaned DataFrame
        """
        df_clean = df.copy()
        
        if strip_strings:
            for col in df_clean.select_dtypes(include=['object']).columns:
                df_clean[col] = df_clean[col].str.strip() if df_clean[col].dtype == 'object' else df_clean[col]
        
        if drop_na:
            df_clean = df_clean.dropna()
        elif fill_value is not None:
            df_clean = df_clean.fillna(fill_value)
        
        return df_clean
    
    @staticmethod
    def filter_dataframe(
        df: pd.DataFrame,
        filters: dict,
        match_all: bool = True
    ) -> pd.DataFrame:
        """
        Filter DataFrame based on column conditions.
        
        Args:
            df: Input DataFrame
            filters: Dict of {column: value} or {column: callable}
            match_all: If True, all conditions must match (AND), else any (OR)
            
        Returns:
            Filtered DataFrame
        """
        if not filters:
            return df
        
        masks = []
        for col, condition in filters.items():
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame")
            
            if callable(condition):
                masks.append(condition(df[col]))
            else:
                masks.append(df[col] == condition)
        
        if match_all:
            final_mask = pd.concat(masks, axis=1).all(axis=1)
        else:
            final_mask = pd.concat(masks, axis=1).any(axis=1)
        
        return df[final_mask]
    
    @staticmethod
    def merge_dataframes(
        left: pd.DataFrame,
        right: pd.DataFrame,
        on: Union[str, List[str]],
        how: str = 'inner',
        suffixes: tuple = ('_left', '_right')
    ) -> pd.DataFrame:
        """
        Merge two DataFrames with error handling.
        
        Args:
            left: Left DataFrame
            right: Right DataFrame
            on: Column(s) to merge on
            how: Type of merge ('inner', 'outer', 'left', 'right')
            suffixes: Suffixes for overlapping columns
            
        Returns:
            Merged DataFrame
        """
        try:
            return pd.merge(left, right, on=on, how=how, suffixes=suffixes)
        except Exception as e:
            raise Exception(f"Error merging DataFrames: {str(e)}")
    
    @staticmethod
    def pivot_dataframe(
        df: pd.DataFrame,
        index: Union[str, List[str]],
        columns: str,
        values: str,
        aggfunc: Union[str, Callable] = 'sum'
    ) -> pd.DataFrame:
        """
        Create pivot table from DataFrame.
        
        Args:
            df: Input DataFrame
            index: Column(s) to use as index
            columns: Column to pivot on
            values: Column with values
            aggfunc: Aggregation function
            
        Returns:
            Pivoted DataFrame
        """
        return pd.pivot_table(
            df,
            index=index,
            columns=columns,
            values=values,
            aggfunc=aggfunc,
            fill_value=0
        )
    
    @staticmethod
    def validate_columns(
        df: pd.DataFrame,
        required_columns: List[str],
        raise_error: bool = True
    ) -> bool:
        """
        Validate that DataFrame has required columns.
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            raise_error: Whether to raise error if validation fails
            
        Returns:
            True if valid, False otherwise
        """
        missing_cols = set(required_columns) - set(df.columns)
        
        if missing_cols:
            error_msg = f"Missing required columns: {missing_cols}"
            if raise_error:
                raise ValueError(error_msg)
            return False
        
        return True
    
    @staticmethod
    def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names (lowercase, replace spaces with underscores)."""
        df_normalized = df.copy()
        df_normalized.columns = [
            col.lower().replace(' ', '_').replace('-', '_')
            for col in df.columns
        ]
        return df_normalized


# Singleton instance
df_processor = DataFrameProcessor()
