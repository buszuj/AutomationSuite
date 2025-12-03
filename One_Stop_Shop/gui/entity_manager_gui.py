"""
Entity Manager GUI
Allows users to create, view, and manage PA Service entities in WF_Matrix.py
"""

import customtkinter as ctk
from tkinter import messagebox, scrolledtext, ttk
import sys
from pathlib import Path
import re

# Add Core to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Core import WF_Matrix


class ServiceEditorWindow:
    """Window for viewing and editing services for a specific entity"""
    
    def __init__(self, parent, entity_name, on_save_callback=None):
        """
        Initialize service editor window
        
        Args:
            parent: Parent window
            entity_name: Name of entity to edit
            on_save_callback: Callback function when services are saved
        """
        self.entity_name = entity_name
        self.on_save_callback = on_save_callback
        self.window = ctk.CTkToplevel(parent)
        self.window.title(f"Edit Services - {entity_name}")
        self.window.geometry("900x700")
        
        # Keep window on top and grab focus
        self.window.attributes('-topmost', True)  # Stay on top of all windows
        self.window.after(100, lambda: self.window.attributes('-topmost', False))  # Remove topmost after showing
        self.window.lift()
        self.window.focus_force()
        
        # Prevent window from being garbage collected
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        try:
            # Store original services for comparison
            import importlib
            importlib.reload(WF_Matrix)
            
            if entity_name not in WF_Matrix.PA_SERVICES:
                messagebox.showerror("Error", f"Entity '{entity_name}' not found in WF_Matrix!")
                self.window.destroy()
                return
            
            self.services = [row.copy() for row in WF_Matrix.PA_SERVICES[entity_name]]
            self.modified = False
            
            self.setup_ui()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load services:\n{str(e)}")
            self.window.destroy()
            raise
    
    def on_closing(self):
        """Handle window closing"""
        if self.modified:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?"
            )
            if response is True:  # Yes
                self.save_changes()
            elif response is False:  # No
                self.window.destroy()
            # Cancel - do nothing
        else:
            self.window.destroy()
        
    def setup_ui(self):
        """Setup the editor UI"""
        
        # Header
        header_frame = ctk.CTkFrame(self.window)
        header_frame.pack(fill="x", padx=20, pady=20)
        
        title = ctk.CTkLabel(
            header_frame,
            text=f"{self.entity_name} - Services Editor",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(side="left")
        
        # Service count
        service_count = len(self.services) - 1  # Exclude header
        count_label = ctk.CTkLabel(
            header_frame,
            text=f"{service_count} services",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        count_label.pack(side="left", padx=20)
        
        # Table frame
        table_frame = ctk.CTkFrame(self.window)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Create scrollable frame for table
        self.scroll_frame = ctk.CTkScrollableFrame(table_frame, height=500)
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Header row
        header_bg = ctk.CTkFrame(self.scroll_frame, fg_color="#2b2b2b")
        header_bg.pack(fill="x", pady=(0, 10))
        
        headers = ["#", "Service Group 1", "Service Group 2", "Service", "UofM", "Actions"]
        col_widths = [40, 150, 150, 200, 80, 100]
        
        for i, (header, width) in enumerate(zip(headers, col_widths)):
            label = ctk.CTkLabel(
                header_bg,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=width
            )
            label.grid(row=0, column=i, padx=5, pady=10, sticky="w")
        
        # Data rows (skip header row in services)
        self.entry_widgets = []
        for idx, service in enumerate(self.services[1:], 1):
            self.create_service_row(idx, service)
        
        # Button frame
        button_frame = ctk.CTkFrame(self.window)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Add new service button
        add_btn = ctk.CTkButton(
            button_frame,
            text="➕ Add New Service",
            command=self.add_new_service,
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="#3498db",
            hover_color="#2980b9"
        )
        add_btn.pack(side="left", padx=(0, 10))
        
        # Save button
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Save Changes",
            command=self.save_changes,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#2ecc71",
            hover_color="#27ae60"
        )
        save_btn.pack(side="right", padx=(0, 10))
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.window.destroy,
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="#95a5a6",
            hover_color="#7f8c8d"
        )
        cancel_btn.pack(side="right")
        
    def create_service_row(self, row_num, service):
        """Create a row for editing a service"""
        
        row_frame = ctk.CTkFrame(self.scroll_frame)
        row_frame.pack(fill="x", pady=2)
        
        # Row number
        num_label = ctk.CTkLabel(row_frame, text=str(row_num), width=40)
        num_label.grid(row=0, column=0, padx=5, pady=5)
        
        # Entry fields
        entries = []
        col_widths = [150, 150, 200, 80]
        
        def on_entry_change(*args):
            self.modified = True
        
        for col_idx, (value, width) in enumerate(zip(service, col_widths), 1):
            entry = ctk.CTkEntry(row_frame, width=width)
            entry.insert(0, str(value))
            entry.grid(row=0, column=col_idx, padx=5, pady=5)
            # Bind change event
            entry.bind('<KeyRelease>', on_entry_change)
            entries.append(entry)
        
        # Delete button
        delete_btn = ctk.CTkButton(
            row_frame,
            text="🗑️",
            command=lambda: self.delete_service_row(row_frame, row_num),
            width=60,
            height=30,
            fg_color="#e74c3c",
            hover_color="#c0392b"
        )
        delete_btn.grid(row=0, column=5, padx=5, pady=5)
        
        self.entry_widgets.append((row_frame, entries, row_num))
        
    def add_new_service(self):
        """Add a new blank service row"""
        new_row_num = len(self.entry_widgets) + 1
        new_service = ["", "", "", ""]
        self.create_service_row(new_row_num, new_service)
        self.modified = True
        
    def delete_service_row(self, row_frame, row_num):
        """Delete a service row"""
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete service #{row_num}?"
        )
        
        if confirm:
            row_frame.destroy()
            # Remove from entry_widgets
            self.entry_widgets = [(f, e, n) for f, e, n in self.entry_widgets if f != row_frame]
            self.modified = True
            # Renumber remaining rows
            for idx, (frame, entries, old_num) in enumerate(self.entry_widgets, 1):
                # Update row number label
                for widget in frame.winfo_children():
                    if isinstance(widget, ctk.CTkLabel):
                        widget.configure(text=str(idx))
                        break
            
    def save_changes(self):
        """Save changes to WF_Matrix.py"""
        
        # Collect all services from entry widgets
        new_services = [self.services[0]]  # Keep header
        
        for frame, entries, _ in self.entry_widgets:
            if frame.winfo_exists():  # Check if not deleted
                service = [entry.get() for entry in entries]
                new_services.append(service)
        
        if len(new_services) == 1:  # Only header
            messagebox.showerror("Error", "Cannot save entity with no services!")
            return
        
        # Update WF_Matrix.py
        try:
            # If this is TPUS (master), detect new services and sync to other entities
            if self.entity_name == "TPUS":
                old_master_services = [row[2] for row in self.services[1:]]  # Old service names
                new_master_services = [row[2] for row in new_services[1:]]  # New service names
                added_services = [s for s in new_master_services if s not in old_master_services]
                
                if added_services:
                    # Import mapper to sync
                    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "Core"))
                    from entity_service_mapper import EntityServiceMapper
                    mapper = EntityServiceMapper()
                    
                    # Ask user if they want to sync
                    sync_response = messagebox.askyesno(
                        "Sync Master Services",
                        f"You added {len(added_services)} new service(s) to TPUS:\n" +
                        "\n".join(f"  • {s}" for s in added_services) +
                        "\n\nDo you want to add these to all other entities?\n" +
                        "(They will use the same name by default, but you can edit them later)"
                    )
                    
                    if sync_response:
                        # Update all entities
                        for service_name in added_services:
                            mapper.update_all_entities_with_new_master_service(service_name, WF_Matrix.PA_SERVICES)
            
            self.update_services_in_file(new_services)
            messagebox.showinfo("Success", f"Services for {self.entity_name} saved successfully!")
            self.modified = False
            
            if self.on_save_callback:
                self.on_save_callback()
            
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save services:\n{str(e)}")
    
    def update_services_in_file(self, new_services):
        """Update services in WF_Matrix.py file"""
        
        wf_matrix_path = Path(__file__).parent.parent.parent / "Core" / "WF_Matrix.py"
        
        with open(wf_matrix_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find the entity list definition
        variable_name = f"{self.entity_name}_PA_SERVICES"
        start_line = -1
        end_line = -1
        bracket_count = 0
        
        for i, line in enumerate(lines):
            if f"{variable_name} = [" in line:
                start_line = i
                bracket_count = line.count('[') - line.count(']')
            elif start_line != -1:
                bracket_count += line.count('[') - line.count(']')
                if bracket_count == 0:
                    end_line = i
                    break
        
        if start_line == -1:
            raise Exception(f"Could not find {variable_name} in WF_Matrix.py")
        
        # Generate new lines
        new_lines = [f"{variable_name} = [\n"]
        for service in new_services:
            new_lines.append(f"    {service},\n")
        new_lines.append("]\n")
        
        # Replace old definition with new one
        lines = lines[:start_line] + new_lines + lines[end_line + 1:]
        
        # Write back
        with open(wf_matrix_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)


class EntityManagerGUI:
    """GUI for managing PA Service entities"""
    
    def __init__(self, parent=None):
        """
        Initialize the Entity Manager GUI
        
        Args:
            parent: Parent window (optional). If None, creates standalone window.
        """
        if parent:
            self.window = ctk.CTkToplevel(parent)
        else:
            self.window = ctk.CTk()
            
        self.window.title("PA Services Entity Manager")
        self.window.geometry("800x600")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Store reference to open editor windows
        self.editor_windows = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        
        # Main container
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="PA Services Entity Manager",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Create two columns
        columns_frame = ctk.CTkFrame(main_frame)
        columns_frame.pack(fill="both", expand=True)
        
        # Left column - Entity creation
        left_frame = ctk.CTkFrame(columns_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.setup_creation_panel(left_frame)
        
        # Right column - Entity list
        right_frame = ctk.CTkFrame(columns_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        self.setup_entity_list_panel(right_frame)
        
    def setup_creation_panel(self, parent):
        """Setup the entity creation panel"""
        
        # Header
        header = ctk.CTkLabel(
            parent,
            text="Create New Entity",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header.pack(pady=(10, 20))
        
        # Entity name input
        input_frame = ctk.CTkFrame(parent)
        input_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(
            input_frame,
            text="Entity Name:",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", pady=(10, 5))
        
        self.entity_name_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="e.g., TPIT, TPFR, TPUK",
            font=ctk.CTkFont(size=14),
            height=40
        )
        self.entity_name_entry.pack(fill="x", pady=(0, 5))
        
        # Info label
        info_label = ctk.CTkLabel(
            input_frame,
            text="Entity name will be automatically uppercased\nand formatted as: ENTITYNAME_PA_SERVICES",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        info_label.pack(pady=(5, 10))
        
        # Copy from existing entity option
        copy_frame = ctk.CTkFrame(parent)
        copy_frame.pack(fill="x", padx=20, pady=(10, 10))
        
        ctk.CTkLabel(
            copy_frame,
            text="Copy Services From (optional):",
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", pady=(10, 5))
        
        # Get existing entities
        existing_entities = list(WF_Matrix.PA_SERVICES.keys())
        
        self.copy_from_combo = ctk.CTkComboBox(
            copy_frame,
            values=["None"] + existing_entities,
            font=ctk.CTkFont(size=14),
            height=40
        )
        self.copy_from_combo.set("None")
        self.copy_from_combo.pack(fill="x", pady=(0, 10))
        
        # Create button
        self.create_button = ctk.CTkButton(
            parent,
            text="Create Entity",
            command=self.create_entity,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            fg_color="#2ecc71",
            hover_color="#27ae60"
        )
        self.create_button.pack(pady=(20, 10), padx=20, fill="x")
        
        # Status label
        self.status_label = ctk.CTkLabel(
            parent,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#95a5a6"
        )
        self.status_label.pack(pady=(10, 20))
        
    def setup_entity_list_panel(self, parent):
        """Setup the entity list panel"""
        
        # Header
        header = ctk.CTkLabel(
            parent,
            text="Existing Entities",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        header.pack(pady=(10, 20))
        
        # Button frame for refresh and sync
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(pady=(0, 10))
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Refresh",
            command=self.refresh_entity_list,
            font=ctk.CTkFont(size=12),
            height=30,
            width=100
        )
        refresh_btn.pack(side="left", padx=5)
        
        # Sync button
        sync_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Sync All",
            command=self.sync_all_entities,
            font=ctk.CTkFont(size=12),
            height=30,
            width=100,
            fg_color="#e67e22",
            hover_color="#d35400"
        )
        sync_btn.pack(side="left", padx=5)
        
        # Entity list with scrollbar
        list_frame = ctk.CTkFrame(parent)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Create scrollable frame
        self.entity_list_frame = ctk.CTkScrollableFrame(list_frame)
        self.entity_list_frame.pack(fill="both", expand=True)
        
        # Initial load
        self.refresh_entity_list()
        
    def refresh_entity_list(self):
        """Refresh the entity list display"""
        
        # Clear existing widgets
        for widget in self.entity_list_frame.winfo_children():
            widget.destroy()
        
        # Reload WF_Matrix to get latest data
        import importlib
        importlib.reload(WF_Matrix)
        
        # Display entities
        entities = WF_Matrix.PA_SERVICES
        
        if not entities:
            no_entities_label = ctk.CTkLabel(
                self.entity_list_frame,
                text="No entities found",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            no_entities_label.pack(pady=20)
            return
        
        for entity_name, services in entities.items():
            # Entity card
            entity_card = ctk.CTkFrame(self.entity_list_frame, fg_color="#2b2b2b")
            entity_card.pack(fill="x", pady=5, padx=5)
            
            # Left side - Entity info
            info_frame = ctk.CTkFrame(entity_card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            
            # Entity name
            name_label = ctk.CTkLabel(
                info_frame,
                text=entity_name,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            name_label.pack(anchor="w")
            
            # Service count (excluding header)
            service_count = len(services) - 1
            count_label = ctk.CTkLabel(
                info_frame,
                text=f"{service_count} services",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            count_label.pack(anchor="w")
            
            # Right side - Action buttons
            button_frame = ctk.CTkFrame(entity_card, fg_color="transparent")
            button_frame.pack(side="right", padx=10, pady=10)
            
            # Edit Services button
            edit_btn = ctk.CTkButton(
                button_frame,
                text="📝 Edit Services",
                command=lambda e=entity_name: self.open_service_editor(e),
                width=120,
                height=32,
                fg_color="#3498db",
                hover_color="#2980b9"
            )
            edit_btn.pack(pady=(0, 5))
            
            # Map Services button (skip for TPUS - it's the master)
            if entity_name != "TPUS":
                map_btn = ctk.CTkButton(
                    button_frame,
                    text="🔗 Map Services",
                    command=lambda e=entity_name: self.open_service_mapping(e),
                    width=120,
                    height=32,
                    fg_color="#9b59b6",
                    hover_color="#8e44ad"
                )
                map_btn.pack(pady=(0, 5))
                
                # Delete Entity button (skip for TPUS - it's the master)
                delete_btn = ctk.CTkButton(
                    button_frame,
                    text="🗑️ Delete",
                    command=lambda e=entity_name: self.delete_entity(e),
                    width=120,
                    height=32,
                    fg_color="#e74c3c",
                    hover_color="#c0392b"
                )
                delete_btn.pack()
        
        # Update combo box in creation panel
        self.copy_from_combo.configure(values=["None"] + list(entities.keys()))
    
    def open_service_editor(self, entity_name):
        """Open the service editor window for an entity"""
        try:
            # Create and store reference to editor window
            editor = ServiceEditorWindow(self.window, entity_name, on_save_callback=self.refresh_entity_list)
            self.editor_windows.append(editor)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open service editor:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def open_service_mapping(self, entity_name):
        """Open the service mapping window for an entity"""
        try:
            # Dynamic import to avoid circular dependency
            from gui.service_mapping_gui import ServiceMappingWindow
            
            # Create and store reference to mapping window
            mapper = ServiceMappingWindow(self.window, entity_name)
            self.editor_windows.append(mapper)
        except ImportError as ie:
            messagebox.showerror(
                "Import Error",
                f"Service mapping functionality is not available:\n{str(ie)}\n\n"
                "Please check that service_mapping_gui.py is in the gui folder."
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open service mapping:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def sync_all_entities(self):
        """Synchronize all entities to match TPUS master services"""
        try:
            # Import sync module
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "Core"))
            from sync_entities import sync_all_entities_to_master, get_sync_status
            
            # Get current status
            status = get_sync_status()
            out_of_sync = [e for e, info in status.items() if not info["in_sync"] and e != "TPUS"]
            
            if not out_of_sync:
                messagebox.showinfo(
                    "Already Synchronized",
                    "All entities are already in sync with TPUS!"
                )
                return
            
            # Show what will be synced
            msg_lines = ["The following entities are out of sync:\n"]
            for entity in out_of_sync:
                missing = status[entity]["missing"]
                msg_lines.append(f"• {entity}: missing {missing} service(s)")
            
            msg_lines.append("\n\nMissing services will be added with the same")
            msg_lines.append("name as TPUS. You can edit them later.")
            msg_lines.append("\n\nDo you want to synchronize now?")
            
            confirm = messagebox.askyesno(
                "Synchronize Entities",
                "\n".join(msg_lines)
            )
            
            if not confirm:
                return
            
            # Perform sync
            success = sync_all_entities_to_master()
            
            if success:
                messagebox.showinfo(
                    "Success",
                    "All entities have been synchronized with TPUS master services!"
                )
                self.refresh_entity_list()
            else:
                messagebox.showinfo(
                    "No Changes",
                    "All entities were already in sync."
                )
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to sync entities:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def delete_entity(self, entity_name):
        """Delete an entity from WF_Matrix.py"""
        if entity_name == "TPUS":
            messagebox.showerror(
                "Cannot Delete Master",
                "TPUS is the master entity and cannot be deleted!"
            )
            return
        
        # Confirmation with details
        import importlib
        importlib.reload(WF_Matrix)
        
        service_count = len(WF_Matrix.PA_SERVICES.get(entity_name, [])) - 1
        
        confirm = messagebox.askyesno(
            "Delete Entity",
            f"Are you sure you want to delete entity '{entity_name}'?\n\n"
            f"This will permanently remove:\n"
            f"• {service_count} services\n"
            f"• Service mappings\n"
            f"• All related configurations\n\n"
            f"This action cannot be undone!"
        )
        
        if not confirm:
            return
        
        # Double confirmation
        double_confirm = messagebox.askyesno(
            "Final Confirmation",
            f"LAST CHANCE!\n\n"
            f"Delete '{entity_name}' permanently?\n\n"
            f"Type the entity name to confirm:",
            icon="warning"
        )
        
        if not double_confirm:
            return
        
        try:
            wf_matrix_path = Path(__file__).parent.parent.parent / "Core" / "WF_Matrix.py"
            
            with open(wf_matrix_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find and remove entity list definition
            variable_name = f"{entity_name}_PA_SERVICES"
            start_line = -1
            end_line = -1
            bracket_count = 0
            
            # Find list definition
            for i, line in enumerate(lines):
                if f"{variable_name} = [" in line or f"# List of {entity_name}" in line:
                    if start_line == -1:
                        start_line = i
                        if "# List" in line:
                            continue
                if start_line != -1 and f"{variable_name} = [" in line:
                    bracket_count = line.count('[') - line.count(']')
                elif start_line != -1 and bracket_count > 0:
                    bracket_count += line.count('[') - line.count(']')
                    if bracket_count == 0:
                        end_line = i
                        break
            
            if start_line != -1 and end_line != -1:
                # Remove list definition (including comment)
                del lines[start_line:end_line + 2]  # +2 to include newline after
            
            # Remove from PA_SERVICES dictionary
            new_lines = []
            skip_next = False
            for line in lines:
                if f'"{entity_name}":' in line and "_PA_SERVICES" in line:
                    skip_next = True
                    continue
                if skip_next:
                    skip_next = False
                    continue
                new_lines.append(line)
            
            # Write back
            with open(wf_matrix_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            # Remove mappings
            try:
                sys.path.insert(0, str(Path(__file__).parent.parent.parent / "Core"))
                from entity_service_mapper import EntityServiceMapper
                mapper = EntityServiceMapper()
                if entity_name in mapper.mappings.get("mappings", {}):
                    del mapper.mappings["mappings"][entity_name]
                    mapper.save_mappings()
            except:
                pass  # Mapping removal is not critical
            
            messagebox.showinfo(
                "Success",
                f"Entity '{entity_name}' has been deleted successfully!"
            )
            
            self.refresh_entity_list()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete entity:\n{str(e)}")
            import traceback
            traceback.print_exc()
        
    def validate_entity_name(self, name):
        """
        Validate entity name
        
        Args:
            name (str): Entity name to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not name:
            return False, "Entity name cannot be empty"
        
        # Remove whitespace
        name = name.strip()
        
        if not name:
            return False, "Entity name cannot be empty"
        
        # Check if contains only alphanumeric characters
        if not re.match(r'^[A-Za-z0-9]+$', name):
            return False, "Entity name must contain only letters and numbers"
        
        # Reload WF_Matrix to check for latest entities
        import importlib
        importlib.reload(WF_Matrix)
        
        # Check if already exists (case-insensitive)
        existing_entities = [e.upper() for e in WF_Matrix.PA_SERVICES.keys()]
        if name.upper() in existing_entities:
            return False, f"Entity '{name.upper()}' already exists!\n\nDuplicate entities are not allowed.\nPlease choose a different name."
        
        # Check in file to catch entities not yet in PA_SERVICES dict
        wf_matrix_path = Path(__file__).parent.parent.parent / "Core" / "WF_Matrix.py"
        with open(wf_matrix_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        variable_name = f"{name.upper()}_PA_SERVICES"
        if variable_name in content:
            return False, f"Entity '{name.upper()}' already exists in WF_Matrix.py!\n\nDuplicate entities are not allowed.\nPlease choose a different name or refresh the entity list."
        
        return True, ""
    
    def create_entity(self):
        """Create a new entity"""
        
        # Get entity name
        entity_name = self.entity_name_entry.get().strip().upper()
        
        # Validate
        is_valid, error_msg = self.validate_entity_name(entity_name)
        if not is_valid:
            self.status_label.configure(text=f"❌ {error_msg}", text_color="#e74c3c")
            messagebox.showerror("Invalid Entity Name", error_msg)
            return
        
        # Check if copying from existing entity
        copy_from = self.copy_from_combo.get()
        
        try:
            # Add entity to WF_Matrix
            success = self.add_entity_to_wf_matrix(entity_name, copy_from)
            
            if success:
                self.status_label.configure(
                    text=f"✓ Entity '{entity_name}' created successfully!",
                    text_color="#2ecc71"
                )
                
                # Clear input
                self.entity_name_entry.delete(0, "end")
                self.copy_from_combo.set("None")
                
                # Refresh list
                self.refresh_entity_list()
                
                messagebox.showinfo(
                    "Success",
                    f"Entity '{entity_name}' has been created!\n\n"
                    f"Variable name: {entity_name}_PA_SERVICES\n"
                    f"Location: Core/WF_Matrix.py"
                )
            else:
                self.status_label.configure(
                    text="❌ Failed to create entity",
                    text_color="#e74c3c"
                )
                
        except Exception as e:
            self.status_label.configure(
                text=f"❌ Error: {str(e)}",
                text_color="#e74c3c"
            )
            messagebox.showerror("Error", f"Failed to create entity:\n{str(e)}")
    
    def add_entity_to_wf_matrix(self, entity_name, copy_from=None):
        """
        Add new entity to WF_Matrix.py file
        
        Args:
            entity_name (str): Name of entity to create
            copy_from (str): Entity to copy services from (optional)
            
        Returns:
            bool: True if successful
        """
        wf_matrix_path = Path(__file__).parent.parent.parent / "Core" / "WF_Matrix.py"
        
        # Read current file
        with open(wf_matrix_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Prepare new entity list
        variable_name = f"{entity_name}_PA_SERVICES"
        
        if copy_from and copy_from != "None" and copy_from in WF_Matrix.PA_SERVICES:
            # Copy services from existing entity
            services = WF_Matrix.PA_SERVICES[copy_from].copy()
        else:
            # Create with just header
            services = [["Service Group 1", "Service Group 2", "Service", "Default UofM"]]
        
        # Format services as Python code
        new_entity_lines = [f"\n# List of {entity_name} PA Services\n"]
        new_entity_lines.append(f"{variable_name} = [\n")
        for service in services:
            new_entity_lines.append(f"    {service},\n")
        new_entity_lines.append("]\n")
        
        # Find the PA_SERVICES dictionary and insert new entity
        pa_services_dict_line = -1
        pa_services_closing_line = -1
        last_dict_entry_line = -1
        
        for i, line in enumerate(lines):
            if "PA_SERVICES = {" in line:
                pa_services_dict_line = i
            if pa_services_dict_line != -1:
                # Look for dictionary entries
                if '": ' in line and '_PA_SERVICES' in line:
                    last_dict_entry_line = i
                if line.strip() == "}":
                    pa_services_closing_line = i
                    break
        
        if pa_services_dict_line == -1:
            raise Exception("Could not find PA_SERVICES dictionary in WF_Matrix.py")
        
        # Insert new entity definition before PA_SERVICES dictionary
        lines = lines[:pa_services_dict_line] + new_entity_lines + ["\n"] + lines[pa_services_dict_line:]
        
        # Update line numbers after insertion
        pa_services_closing_line += len(new_entity_lines) + 1
        last_dict_entry_line += len(new_entity_lines) + 1
        
        # Ensure the last entry has a comma
        if last_dict_entry_line != -1:
            line = lines[last_dict_entry_line]
            if not line.rstrip().endswith(','):
                lines[last_dict_entry_line] = line.rstrip() + ',\n'
        
        # Add new entry to PA_SERVICES dictionary (before closing brace)
        new_dict_entry = f'    "{entity_name}": {variable_name},\n'
        lines.insert(pa_services_closing_line, new_dict_entry)
        
        # Write back to file
        with open(wf_matrix_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        # Create initial service mappings for the new entity (if not TPUS)
        if entity_name != "TPUS":
            try:
                sys.path.insert(0, str(Path(__file__).parent.parent.parent / "Core"))
                from entity_service_mapper import EntityServiceMapper
                
                # Reload WF_Matrix to get the new entity
                import importlib
                importlib.reload(WF_Matrix)
                
                mapper = EntityServiceMapper()
                mapper.create_entity_mappings(entity_name, WF_Matrix.PA_SERVICES)
            except Exception as e:
                # Don't fail entity creation if mapping fails
                print(f"Warning: Could not create initial mappings: {e}")
        
        return True
    
    def run(self):
        """Run the GUI"""
        self.window.mainloop()


def open_entity_manager(parent=None):
    """
    Open the Entity Manager GUI
    
    Args:
        parent: Parent window (optional)
    """
    manager = EntityManagerGUI(parent)
    if not parent:
        manager.run()
    return manager


if __name__ == "__main__":
    # Standalone mode
    manager = EntityManagerGUI()
    manager.run()
