"""
Rate Card Builder - Main GUI Application
Standalone module for creating and managing rate cards with a modern UI using customtkinter.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import tkinter as tk
import tkinter.ttk as ttk
import csv
import json
from pathlib import Path
import sys
import os
from tiered_rate_card_window import TieredRateCardWindow


class RateCardBuilderGUI:
    """Main GUI class for Rate Card Builder application."""
    
    def __init__(self, root):
        """
        Initialize the Rate Card Builder GUI.
        
        Args:
            root: The root CTk window
        """
        self.root = root
        self.root.title("Rate Card Builder")
        self.root.state('zoomed')  # Fullscreen
        
        # Set color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.itemized_editor = None
        self.global_services_listbox = None
        self.global_service_entry = None
        self.global_service_status_label = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface with main components."""
        # Main container
        main_container = ctk.CTkFrame(self.root, corner_radius=0)
        main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Header section
        header_frame = ctk.CTkFrame(main_container, corner_radius=0, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="Rate Card Builder",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(anchor="w")
        
        # Tabbed interface
        self.tabview = ctk.CTkTabview(main_container, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Add tabs
        self.tab_itemized = self.tabview.add("Itemized Rate Card")
        self.tab_tiered = self.tabview.add("Tiered Rate Card")
        self.tab_load = self.tabview.add("Load Rate Card")
        self.tab_settings = self.tabview.add("Settings")
        
        # Setup tab content
        self.setup_itemized_tab()
        self.setup_tiered_tab()
        self.setup_load_tab()
        self.setup_settings_tab()
        
        # Status bar
        status_frame = ctk.CTkFrame(main_container, corner_radius=10, fg_color="gray20")
        status_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.status_label.pack(anchor="w", padx=10, pady=8)
    
    def setup_itemized_tab(self):
        """Setup the Itemized Rate Card tab with embedded editor."""
        # Import the ItemizedRateCardWindow class components
        from itemized_rate_card_editor import setup_itemized_editor
        
        # Setup the editor directly in this tab
        self.itemized_editor = setup_itemized_editor(self.tab_itemized, self.root)
    
    def setup_tiered_tab(self):
        """Setup the Tiered Rate Card tab."""
        content_frame = ctk.CTkFrame(self.tab_tiered, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Welcome message
        welcome_label = ctk.CTkLabel(
            content_frame,
            text="Create Tiered Rate Card",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        welcome_label.pack(pady=(0, 10))
        
        description_label = ctk.CTkLabel(
            content_frame,
            text="Create a new tiered rate card with volume/tier-based pricing",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        description_label.pack(pady=(0, 30))
        
        # Button
        create_button = ctk.CTkButton(
            content_frame,
            text="Create Tiered Rate Card",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=50,
            corner_radius=10,
            command=self.on_create_tiered
        )
        create_button.pack(padx=40, pady=20)
    
    def setup_load_tab(self):
        """Setup the Load Rate Card tab with embedded file list."""
        content_frame = ctk.CTkFrame(self.tab_load, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            content_frame,
            text="Load Existing Rate Card",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(anchor="w", pady=(0, 10))
        
        # List section
        list_label = ctk.CTkLabel(
            content_frame,
            text="Saved Rate Cards:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        list_label.pack(anchor="w", pady=(10, 5))
        
        # Create frame for listbox with scrollbar
        list_frame = ctk.CTkFrame(content_frame, fg_color="gray20", corner_radius=5)
        list_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        # Listbox
        self.load_file_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            height=15
        )
        self.load_file_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        scrollbar.config(command=self.load_file_listbox.yview)
        
        # Bind selection
        self.load_file_listbox.bind("<<ListboxSelect>>", self.on_load_file_selected)
        self.load_file_listbox.bind("<Double-Button-1>", self.on_load_file_double_click)
        
        # Info section
        info_label = ctk.CTkLabel(
            content_frame,
            text="Rate Card Details:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        info_label.pack(anchor="w", pady=(10, 5))
        
        # Info frame
        self.load_info_frame = ctk.CTkFrame(content_frame, fg_color="gray20", corner_radius=5, height=100)
        self.load_info_frame.pack(fill="x", pady=(0, 20))
        self.load_info_frame.pack_propagate(False)
        
        self.load_info_text = ctk.CTkLabel(
            self.load_info_frame,
            text="Select a rate card to view details",
            font=ctk.CTkFont(size=11),
            justify="left",
            wraplength=600
        )
        self.load_info_text.pack(anchor="nw", padx=10, pady=10)
        
        # Buttons frame
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        # Open button
        open_button = ctk.CTkButton(
            button_frame,
            text="Open Selected",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="green",
            hover_color="darkgreen",
            command=self.on_load_open
        )
        open_button.pack(side="left", padx=5)
        
        # Delete button
        delete_button = ctk.CTkButton(
            button_frame,
            text="Delete",
            font=ctk.CTkFont(size=12),
            fg_color="red",
            hover_color="darkred",
            command=self.on_load_delete
        )
        delete_button.pack(side="left", padx=5)

        export_button = ctk.CTkButton(
            button_frame,
            text="Export CSV",
            font=ctk.CTkFont(size=12),
            fg_color="#5a4d9a",
            hover_color="#6d5bb8",
            command=self.on_load_export_csv
        )
        export_button.pack(side="left", padx=5)
        
        # Browse button
        browse_button = ctk.CTkButton(
            button_frame,
            text="Browse...",
            font=ctk.CTkFont(size=12),
            fg_color="gray60",
            hover_color="gray70",
            command=self.on_load_browse
        )
        browse_button.pack(side="left", padx=5)
        
        # Store current selection
        self.load_current_file = None
        self.load_current_data = None
        
        # Populate list on tab setup
        self.populate_load_file_list()
    
    def setup_settings_tab(self):
        """Setup the Settings tab."""
        content_frame = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Welcome message
        welcome_label = ctk.CTkLabel(
            content_frame,
            text="Settings",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        welcome_label.pack(pady=(0, 10))
        
        description_label = ctk.CTkLabel(
            content_frame,
            text="Configure application settings",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        description_label.pack(pady=(0, 30))
        
        service_card = ctk.CTkFrame(content_frame, fg_color="gray20", corner_radius=10)
        service_card.pack(fill="both", expand=True)

        service_title = ctk.CTkLabel(
            service_card,
            text="Global Service List",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        service_title.pack(anchor="w", padx=15, pady=(15, 4))

        service_description = ctk.CTkLabel(
            service_card,
            text="Services here are shared by future rate cards and can be added or removed globally.",
            font=ctk.CTkFont(size=11),
            text_color="gray70"
        )
        service_description.pack(anchor="w", padx=15, pady=(0, 12))

        editor_frame = ctk.CTkFrame(service_card, fg_color="transparent")
        editor_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        list_frame = ctk.CTkFrame(editor_frame, fg_color="gray15", corner_radius=8)
        list_frame.pack(side="left", fill="both", expand=True, padx=(0, 12))

        list_scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        list_scrollbar.pack(side="right", fill="y")

        self.global_services_listbox = tk.Listbox(
            list_frame,
            height=14,
            activestyle="dotbox",
            yscrollcommand=list_scrollbar.set,
            selectmode="browse"
        )
        self.global_services_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        list_scrollbar.config(command=self.global_services_listbox.yview)

        control_frame = ctk.CTkFrame(editor_frame, fg_color="transparent")
        control_frame.pack(side="right", fill="y")

        entry_label = ctk.CTkLabel(
            control_frame,
            text="Service name",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        entry_label.pack(anchor="w", pady=(0, 5))

        self.global_service_entry = ctk.CTkEntry(control_frame, width=240, placeholder_text="Enter a new service")
        self.global_service_entry.pack(fill="x", pady=(0, 10))

        add_button = ctk.CTkButton(
            control_frame,
            text="Add Service",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.on_global_service_add
        )
        add_button.pack(fill="x", pady=(0, 8))

        delete_button = ctk.CTkButton(
            control_frame,
            text="Delete Selected",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#7a1f1f",
            hover_color="#9a2a2a",
            command=self.on_global_service_delete
        )
        delete_button.pack(fill="x", pady=(0, 8))

        reload_button = ctk.CTkButton(
            control_frame,
            text="Reload From File",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="gray60",
            hover_color="gray70",
            command=self.refresh_global_service_list
        )
        reload_button.pack(fill="x", pady=(0, 8))

        self.global_service_status_label = ctk.CTkLabel(
            control_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="gray70",
            justify="left",
            wraplength=240
        )
        self.global_service_status_label.pack(anchor="w", pady=(10, 0))

        self.refresh_global_service_list()

    def _service_columns_config_path(self):
        """Return the shared service column file path."""
        return Path(__file__).parent / "service_columns.json"

    def _load_global_service_list(self):
        """Load and sanitize the global service list."""
        config_path = self._service_columns_config_path()
        default_services = [
            "Translation",
            "MTPE",
            "TM - Fuzzy Match Low",
            "TM - Fuzzy Match Medium",
            "TM - Fuzzy Match High",
            "TM - Exact Match"
        ]

        if not config_path.exists():
            return default_services

        try:
            with open(config_path, 'r', encoding='utf-8') as file_handle:
                data = json.load(file_handle)
        except Exception:
            return default_services

        services = data.get("services", [])
        cleaned_services = []
        for service in services:
            service_name = str(service).strip()
            if service_name and service_name not in cleaned_services:
                cleaned_services.append(service_name)

        return cleaned_services if cleaned_services else default_services

    def _save_global_service_list(self, services):
        """Persist the shared service list to disk."""
        cleaned_services = []
        for service in services:
            service_name = str(service).strip()
            if service_name and service_name not in cleaned_services:
                cleaned_services.append(service_name)

        if not cleaned_services:
            return False

        with open(self._service_columns_config_path(), 'w', encoding='utf-8') as file_handle:
            json.dump({"services": cleaned_services}, file_handle, indent=2, ensure_ascii=False)

        return True

    def refresh_global_service_list(self):
        """Refresh the Settings tab service list from the shared file."""
        if not self.global_services_listbox:
            return

        self.global_services_listbox.delete(0, "end")
        for service_name in self._load_global_service_list():
            self.global_services_listbox.insert("end", service_name)

    def _notify_itemized_service_change(self):
        """Refresh the embedded itemized editor after global service changes."""
        if self.itemized_editor and hasattr(self.itemized_editor, "reload_global_services_from_file"):
            self.itemized_editor.reload_global_services_from_file()

    def on_global_service_add(self):
        """Add a service to the global list from the Settings tab."""
        if not self.global_service_entry:
            return

        service_name = self.global_service_entry.get().strip()
        if not service_name:
            messagebox.showwarning("Missing Service", "Please enter a service name.")
            return

        services = self._load_global_service_list()
        if service_name in services:
            messagebox.showwarning("Duplicate", f"Service '{service_name}' already exists in the global list.")
            return

        services.append(service_name)
        self._save_global_service_list(services)
        self.global_service_entry.delete(0, "end")
        self.refresh_global_service_list()
        self._notify_itemized_service_change()
        if self.global_service_status_label:
            self.global_service_status_label.configure(text=f"Added: {service_name}")

    def on_global_service_delete(self):
        """Delete the selected service from the global list."""
        if not self.global_services_listbox:
            return

        selection = self.global_services_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a service to delete.")
            return

        index = selection[0]
        service_name = self.global_services_listbox.get(index)
        services = self._load_global_service_list()

        if len(services) <= 1:
            messagebox.showwarning("Cannot Delete", "At least one service must remain in the global list.")
            return

        confirm = messagebox.askyesno(
            "Delete Service",
            f"Delete '{service_name}' from the global service list?"
        )
        if not confirm:
            return

        services = [service for service in services if service != service_name]
        self._save_global_service_list(services)
        self.refresh_global_service_list()
        self._notify_itemized_service_change()
        if self.global_service_status_label:
            self.global_service_status_label.configure(text=f"Deleted: {service_name}")
    
    def on_create_tiered(self):
        """Handle create tiered rate card button click."""
        self.update_status("Opening Tiered Rate Card Editor...")
        tiered_window = TieredRateCardWindow(self.root)
        self.update_status("Ready")
    
    def populate_load_file_list(self):
        """Populate the list of saved rate cards."""
        self.load_file_listbox.delete(0, "end")
        
        module_dir = Path(__file__).parent
        rate_card_files = list(module_dir.glob("rate_cards_*.json"))
        
        for file_path in sorted(rate_card_files, key=lambda x: x.stat().st_mtime, reverse=True):
            self.load_file_listbox.insert("end", file_path.name)
    
    def on_load_file_selected(self, event):
        """Handle file selection in load tab."""
        selection = self.load_file_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        filename = self.load_file_listbox.get(index)
        file_path = Path(__file__).parent / filename
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.load_current_data = json.load(f)
                    self.load_current_file = file_path
                
                # Display info
                info = f"""
Name: {self.load_current_data.get('name', 'N/A')}
Sponsor: {self.load_current_data.get('sponsor', 'N/A')}
Type: {self.load_current_data.get('type', 'itemized')}
Languages: {len(self.load_current_data.get('languages', {}))}
Services: {len(self.load_current_data.get('services', []))}
                """.strip()
                
                self.load_info_text.configure(text=info)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to read file:\n{str(e)}")
    
    def on_load_file_double_click(self, event):
        """Handle double-click to open file."""
        self.on_load_open()
    
    def on_load_open(self):
        """Open selected rate card for viewing/editing."""
        if not self.load_current_file or not self.load_current_data:
            messagebox.showwarning("No Selection", "Please select a rate card to open.")
            return
        
        # For now, show a message
        messagebox.showinfo(
            "Rate Card",
            f"""Opened: {self.load_current_file.name}
            
Name: {self.load_current_data.get('name', 'N/A')}
Type: {self.load_current_data.get('type', 'itemized')}
Languages: {len(self.load_current_data.get('languages', {}))}

(Edit functionality coming soon)"""
        )
        # TODO: Implement editor for loaded rate card
    
    def on_load_delete(self):
        """Delete selected rate card."""
        if not self.load_current_file:
            messagebox.showwarning("No Selection", "Please select a rate card to delete.")
            return
        
        confirm = messagebox.askyesno(
            "Delete Rate Card",
            f"Delete '{self.load_current_file.name}'?\n\nThis cannot be undone."
        )
        
        if confirm:
            try:
                self.load_current_file.unlink()
                self.load_current_file = None
                self.load_current_data = None
                self.load_info_text.configure(text="Select a rate card to view details")
                self.populate_load_file_list()
                messagebox.showinfo("Success", "Rate card deleted.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete file:\n{str(e)}")

    def _build_csv_from_rate_card(self, rate_card_data):
        """Build CSV headers and rows from a saved rate card."""
        services = rate_card_data.get("services", [])
        if not isinstance(services, list):
            services = []

        headers = ["Language Name", "ISO CODE"] + [str(service).strip() for service in services if str(service).strip()]
        rows = []

        for lang_name, lang_info in rate_card_data.get("languages", {}).items():
            if not isinstance(lang_info, dict):
                continue

            rates = lang_info.get("rates", {}) if isinstance(lang_info.get("rates", {}), dict) else {}
            row = [lang_name, lang_info.get("iso_code", "")]

            for service_name in services:
                cleaned_service = str(service_name).strip()
                if not cleaned_service:
                    continue
                row.append(rates.get(cleaned_service, ""))

            rows.append(row)

        return headers, rows

    def on_load_export_csv(self):
        """Export the selected saved rate card to CSV using its visible service columns."""
        if not self.load_current_data or not self.load_current_file:
            messagebox.showwarning("No Selection", "Please select a rate card to export.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Export Rate Card as CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=str(Path(__file__).parent),
            initialfile=f"{self.load_current_file.stem}.csv"
        )

        if not file_path:
            return

        headers, rows = self._build_csv_from_rate_card(self.load_current_data)

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(headers)
                writer.writerows(rows)

            messagebox.showinfo("Export Complete", f"CSV exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV:\n{str(e)}")
    
    def on_load_browse(self):
        """Browse for a rate card file."""
        file_path = filedialog.askopenfilename(
            title="Select Rate Card",
            initialdir=str(Path(__file__).parent),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.load_current_data = json.load(f)
                    self.load_current_file = Path(file_path)
                
                # Display info
                info = f"""
Name: {self.load_current_data.get('name', 'N/A')}
Sponsor: {self.load_current_data.get('sponsor', 'N/A')}
Type: {self.load_current_data.get('type', 'itemized')}
Languages: {len(self.load_current_data.get('languages', {}))}
Services: {len(self.load_current_data.get('services', []))}
                """.strip()
                
                self.load_info_text.configure(text=info)
                self.update_status(f"Loaded: {Path(file_path).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
    
    def update_status(self, message):
        """Update status bar message."""
        self.status_label.configure(text=message)
        self.root.update_idletasks()


def main():
    """Main entry point for the application."""
    root = ctk.CTk()
    app = RateCardBuilderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
