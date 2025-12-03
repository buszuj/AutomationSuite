"""
Quick launcher for testing Service Mapping GUI
"""

import customtkinter as ctk
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "gui"))

from gui.service_mapping_gui import open_service_mapping


def main():
    """Launch mapping GUI test"""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    root.title("Service Mapping Test Launcher")
    root.geometry("500x400")
    
    # Title
    title = ctk.CTkLabel(
        root,
        text="Service Mapping System",
        font=("Arial", 20, "bold")
    )
    title.pack(pady=30)
    
    # Info
    info = ctk.CTkLabel(
        root,
        text="Click a button to open the mapping window for that entity.\n"
             "Map entity service names to TPUS master services.",
        font=("Arial", 11)
    )
    info.pack(pady=10)
    
    # Buttons frame
    buttons_frame = ctk.CTkFrame(root)
    buttons_frame.pack(pady=20)
    
    # Add Core path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent / "Core"))
    from WF_Matrix import PA_SERVICES
    
    # Create button for each entity (except TPUS)
    for entity in sorted(PA_SERVICES.keys()):
        if entity == "TPUS":
            continue
        
        btn = ctk.CTkButton(
            buttons_frame,
            text=f"Map {entity} Services",
            command=lambda e=entity: open_service_mapping(root, e),
            width=250,
            height=40,
            font=("Arial", 13)
        )
        btn.pack(pady=5)
    
    # Footer
    footer = ctk.CTkLabel(
        root,
        text="TPUS is the master entity and doesn't need mapping",
        font=("Arial", 10),
        text_color="gray"
    )
    footer.pack(side="bottom", pady=20)
    
    root.mainloop()


if __name__ == "__main__":
    main()
