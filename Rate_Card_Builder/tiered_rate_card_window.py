"""
Tiered Rate Card Window
Main editing window for creating tiered rate cards.
"""

import customtkinter as ctk
from tkinter import messagebox, scrolledtext
import tkinter as tk
import tkinter.ttk as ttk
import json
import re
from pathlib import Path
from language_loader import get_language_manager


class TieredRateCardWindow:
    """Window for creating and editing tiered rate cards."""
    
    # Default services
    DEFAULT_SERVICES = [
        "Translation",
        "TM - Fuzzy Match Low",
        "TM - Fuzzy Match Medium",
        "TM - Fuzzy Match High",
        "TM - Exact Match"
    ]
    
    # Default tiers
    DEFAULT_TIERS = [
        "0-10k",
        "10k-50k",
        "50k-100k",
        "100k+"
    ]
    
    def __init__(self, parent):
        """Initialize the tiered rate card window."""
        self.parent = parent
        self.language_manager = get_language_manager()
        self.languages_data = {}  # {language_name: {iso_code, rates_dict}}
        self.missing_languages = []  # Languages not found in ISO database
        self.current_edit_entry = None  # Track active inline edit Entry
        self.current_edit_item = None  # Track active item being edited
        self.current_edit_col = None  # Track active column being edited
        
        # Create window
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Tiered Rate Card Editor")
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
            text="Tiered Rate Card Editor",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(anchor="w")
        
        # Main content with two sections
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left panel: Inputs
        left_panel = ctk.CTkFrame(content_frame, fg_color="transparent")
        left_panel.pack(side="left", fill="both", padx=(0, 10))
        
        # Load/Create buttons at top
        button_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 15))
        
        load_button = ctk.CTkButton(
            button_frame,
            text="Load Rate Card",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="blue",
            hover_color="darkblue",
            height=35,
            command=self.on_load_rate_card
        )
        load_button.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        create_button = ctk.CTkButton(
            button_frame,
            text="Create New",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="gray60",
            hover_color="gray70",
            height=35,
            command=self.on_create_new
        )
        create_button.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
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
            text="Rate Card (by Tier):",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        table_label.pack(anchor="w", pady=(0, 10))
        
        # Create table frame
        table_frame = ctk.CTkFrame(right_panel, fg_color="gray20", corner_radius=5)
        table_frame.pack(fill="both", expand=True)
        
        # Create Treeview
        self.create_table(table_frame)
    
    def create_table(self, parent):
        """Create the tiered rate card table."""
        # Build columns: Language, ISO Code, then tiers with services
        columns = ["Language", "ISO_CODE"]
        for tier in self.DEFAULT_TIERS:
            for service in self.DEFAULT_SERVICES:
                columns.append(f"{tier}_{service}")
        
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
        
        for col in columns[2:]:
            self.tree.heading(col, text=col.replace("_", "\n"))
            self.tree.column(col, width=80, anchor="center")
        
        # Bind double-click for editing
        self.tree.bind("<Double-1>", self.on_cell_click)
        
        # Add control buttons area below tree
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # Status label
        self.edit_status_label = ctk.CTkLabel(
            button_frame,
            text="Click a cell and start typing. Press Enter to save, Escape to cancel.",
            font=ctk.CTkFont(size=10),
            text_color="gray80"
        )
        self.edit_status_label.pack(anchor="w", pady=(0, 10))
        
        # Bulk fill button
        bulk_fill_button = ctk.CTkButton(
            button_frame,
            text="Fill Column with Selected Value",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2d5016",
            hover_color="#3d7020",
            command=self.on_bulk_fill
        )
        bulk_fill_button.pack(side="left", padx=(0, 10))
        
        # Info label for bulk fill
        self.bulk_fill_info = ctk.CTkLabel(
            button_frame,
            text="(Edit a cell, then click to fill all empty cells in that column)",
            font=ctk.CTkFont(size=10),
            text_color="gray70"
        )
        self.bulk_fill_info.pack(side="left")
    
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
                rates = {}
                for tier in self.DEFAULT_TIERS:
                    for service in self.DEFAULT_SERVICES:
                        rates[f"{tier}_{service}"] = ""
                
                self.languages_data[lang] = {
                    "iso_code": iso_data["code"],
                    "found": True,
                    "rates": rates
                }
            else:
                # Not found - add as missing
                rates = {}
                for tier in self.DEFAULT_TIERS:
                    for service in self.DEFAULT_SERVICES:
                        rates[f"{tier}_{service}"] = ""
                
                self.languages_data[lang] = {
                    "iso_code": "",
                    "found": False,
                    "rates": rates
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
            columns = ["Language", "ISO_CODE"]
            for tier in self.DEFAULT_TIERS:
                for service in self.DEFAULT_SERVICES:
                    columns.append(f"{tier}_{service}")
            
            values = [lang_name, iso_code] + [rates.get(col, "") for col in columns[2:]]
            
            # Add row with tag if missing
            tag = "missing" if not lang_info["found"] else ""
            iid = self.tree.insert("", "end", values=values, tags=(tag,))
            
            # Configure tag colors
            if tag:
                self.tree.tag_configure("missing", background="#4d3333", foreground="#ff9999")
    
    def on_cell_click(self, event):
        """Handle cell double-click to enable inline editing."""
        # Close any existing edit entry
        if self.current_edit_entry:
            self.current_edit_entry.destroy()
            self.current_edit_entry = None
        
        try:
            item = self.tree.selection()[0]
        except IndexError:
            return
        
        col = self.tree.identify_column(event.x)
        col_index = int(col.lstrip('#')) - 1
        
        # Get current values
        values = self.tree.item(item)['values']
        lang_name = values[0] if values else ""
        col_name = self.tree['columns'][col_index] if col_index < len(self.tree['columns']) else ""
        current_value = values[col_index] if col_index < len(values) else ""
        
        # Check if this is a missing language row
        item_tags = self.tree.item(item, 'tags')
        is_missing = 'missing' in item_tags if item_tags else False
        
        # Language name column (col 0) - only editable for missing languages
        if col_index == 0 and not is_missing:
            messagebox.showinfo("Cannot Edit", "Language name is locked for mapped languages.\n\nYou can only edit the language name if it's missing from the ISO code database.")
            return
        
        # Get cell bbox for positioning the entry widget
        bbox = self.tree.bbox(item, col)
        if not bbox:
            return
        
        # Create inline entry widget
        self.current_edit_entry = tk.Entry(self.tree, font=("Arial", 10), width=20)
        self.current_edit_entry.insert(0, str(current_value))
        self.current_edit_entry.select_range(0, len(self.current_edit_entry.get()))
        
        # Position entry over cell
        self.tree.window_create(item, window=self.current_edit_entry, column=col_index)
        self.current_edit_entry.focus()
        
        # Store edit context
        self.current_edit_item = item
        self.current_edit_col = col_index
        
        # Bind keys for save/cancel
        def on_return(e):
            self.save_inline_edit(item, col_index, col_name, lang_name, is_missing)
        
        def on_escape(e):
            self.cancel_inline_edit()
        
        def on_focus_out(e):
            # Save on focus out
            self.save_inline_edit(item, col_index, col_name, lang_name, is_missing)
        
        self.current_edit_entry.bind("<Return>", on_return)
        self.current_edit_entry.bind("<Escape>", on_escape)
        self.current_edit_entry.bind("<FocusOut>", on_focus_out)
    
    def save_inline_edit(self, item, col_index, col_name, lang_name, is_missing):
        """Save inline edit and update data."""
        if not self.current_edit_entry:
            return
        
        new_value = self.current_edit_entry.get()
        
        # Validate if it's a rate column (numeric)
        if col_index > 1:  # All rate columns are numeric
            if new_value and new_value.strip():
                try:
                    float_val = float(new_value)
                    new_value = str(float_val)
                except ValueError:
                    messagebox.showerror("Invalid Value", f"'{new_value}' is not a valid number. Please enter a numeric value.")
                    self.cancel_inline_edit()
                    return
        
        # Get all values
        values = list(self.tree.item(item)['values'])
        old_lang_name = values[0]
        old_iso_code = values[1] if len(values) > 1 else ""
        
        # Handle language name change (col 0)
        if col_index == 0 and new_value:
            # Check if new language name already exists
            if new_value != old_lang_name and new_value in self.languages_data:
                messagebox.showerror("Duplicate", f"Language '{new_value}' already exists in the rate card.")
                self.cancel_inline_edit()
                return
            
            # Update the languages_data dictionary with new key
            self.languages_data[new_value] = self.languages_data.pop(old_lang_name)
            values[0] = new_value
            lang_name = new_value
            
            # Persist to ISO codes database if it has an ISO code
            if old_iso_code:
                self.language_manager.update_language_name(old_iso_code, new_value)
        else:
            values[col_index] = new_value
        
        # Update tree display
        self.tree.item(item, values=values)
        
        # Update internal data
        if col_index == 1:  # ISO CODE column
            self.languages_data[lang_name]["iso_code"] = new_value
            # Persist ISO code change to database
            if old_iso_code and new_value:
                self.language_manager.update_language_code(old_iso_code, new_value)
            
            # Check if now found
            if new_value:
                self.languages_data[lang_name]["found"] = True
                if lang_name in self.missing_languages:
                    self.missing_languages.remove(lang_name)
                self.tree.item(item, tags=())
                self.error_label.configure(text="")
        elif col_index > 1:  # Rate column
            self.languages_data[lang_name]["rates"][col_name] = new_value
        
        # Update status
        self.edit_status_label.configure(text=f"✓ Saved: {col_name} = {new_value}")
        
        # Track this for bulk fill
        self.current_edit_col = col_index
        
        self.cancel_inline_edit()
    
    def cancel_inline_edit(self):
        """Cancel inline editing and cleanup."""
        if self.current_edit_entry:
            try:
                self.current_edit_entry.destroy()
            except:
                pass
            self.current_edit_entry = None
        self.current_edit_item = None
    
    def on_bulk_fill(self):
        """Fill all empty cells in the last edited column with the selected value."""
        if self.current_edit_col is None:
            messagebox.showwarning("No Selection", "Please edit a cell first to select which column to fill.")
            return
        
        # Get column name and the value to fill from first language
        col_name = self.tree['columns'][self.current_edit_col] if self.current_edit_col < len(self.tree['columns']) else None
        if not col_name:
            messagebox.showwarning("Invalid Column", "Could not identify the column to fill.")
            return
        
        # Find the value to fill (from first edited item or current selection)
        try:
            selected_item = self.tree.selection()[0]
            values = self.tree.item(selected_item)['values']
            fill_value = values[self.current_edit_col] if self.current_edit_col < len(values) else ""
        except (IndexError, KeyError):
            messagebox.showwarning("No Selection", "Please select a cell with a value to fill from.")
            return
        
        if not fill_value or not fill_value.strip():
            messagebox.showwarning("Empty Value", "The selected cell is empty. Please enter a value first.")
            return
        
        # Confirm bulk fill
        result = messagebox.askyesno(
            "Bulk Fill",
            f"Fill all empty cells in column '{col_name}' with value '{fill_value}'?"
        )
        
        if not result:
            return
        
        # Fill all empty cells in this column
        filled_count = 0
        for item in self.tree.get_children():
            values = list(self.tree.item(item)['values'])
            lang_name = values[0]
            
            # Only fill if empty
            if not values[self.current_edit_col] or not str(values[self.current_edit_col]).strip():
                values[self.current_edit_col] = fill_value
                self.tree.item(item, values=values)
                
                # Update internal data
                self.languages_data[lang_name]["rates"][col_name] = fill_value
                
                filled_count += 1
        
        messagebox.showinfo("Bulk Fill Complete", f"Filled {filled_count} cells in column '{col_name}'.")
    
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
            "type": "tiered",
            "tiers": self.DEFAULT_TIERS,
            "services": self.DEFAULT_SERVICES,
            "languages": {}
        }
        
        for lang_name, lang_info in self.languages_data.items():
            rate_card["languages"][lang_name] = {
                "iso_code": lang_info["iso_code"],
                "rates": lang_info["rates"]
            }
        
        # Save to JSON
        file_path = Path(__file__).parent / f"rate_cards_{self.name_entry.get().replace(' ', '_')}_tiered.json"
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(rate_card, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Success", f"Tiered rate card saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save rate card:\n{str(e)}")
    
    def on_load_rate_card(self):
        """Open dialog to load an existing rate card."""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="Select Rate Card",
            initialdir=str(Path(__file__).parent),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Check if current data modified and prompt save
        if self.languages_data:
            result = messagebox.askyesnocancel(
                "Save Current Rate Card?",
                "You have unsaved changes. Save before loading?"
            )
            if result is True:  # Yes
                self.on_save()
            elif result is None:  # Cancel
                return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load data into editor
            self.name_entry.delete(0, "end")
            self.name_entry.insert(0, data.get("name", ""))
            
            self.sponsor_entry.delete(0, "end")
            self.sponsor_entry.insert(0, data.get("sponsor", ""))
            
            # Clear and reload languages data
            self.languages_data = {}
            self.missing_languages = []
            self.error_label.configure(text="")
            
            # Populate languages_data from loaded file
            for lang_name, lang_info in data.get("languages", {}).items():
                iso_code = lang_info.get("iso_code", "")
                
                # Try to verify ISO code
                iso_data = self.language_manager.get_by_code(iso_code) if iso_code else None
                is_found = iso_data is not None if iso_code else False
                
                # Initialize rates with all tier/service combinations
                rates = {}
                for tier in self.DEFAULT_TIERS:
                    for service in self.DEFAULT_SERVICES:
                        col_name = f"{tier}_{service}"
                        rates[col_name] = lang_info.get("rates", {}).get(col_name, "")
                
                self.languages_data[lang_name] = {
                    "iso_code": iso_code,
                    "found": is_found,
                    "rates": rates
                }
                
                if not is_found and iso_code:
                    self.missing_languages.append(lang_name)
            
            # Update table
            self.update_table()
            
            # Clear language text area
            self.language_text.delete("1.0", "end")
            
            # Show success message
            messagebox.showinfo("Loaded", f"Loaded: {Path(file_path).name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load rate card:\n{str(e)}")
    
    def on_create_new(self):
        """Create a new rate card with prompt to save current one."""
        if self.languages_data:
            result = messagebox.askyesnocancel(
                "Save Current Rate Card?",
                "You have unsaved changes. Save before creating new?"
            )
            if result is True:  # Yes
                self.on_save()
            elif result is None:  # Cancel
                return
        
        # Clear all fields
        self.name_entry.delete(0, "end")
        self.sponsor_entry.delete(0, "end")
        self.language_text.delete("1.0", "end")
        
        # Clear data
        self.languages_data = {}
        self.missing_languages = []
        self.error_label.configure(text="")
        
        # Clear table
        self.update_table()
        
        messagebox.showinfo("New Rate Card", "Ready to create a new tiered rate card!")
