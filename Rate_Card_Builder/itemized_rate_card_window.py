"""
Itemized Rate Card Window
Main editing window for creating itemized rate cards.
"""

import customtkinter as ctk
from tkinter import messagebox, scrolledtext
import tkinter.ttk as ttk
import json
import re
from pathlib import Path
from language_loader import get_language_manager


class ItemizedRateCardWindow:
    """Window for creating and editing itemized rate cards."""
    
    # Default services
    DEFAULT_SERVICES = [
        "Translation",
        "TM - Fuzzy Match Low",
        "TM - Fuzzy Match Medium",
        "TM - Fuzzy Match High",
        "TM - Exact Match"
    ]
    
    def __init__(self, parent):
        """Initialize the itemized rate card window."""
        self.parent = parent
        self.language_manager = get_language_manager()
        self.languages_data = {}  # {language_name: {iso_code, rates_dict}}
        self.missing_languages = []  # Languages not found in ISO database
        
        # Create window
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Itemized Rate Card Editor")
        self.window.state('zoomed')  # Fullscreen
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface."""
        # Main container
        main_container = ctk.CTkFrame(self.window, corner_radius=0)
        main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Header section
        header_frame = ctk.CTkFrame(main_container, corner_radius=0, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="Itemized Rate Card Editor",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(anchor="w")
        
        # Main content with two sections
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left panel: Inputs
        left_panel = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_panel.pack(side="left", fill="both", padx=(0, 10))
        
        # Rate Card Name
        name_label = ctk.CTkLabel(
            left_panel,
            text="Rate Card Name:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        name_label.pack(anchor="w", pady=(0, 5))
        
        self.name_entry = ctk.CTkEntry(left_panel, placeholder_text="Enter rate card name")
        self.name_entry.pack(anchor="w", fill="x", pady=(0, 10))
        
        # Sponsor
        sponsor_label = ctk.CTkLabel(
            left_panel,
            text="Sponsor:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        sponsor_label.pack(anchor="w", pady=(0, 5))
        
        self.sponsor_entry = ctk.CTkEntry(left_panel, placeholder_text="Enter sponsor name")
        self.sponsor_entry.pack(anchor="w", fill="x", pady=(0, 15))
        
        # Language input section
        lang_label = ctk.CTkLabel(
            left_panel,
            text="Paste the languages for your rate card:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        lang_label.pack(anchor="w", pady=(0, 5))
        
        lang_instructions = ctk.CTkLabel(
            left_panel,
            text="(Separated by ', ' or '; ')",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        lang_instructions.pack(anchor="w", pady=(0, 5))
        
        # Text area for language input
        self.language_text = scrolledtext.ScrolledText(
            left_panel,
            height=8,
            width=40,
            wrap="word",
            bg="#212121",
            fg="white",
            insertbackground="white"
        )
        self.language_text.pack(fill="both", expand=True, pady=(0, 10))
        
        # Import button
        import_button = ctk.CTkButton(
            left_panel,
            text="Import Languages",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.on_import_languages
        )
        import_button.pack(fill="x", pady=(0, 10))
        
        # Error message area
        self.error_label = ctk.CTkLabel(
            left_panel,
            text="",
            font=ctk.CTkFont(size=10),
            text_color="red",
            justify="left",
            wraplength=300
        )
        self.error_label.pack(anchor="w", pady=(0, 10))
        
        # Save button
        save_button = ctk.CTkButton(
            left_panel,
            text="Save Rate Card",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="green",
            hover_color="darkgreen",
            command=self.on_save
        )
        save_button.pack(fill="x", pady=(0, 10))
        
        # Close button
        close_button = ctk.CTkButton(
            left_panel,
            text="Close",
            font=ctk.CTkFont(size=12),
            fg_color="gray40",
            command=self.window.destroy
        )
        close_button.pack(fill="x")
        
        # Right panel: Viewing pane (table)
        right_panel = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_panel.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        table_label = ctk.CTkLabel(
            right_panel,
            text="Rate Card:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        table_label.pack(anchor="w", pady=(0, 10))
        
        # Create table frame
        table_frame = ctk.CTkFrame(right_panel, fg_color="gray20", corner_radius=5)
        table_frame.pack(fill="both", expand=True)
        
        # Create Treeview
        self.create_table(table_frame)
    
    def create_table(self, parent):
        """Create the rate card table."""
        # Build columns: Language, ISO Code, then services
        columns = ["Language", "ISO_CODE"] + self.DEFAULT_SERVICES
        
        # Create Treeview with scrollbars
        tree_frame = ctk.CTkFrame(parent, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side="right", fill="y")
        
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.pack(side="bottom", fill="x")
        
        # Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=15,
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        self.tree.pack(fill="both", expand=True)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Configure column headings and widths
        self.tree.heading("Language", text="Language Name")
        self.tree.column("Language", width=150, anchor="center")
        
        self.tree.heading("ISO_CODE", text="ISO CODE")
        self.tree.column("ISO_CODE", width=120, anchor="center")
        
        for service in self.DEFAULT_SERVICES:
            self.tree.heading(service, text=service)
            self.tree.column(service, width=120, anchor="center")
        
        # Bind double-click for editing
        self.tree.bind("<Double-1>", self.on_cell_click)
    
    def on_import_languages(self):
        """Import languages from text input."""
        text = self.language_text.get("1.0", "end-1c").strip()
        
        if not text:
            messagebox.showwarning("Empty Input", "Please paste languages first.")
            return
        
        # Parse languages (split by comma or semicolon)
        languages = re.split(r'[,;]', text)
        languages = [lang.strip() for lang in languages if lang.strip()]
        
        if not languages:
            messagebox.showwarning("No Languages", "No valid languages found.")
            return
        
        # Clear previous data
        self.languages_data = {}
        self.missing_languages = []
        self.error_label.configure(text="")
        
        # Process each language
        for lang in languages:
            iso_data = self.language_manager.get_by_code(lang)
            
            if not iso_data:
                # Try to find by language name
                variants = self.language_manager.get_by_language(lang)
                if variants:
                    iso_data = variants[0]  # Use first variant
            
            if iso_data:
                # Found in database
                self.languages_data[lang] = {
                    "iso_code": iso_data["code"],
                    "found": True,
                    "rates": {service: "" for service in self.DEFAULT_SERVICES}
                }
            else:
                # Not found - add as missing
                self.languages_data[lang] = {
                    "iso_code": "",
                    "found": False,
                    "rates": {service: "" for service in self.DEFAULT_SERVICES}
                }
                self.missing_languages.append(lang)
        
        # Update table
        self.update_table()
        
        # Show error if any languages are missing
        if self.missing_languages:
            error_msg = f"⚠ Missing Languages:\n{', '.join(self.missing_languages)}\n\nPlease update the language names or ISO codes."
            self.error_label.configure(text=error_msg)
            messagebox.showwarning(
                "Missing ISO Codes",
                f"The following languages were not found:\n{', '.join(self.missing_languages)}\n\nYou can edit them in the table."
            )
        else:
            messagebox.showinfo("Success", "All languages imported successfully!")
    
    def update_table(self):
        """Update the table with current languages data."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add data rows
        for idx, (lang_name, lang_info) in enumerate(self.languages_data.items()):
            iso_code = lang_info["iso_code"]
            rates = lang_info["rates"]
            
            # Create values list
            values = [lang_name, iso_code] + [rates.get(service, "") for service in self.DEFAULT_SERVICES]
            
            # Add row with tag if missing
            tag = "missing" if not lang_info["found"] else ""
            iid = self.tree.insert("", "end", values=values, tags=(tag,))
            
            # Configure tag colors
            if tag:
                self.tree.tag_configure("missing", background="#4d3333", foreground="#ff9999")
    
    def on_cell_click(self, event):
        """Handle cell double-click for editing."""
        item = self.tree.selection()[0]
        col = self.tree.identify_column(event.x)
        col_index = int(col.lstrip('#')) - 1
        
        # Get column name
        if col_index < len(self.tree['columns']):
            col_name = self.tree['columns'][col_index]
            
            # Get current value
            values = self.tree.item(item)['values']
            current_value = values[col_index] if col_index < len(values) else ""
            
            # Only allow editing if not Language Name (col 0)
            if col_index == 0:
                messagebox.showinfo("Cannot Edit", "Language name is locked. Double-click ISO CODE to edit.")
                return
            
            # Create edit window
            self.create_edit_window(item, col_index, col_name, current_value)
    
    def create_edit_window(self, item, col_index, col_name, current_value):
        """Create a window for editing a cell."""
        edit_window = ctk.CTkToplevel(self.window)
        edit_window.title(f"Edit {col_name}")
        edit_window.geometry("400x150")
        
        # Label
        label = ctk.CTkLabel(
            edit_window,
            text=f"Edit {col_name}:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        label.pack(padx=10, pady=(10, 5))
        
        # Text entry
        entry = ctk.CTkEntry(
            edit_window,
            placeholder_text="Enter value"
        )
        entry.pack(padx=10, pady=5, fill="x")
        entry.insert(0, str(current_value))
        
        def save_edit():
            new_value = entry.get()
            
            # Get all values
            values = list(self.tree.item(item)['values'])
            
            # Validate if it's a rate column (numeric)
            col_name_check = self.tree['columns'][col_index] if col_index < len(self.tree['columns']) else ""
            if col_name_check in self.DEFAULT_SERVICES:
                # This is a rate column - validate float
                if new_value and new_value.strip():
                    try:
                        float_val = float(new_value)
                        new_value = str(float_val)
                    except ValueError:
                        messagebox.showerror("Invalid Value", f"'{new_value}' is not a valid number. Please enter a numeric value.")
                        return
            
            values[col_index] = new_value
            
            # Update tree
            self.tree.item(item, values=values)
            
            # Update internal data
            lang_name = values[0]
            if col_index == 1:  # ISO CODE column
                self.languages_data[lang_name]["iso_code"] = new_value
                # Check if now found
                if new_value:
                    self.languages_data[lang_name]["found"] = True
                    if lang_name in self.missing_languages:
                        self.missing_languages.remove(lang_name)
                    self.tree.item(item, tags=())
                    self.error_label.configure(text="")
            else:  # Rate column
                service_name = self.DEFAULT_SERVICES[col_index - 2]
                self.languages_data[lang_name]["rates"][service_name] = new_value
            
            edit_window.destroy()
        
        # Save button
        save_button = ctk.CTkButton(
            edit_window,
            text="Save",
            command=save_edit
        )
        save_button.pack(padx=10, pady=5, fill="x")
    
    def on_save(self):
        """Save the rate card to JSON."""
        if not self.name_entry.get():
            messagebox.showwarning("Missing Name", "Please enter a rate card name.")
            return
        
        if not self.languages_data:
            messagebox.showwarning("No Data", "Please import languages first.")
            return
        
        # Build save data
        rate_card = {
            "name": self.name_entry.get(),
            "sponsor": self.sponsor_entry.get(),
            "services": self.DEFAULT_SERVICES,
            "languages": {}
        }
        
        for lang_name, lang_info in self.languages_data.items():
            rate_card["languages"][lang_name] = {
                "iso_code": lang_info["iso_code"],
                "rates": lang_info["rates"]
            }
        
        # Save to JSON
        file_path = Path(__file__).parent / f"rate_cards_{self.name_entry.get().replace(' ', '_')}.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(rate_card, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Success", f"Rate card saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save rate card:\n{str(e)}")
