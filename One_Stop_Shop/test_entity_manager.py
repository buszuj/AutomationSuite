"""
Quick test script for Entity Manager GUI
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

print("Testing Entity Manager GUI...")
print(f"Python path: {sys.path}")

try:
    from gui.entity_manager_gui import EntityManagerGUI
    print("✓ Successfully imported EntityManagerGUI")
    
    from Core import WF_Matrix
    print("✓ Successfully imported WF_Matrix")
    print(f"✓ Current entities: {list(WF_Matrix.PA_SERVICES.keys())}")
    
    print("\nAll imports successful! Ready to launch GUI.")
    print("\nTo launch the GUI, run:")
    print("  python launch_entity_manager.py")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
