"""
Test the add_entity_to_wf_matrix function directly
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from gui.entity_manager_gui import EntityManagerGUI
from Core import WF_Matrix

print("Testing entity creation function...")
print(f"Current entities before: {list(WF_Matrix.PA_SERVICES.keys())}")

# Create a dummy GUI instance (without running it)
class MockWindow:
    def mainloop(self):
        pass

# Create instance
manager = EntityManagerGUI.__new__(EntityManagerGUI)

# Test the function directly
try:
    print("\nTesting add_entity_to_wf_matrix('TPTEST', 'TPUS')...")
    result = manager.add_entity_to_wf_matrix('TPTEST', 'TPUS')
    print(f"Result: {result}")
    
    # Reload to see changes
    import importlib
    importlib.reload(WF_Matrix)
    
    print(f"\nCurrent entities after: {list(WF_Matrix.PA_SERVICES.keys())}")
    
    if 'TPTEST' in WF_Matrix.PA_SERVICES:
        print("✓ TPTEST successfully created!")
        print(f"  Services count: {len(WF_Matrix.PA_SERVICES['TPTEST']) - 1}")
    else:
        print("✗ TPTEST was not found in PA_SERVICES")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
