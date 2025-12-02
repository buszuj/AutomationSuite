"""
Excel to DataFrame Processing Template
Template for reading Excel data and processing it with pandas.

Use this template when you need to:
- Load Excel data
- Clean and transform data
- Perform calculations
- Export results
"""

import sys
from pathlib import Path

# Add Core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Core.excel_io import excel_handler
from Core.utils.logger import get_logger
import pandas as pd
import numpy as np

# Initialize logger
logger = get_logger(__name__)


class ExcelDataProcessor:
    """
    Template class for Excel data processing.
    Customize this class for your specific data processing needs.
    """
    
    def __init__(self, input_file: str, sheet_name: str = "Sheet1"):
        """
        Initialize the processor.
        
        Args:
            input_file: Path to input Excel file
            sheet_name: Sheet name to read
        """
        self.input_file = Path(input_file)
        self.sheet_name = sheet_name
        self.raw_data = None
        self.processed_data = None
        logger.info(f"Initialized processor for {input_file}")
    
    def load_data(self) -> bool:
        """Load data from Excel file."""
        try:
            self.raw_data = excel_handler.read_excel(
                self.input_file,
                sheet_name=self.sheet_name
            )
            logger.info(f"Loaded {len(self.raw_data)} rows, {len(self.raw_data.columns)} columns")
            return True
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return False
    
    def validate_data(self) -> bool:
        """Validate data structure and content."""
        if self.raw_data is None:
            logger.error("No data loaded")
            return False
        
        # TODO: Add your validation logic here
        # Example validations:
        
        # Check for required columns
        required_columns = ["Column1", "Column2", "Column3"]
        missing_columns = [col for col in required_columns if col not in self.raw_data.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return False
        
        # Check for empty DataFrame
        if self.raw_data.empty:
            logger.error("DataFrame is empty")
            return False
        
        # Check for missing data
        if self.raw_data.isnull().any().any():
            null_counts = self.raw_data.isnull().sum()
            logger.warning(f"Found missing values:\n{null_counts[null_counts > 0]}")
        
        logger.info("Data validation passed")
        return True
    
    def clean_data(self):
        """Clean and prepare data for processing."""
        df = self.raw_data.copy()
        
        # TODO: Add your cleaning logic here
        # Examples:
        
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Fill missing values
        df = df.fillna({
            'NumericColumn': 0,
            'TextColumn': '',
        })
        
        # Strip whitespace from string columns
        string_columns = df.select_dtypes(include=['object']).columns
        df[string_columns] = df[string_columns].apply(lambda x: x.str.strip())
        
        # Convert data types
        # df['DateColumn'] = pd.to_datetime(df['DateColumn'])
        # df['NumericColumn'] = pd.to_numeric(df['NumericColumn'], errors='coerce')
        
        self.processed_data = df
        logger.info("Data cleaning complete")
    
    def transform_data(self):
        """Transform and enrich data."""
        df = self.processed_data.copy()
        
        # TODO: Add your transformation logic here
        # Examples:
        
        # Create calculated columns
        # df['Total'] = df['Quantity'] * df['Price']
        
        # Add categorization
        # df['Category'] = df['Value'].apply(lambda x: 'High' if x > 100 else 'Low')
        
        # Group and aggregate
        # summary = df.groupby('Group').agg({
        #     'Value': ['sum', 'mean', 'count']
        # })
        
        self.processed_data = df
        logger.info("Data transformation complete")
    
    def analyze_data(self) -> dict:
        """Perform analysis on the data."""
        df = self.processed_data
        
        # TODO: Add your analysis logic here
        # Examples:
        
        analysis_results = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'memory_usage': df.memory_usage(deep=True).sum(),
        }
        
        # Numeric column statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            analysis_results['numeric_stats'] = df[numeric_cols].describe().to_dict()
        
        # Categorical column value counts
        categorical_cols = df.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            analysis_results['value_counts'] = {
                col: df[col].value_counts().to_dict()
                for col in categorical_cols[:5]  # First 5 categorical columns
            }
        
        logger.info("Data analysis complete")
        return analysis_results
    
    def export_results(self, output_file: str):
        """Export processed data to Excel."""
        if self.processed_data is None:
            logger.error("No processed data to export")
            return False
        
        try:
            excel_handler.write_excel(
                self.processed_data,
                output_file,
                sheet_name="Processed Data"
            )
            logger.info(f"Results exported to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            return False
    
    def process(self) -> bool:
        """
        Run the complete processing pipeline.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting data processing pipeline")
        
        # Step 1: Load data
        if not self.load_data():
            return False
        
        # Step 2: Validate data
        if not self.validate_data():
            return False
        
        # Step 3: Clean data
        self.clean_data()
        
        # Step 4: Transform data
        self.transform_data()
        
        # Step 5: Analyze data
        analysis = self.analyze_data()
        logger.info(f"Analysis results: {analysis}")
        
        logger.info("Data processing pipeline complete")
        return True


def example_usage():
    """Example of how to use the ExcelDataProcessor."""
    
    # Define input and output files
    input_file = "input_data.xlsx"
    output_file = "processed_data.xlsx"
    
    # Create processor instance
    processor = ExcelDataProcessor(input_file, sheet_name="Sheet1")
    
    # Run processing pipeline
    if processor.process():
        # Export results
        processor.export_results(output_file)
        
        # Access processed data if needed
        df = processor.processed_data
        print("\nProcessed Data Preview:")
        print(df.head())
        
        print("\n✅ Processing complete!")
    else:
        print("\n❌ Processing failed!")


def main():
    """Main entry point."""
    print("="*60)
    print("Excel to DataFrame Processing Template")
    print("="*60 + "\n")
    
    # Run example
    example_usage()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
