"""
Launch Workflow Manager
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "Core"))

from gui.workflow_manager_gui import WorkflowManagerGUI


def main():
    """Main entry point"""
    app = WorkflowManagerGUI()
    app.run()


if __name__ == "__main__":
    main()
