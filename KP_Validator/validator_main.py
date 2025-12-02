"""
KP Validator - Main Entry Point
Validation automation tool.
"""

import sys
import json
from pathlib import Path

# Add Core to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from Core.excel_io import excel_handler
from Core.df_processing import df_processor
from Core.validators import validator
from Core.utils.logger import get_logger
from Core.utils.helpers import load_json

# Initialize logger
logger = get_logger('KPValidator')


class KPValidator:
    """Main class for KP validation automation."""
    
    def __init__(self, rules_file: str = None):
        """Initialize KP Validator."""
        self.rules_file = rules_file or 'validator_rules.json'
        self.rules = self._load_rules()
        logger.info("KP Validator initialized")
    
    def _load_rules(self):
        """Load validation rules from file."""
        rules_path = Path(__file__).parent / self.rules_file
        if rules_path.exists():
            return load_json(rules_path)
        return {}
    
    def validate_data(self, data):
        """Validate data against rules."""
        logger.info("Starting validation")
        # Add validation logic here
        return True
    
    def run(self, input_file: str):
        """Main execution method."""
        logger.info(f"KP Validator started for {input_file}")
        
        # Load data
        data = excel_handler.read_excel(input_file)
        
        # Validate
        is_valid = self.validate_data(data)
        
        if is_valid:
            logger.info("Validation passed")
        else:
            logger.error("Validation failed")
        
        return is_valid


if __name__ == '__main__':
    validator_app = KPValidator()
    # Add your file path here
    # validator_app.run('path/to/file.xlsx')
