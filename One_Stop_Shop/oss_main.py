"""
One Stop Shop - Main Application
Translation service quote calculator with UI integration.
Refactored version integrating TheOneBP functionality with AutomationSuite Core.
"""

import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# Import the original MainScript functionality
# This keeps the UI-heavy code together while leveraging Core modules
from One_Stop_Shop.theonebp_app import TheOneBPApp


def main():
    """Main entry point for One Stop Shop application."""
    app = TheOneBPApp()
    app.run()


if __name__ == '__main__':
    main()
