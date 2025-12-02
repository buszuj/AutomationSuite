"""
One Stop Shop - Main Entry Point
Multi-scenario automation processor.
"""

import sys
from pathlib import Path

# Add Core to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from Core.excel_io import excel_handler
from Core.df_processing import df_processor
from Core.validators import validator
from Core.utils.logger import get_logger
from Core.utils.helpers import load_yaml

# Initialize logger
logger = get_logger('OneStopShop')


class OneStopShop:
    """Main class for One Stop Shop automation."""
    
    def __init__(self, config_file: str = None):
        """Initialize One Stop Shop."""
        self.config_file = config_file or 'oss_config.yaml'
        self.config = self._load_config()
        logger.info("One Stop Shop initialized")
    
    def _load_config(self):
        """Load configuration from file."""
        config_path = Path(__file__).parent / self.config_file
        if config_path.exists():
            return load_yaml(config_path)
        return {}
    
    def run(self):
        """Main execution method."""
        logger.info("One Stop Shop started")
        # Add your main logic here
        pass


if __name__ == '__main__':
    app = OneStopShop()
    app.run()
