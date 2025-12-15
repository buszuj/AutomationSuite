"""
Launcher for One Stop Shop Main GUI
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from one_stop_shop_main import OneStopShopMain

if __name__ == "__main__":
    app = OneStopShopMain()
    app.run()
