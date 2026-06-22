"""
Launcher for One Stop Shop Main GUI
"""

import sys
from pathlib import Path



# ROOT = AUTOMATION/
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from one_stop_shop_main import OneStopShopMain

if __name__ == "__main__":
    app = OneStopShopMain()
    app.run()

    print(sys.path)