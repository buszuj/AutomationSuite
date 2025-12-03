"""
Quick test for service editor window
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import customtkinter as ctk
from gui.entity_manager_gui import ServiceEditorWindow
from Core import WF_Matrix

print("Testing Service Editor Window...")
print(f"Available entities: {list(WF_Matrix.PA_SERVICES.keys())}")

# Create a test window
ctk.set_appearance_mode("dark")
root = ctk.CTk()
root.title("Test Parent")
root.geometry("400x300")

def open_editor():
    print("Opening editor for TPUS...")
    try:
        editor = ServiceEditorWindow(root, "TPUS")
        print("✓ Editor window created successfully")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

# Add button to test
btn = ctk.CTkButton(root, text="Open TPUS Editor", command=open_editor)
btn.pack(pady=50)

print("\nClick the button to test the service editor...")
root.mainloop()
