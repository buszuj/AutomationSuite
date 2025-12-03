"""
Entity Manager Launcher
Quick launcher for the PA Services Entity Manager GUI
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from gui.entity_manager_gui import EntityManagerGUI


def main():
    """Launch the Entity Manager GUI"""
    print("Starting PA Services Entity Manager...")
    app = EntityManagerGUI()
    app.run()


if __name__ == "__main__":
    main()
