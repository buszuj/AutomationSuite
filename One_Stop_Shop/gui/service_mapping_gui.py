"""
Service Mapping GUI
Maps entity service names to TPUS master services
"""

import customtkinter as ctk
from tkinter import messagebox
import sys
from pathlib import Path

# Add Core to path
core_path = Path(__file__).parent.parent.parent / "Core"
sys.path.insert(0, str(core_path))

from entity_service_mapper import EntityServiceMapper
import WF_Matrix


class ServiceMappingWindow:
    """Window for mapping entity services to master (TPUS) services"""
    
    def __init__(self, parent, entity_name):
        """
        Initialize service mapping window
        
        Args:
            parent: Parent window
            entity_name: Name of entity to map
        """
        self.entity_name = entity_name
        self.mapper = EntityServiceMapper()
        self.window = ctk.CTkToplevel(parent)
        self.window.title(f"Service Mapping - {entity_name} → TPUS")
        self.window.geometry("1000x700")
        
        # Keep window on top initially
        self.window.attributes('-topmost', True)
        self.window.after(100, lambda: self.window.attributes('-topmost', False))
        self.window.lift()
        self.window.focus_force()
        
        # Track modifications
        self.modified = False
        self.mapping_widgets = {}  # Store dropdown references
        
        # Prevent window from being garbage collected
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Load data
        self.master_services = self.mapper.get_master_services(WF_Matrix.PA_SERVICES)
        self.entity_services = self.mapper.get_entity_services(entity_name, WF_Matrix.PA_SERVICES)
        self.current_mappings = self.mapper.get_all_entity_mappings(entity_name)
        
        if not self.master_services:
            messagebox.showerror("Error", "No master services found in TPUS!")
            self.window.destroy()
            return
        
        if not self.entity_services:
            messagebox.showerror("Error", f"No services found in {entity_name}!")
            self.window.destroy()
            return
        
        self.setup_ui()
    
    def on_closing(self):
        """Handle window closing"""
        if self.modified:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?"
            )
            if response is True:  # Yes
                self.save_mappings()
            elif response is False:  # No
                self.window.destroy()
            # Cancel - do nothing
        else:
            self.window.destroy()
    
    def setup_ui(self):
        """Setup the mapping UI"""
        
        # Header section
        header_frame = ctk.CTkFrame(self.window)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"Map {self.entity_name} Services to TPUS Master Services",
            font=("Arial", 18, "bold")
        )
        title_label.pack(pady=10)
        
        info_label = ctk.CTkLabel(
            header_frame,
            text="Select the TPUS master service that corresponds to each entity service.\n"
                 "This ensures consistency when switching between entities.",
            font=("Arial", 11)
        )
        info_label.pack(pady=5)
        
        # Statistics
        stats_frame = ctk.CTkFrame(header_frame)
        stats_frame.pack(fill="x", pady=10)
        
        mapped_count = len([m for m in self.current_mappings.values() if m])
        total_count = len(self.entity_services)
        
        stats_label = ctk.CTkLabel(
            stats_frame,
            text=f"Mapped: {mapped_count} / {total_count}",
            font=("Arial", 12, "bold")
        )
        stats_label.pack(side="left", padx=20)
        
        # Quick actions
        auto_btn = ctk.CTkButton(
            stats_frame,
            text="Auto-Map Matching Names",
            command=self.auto_map_matching,
            width=180
        )
        auto_btn.pack(side="right", padx=5)
        
        # Scrollable mappings section
        mappings_frame = ctk.CTkScrollableFrame(self.window)
        mappings_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Header row
        header_row = ctk.CTkFrame(mappings_frame)
        header_row.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            header_row,
            text=f"{self.entity_name} Service Name",
            font=("Arial", 12, "bold"),
            width=400
        ).pack(side="left", padx=10)
        
        ctk.CTkLabel(
            header_row,
            text="→",
            font=("Arial", 16, "bold"),
            width=30
        ).pack(side="left")
        
        ctk.CTkLabel(
            header_row,
            text="TPUS Master Service",
            font=("Arial", 12, "bold"),
            width=400
        ).pack(side="left", padx=10)
        
        # Create mapping rows
        for entity_service in self.entity_services:
            self.create_mapping_row(mappings_frame, entity_service)
        
        # Button section
        button_frame = ctk.CTkFrame(self.window)
        button_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save Mappings",
            command=self.save_mappings,
            width=150,
            height=40,
            font=("Arial", 13, "bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        save_btn.pack(side="right", padx=5)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.window.destroy,
            width=100,
            height=40
        )
        cancel_btn.pack(side="right", padx=5)
    
    def create_mapping_row(self, parent, entity_service):
        """Create a single mapping row"""
        row_frame = ctk.CTkFrame(parent)
        row_frame.pack(fill="x", pady=5)
        
        # Entity service name (read-only)
        entity_label = ctk.CTkLabel(
            row_frame,
            text=entity_service,
            font=("Arial", 11),
            width=400,
            anchor="w"
        )
        entity_label.pack(side="left", padx=10)
        
        # Arrow
        arrow_label = ctk.CTkLabel(
            row_frame,
            text="→",
            font=("Arial", 14),
            width=30
        )
        arrow_label.pack(side="left")
        
        # Master service dropdown
        current_mapping = self.current_mappings.get(entity_service, "")
        
        # Add "(unmapped)" option
        dropdown_values = ["(unmapped)"] + self.master_services
        dropdown_value = current_mapping if current_mapping else "(unmapped)"
        
        dropdown = ctk.CTkComboBox(
            row_frame,
            values=dropdown_values,
            width=400,
            command=lambda choice, svc=entity_service: self.on_mapping_changed(svc, choice)
        )
        dropdown.set(dropdown_value)
        dropdown.pack(side="left", padx=10)
        
        # Store reference
        self.mapping_widgets[entity_service] = dropdown
    
    def on_mapping_changed(self, entity_service, master_service):
        """Handle mapping change"""
        self.modified = True
    
    def auto_map_matching(self):
        """Automatically map services with matching names"""
        mapped_count = 0
        
        for entity_service in self.entity_services:
            if entity_service in self.master_services:
                # Set dropdown to matching master service
                if entity_service in self.mapping_widgets:
                    self.mapping_widgets[entity_service].set(entity_service)
                    mapped_count += 1
                    self.modified = True
        
        messagebox.showinfo(
            "Auto-Mapping Complete",
            f"Automatically mapped {mapped_count} services with matching names.\n"
            "Please review and adjust as needed."
        )
    
    def save_mappings(self):
        """Save all mappings to file"""
        try:
            saved_count = 0
            
            for entity_service, dropdown in self.mapping_widgets.items():
                master_service = dropdown.get()
                
                if master_service == "(unmapped)":
                    # Remove mapping if exists
                    self.mapper.remove_mapping(self.entity_name, entity_service)
                else:
                    # Set mapping
                    self.mapper.set_mapping(self.entity_name, entity_service, master_service)
                    saved_count += 1
            
            self.modified = False
            messagebox.showinfo(
                "Success",
                f"Saved {saved_count} service mappings for {self.entity_name}!"
            )
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save mappings:\n{str(e)}")


def open_service_mapping(parent, entity_name):
    """
    Open service mapping window for an entity
    
    Args:
        parent: Parent window
        entity_name: Name of entity to map
    """
    ServiceMappingWindow(parent, entity_name)


# Standalone test
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    root.title("Service Mapping Test")
    root.geometry("400x300")
    
    title = ctk.CTkLabel(root, text="Service Mapping Manager", font=("Arial", 16, "bold"))
    title.pack(pady=20)
    
    # Test with TPTFR
    btn = ctk.CTkButton(
        root,
        text="Open TPTFR Mapping",
        command=lambda: open_service_mapping(root, "TPTFR"),
        width=200,
        height=40
    )
    btn.pack(pady=10)
    
    # Test with TPTDE
    btn2 = ctk.CTkButton(
        root,
        text="Open TPTDE Mapping",
        command=lambda: open_service_mapping(root, "TPTDE"),
        width=200,
        height=40
    )
    btn2.pack(pady=10)
    
    root.mainloop()
