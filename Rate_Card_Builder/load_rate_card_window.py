"""
Load Rate Card Window
Window for loading and editing existing rate cards.
Supports both JSON and Excel rate card formats.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import tkinter as tk
import tkinter.ttk as ttk
import json
from pathlib import Path
import sys

# Add parent directory to path for importing excel_rate_card_loader
sys.path.insert(0, str(Path(__file__).parent))

try:
    from excel_rate_card_loader import load_excel_rate_card, find_excel_rate_cards
except ImportError:
    load_excel_rate_card = None
    find_excel_rate_cards = None

try:
    from itemized_rate_card_editor import ItemizedRateCardEditor
except ImportError:
    ItemizedRateCardEditor = None

class LoadedRateCardEditor(ItemizedRateCardEditor):
    """Itemized editor variant that saves through LoadRateCardWindow callbacks."""

    def __init__(self, parent_frame, root, save_callback):
        self._save_callback = save_callback
        super().__init__(parent_frame, root)

    def _build_rate_card_payload(self):
        if not self.name_entry.get().strip():
            messagebox.showwarning("Missing Name", "Please enter a rate card name.")
            return None

        if not self.languages_data:
            messagebox.showwarning("No Data", "Please import languages first.")
            return None

        payload = {
            "name": self.name_entry.get().strip(),
            "sponsor": self.sponsor_entry.get().strip(),
            "services": list(self.DEFAULT_SERVICES),
            "iso_codes": self._build_local_iso_codes_snapshot(),
            "languages": {}
        }

        for lang_name, lang_info in self.languages_data.items():
            payload["languages"][lang_name] = {
                "iso_code": lang_info.get("iso_code", ""),
                "rates": dict(lang_info.get("rates", {}))
            }

        return payload

    def on_save(self):
        payload = self._build_rate_card_payload()
        if payload is None:
            return

        try:
            self._save_callback(payload)
            self._save_global_services()
            messagebox.showinfo("Success", "Rate card saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save rate card:\n{str(e)}")

class LoadRateCardWindow:
    """Window for loading and editing existing rate cards."""

    def get_master_rate_cards_path(self):
        """Return the shared master rate cards JSON file."""
        return Path(__file__).parent.parent / "Core" / "master_rate_cards.json"

    def load_master_rate_card_names(self):
        """Return the available master rate card names from the shared JSON."""
        master_path = self.get_master_rate_cards_path()
        if not master_path.exists():
            return []

        try:
            with open(master_path, "r", encoding="utf-8") as file_handle:
                data = json.load(file_handle)
            return sorted(list(data.get("rate_cards", {}).keys()))
        except Exception:
            return []

    def on_load_master_rate_card(self):
        """Open a picker for master rate cards and load the selected card."""
        master_names = self.load_master_rate_card_names()
        if not master_names:
            messagebox.showwarning("No Master Cards", "No master rate cards were found.")
            return

        picker = ctk.CTkToplevel(self.window)
        picker.title("Load Master Rate Card")
        picker.geometry("450x300")
        picker.transient(self.window)
        picker.grab_set()

        title = ctk.CTkLabel(
            picker,
            text="Select a Master Rate Card you would like to Load",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title.pack(pady=(20, 10))

        selected_var = tk.StringVar(value=master_names[0])

        dropdown = ctk.CTkComboBox(
            picker,
            values=master_names,
            variable=selected_var,
            state="readonly",
            width=320
        )
        dropdown.pack(pady=15)

        def load_selected():
            master_path = self.get_master_rate_cards_path()
            try:
                with open(master_path, "r", encoding="utf-8") as file_handle:
                    data = json.load(file_handle)

                selected_name = selected_var.get().strip()
                rate_card = data.get("rate_cards", {}).get(selected_name)

                if not rate_card:
                    messagebox.showerror("Error", f"Could not find master card: {selected_name}")
                    return

                self.current_file = master_path
                self.rate_card_data = rate_card
                self.current_master_card_name = selected_name
                self.info_text.configure(
                    text=f"Master Card: {selected_name}\nStored in: master_rate_cards.json"
                )
                picker.destroy()
                self.on_open()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load master rate card:\n{str(e)}")

        load_button = ctk.CTkButton(
            picker,
            text="Load Selected",
            command=load_selected,
            fg_color="green"
        )
        load_button.pack(pady=15)

        
    
    def __init__(self, parent):
        """Initialize the load rate card window."""
        self.parent = parent
        self.current_file = None
        self.rate_card_data = None
        self.current_master_card_name = None
        
        # Create window
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Load Rate Card")
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
            text="Load Rate Card",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(anchor="w")
        
        # Main content
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Button to browse
        browse_button = ctk.CTkButton(
            content_frame,
            text="Browse Rate Cards",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=50,
            corner_radius=10,
            command=self.on_browse
        )
        browse_button.pack(fill="x", pady=(0, 20))
        
        # File info section
        info_label = ctk.CTkLabel(
            content_frame,
            text="Recent Rate Cards:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        info_label.pack(anchor="w", pady=(10, 5))
        
        # List of recent files
        list_frame = ctk.CTkFrame(content_frame, fg_color="gray20", corner_radius=5)
        list_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Create Listbox with scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.file_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            height=10
        )
        self.file_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Bind selection
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_selected)
        self.file_listbox.bind("<Double-Button-1>", self.on_file_double_click)
        
        # Populate list
        self.populate_file_list()
        
        # Selected file info
        self.info_frame = ctk.CTkFrame(content_frame, fg_color="gray20", corner_radius=5)
        self.info_frame.pack(fill="x", pady=(0, 20))
        
        self.info_text = ctk.CTkLabel(
            self.info_frame,
            text="Select a rate card to view details",
            font=ctk.CTkFont(size=11),
            justify="left",
            wraplength=400
        )
        self.info_text.pack(anchor="w", padx=10, pady=10)
        
        # Buttons frame
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        master_button = ctk.CTkButton(
            button_frame,
            text="Load Master Rate Card",
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#8e44ad",
            hover_color="#7d3c98",
            command=self.on_load_master_rate_card
        )
        master_button.pack(side="left", padx=(0, 10), pady=10)


        # Open button
        open_button = ctk.CTkButton(
            button_frame,
            text="Open Selected",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="green",
            hover_color="darkgreen",
            command=self.on_open
        )
        open_button.pack(side="left", padx=5)
        
        # Delete button
        delete_button = ctk.CTkButton(
            button_frame,
            text="Delete",
            font=ctk.CTkFont(size=12),
            fg_color="red",
            hover_color="darkred",
            command=self.on_delete
        )
        delete_button.pack(side="left", padx=5)
        
        # Close button
        close_button = ctk.CTkButton(
            button_frame,
            text="Close",
            font=ctk.CTkFont(size=12),
            fg_color="gray40",
            command=self.window.destroy
        )
        close_button.pack(side="left", padx=5)
    
    def populate_file_list(self):
        """Populate the list of rate card files (both JSON and Excel)."""
        self.file_listbox.delete(0, "end")
        self._file_paths = []  # Reset stored file paths
        
        # Get rate card files from the module directory
        module_dir = Path(__file__).parent
        rate_card_files = []
        
        # Add JSON files from module directory
        json_files = list(module_dir.glob("rate_cards_*.json"))
        for file_path in sorted(json_files, key=lambda x: x.stat().st_mtime, reverse=True):
            rate_card_files.append((file_path.name, "JSON", str(file_path)))
        
        # Add Excel files from TheOneBP/RateCards if available
        if find_excel_rate_cards:
            try:
                excel_files = find_excel_rate_cards()
                for filename, filepath in excel_files:
                    rate_card_files.append((filename, "XLSX", filepath))
            except Exception as e:
                print(f"Warning: Could not load Excel rate cards: {e}")
        
        # Insert into listbox with type indicator
        for filename, file_type, filepath in rate_card_files:
            display_name = f"[{file_type}] {filename}"
            self.file_listbox.insert("end", display_name)
            # Store the actual filepath in a tag or separate structure
            self._file_paths.append(filepath)
    
    def on_file_selected(self, event):
        """Handle file selection."""
        selection = self.file_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        
        # Get the actual filepath from stored list
        if not hasattr(self, '_file_paths') or index >= len(self._file_paths):
            return
        
        file_path = self._file_paths[index]
        file_path = Path(file_path)
        
        if not file_path.exists():
            messagebox.showerror("Error", f"File not found: {file_path}")
            return
        
        try:
            # Load based on file type
            if file_path.suffix.lower() == '.xlsx':
                if load_excel_rate_card is None:
                    messagebox.showerror("Error", "Excel support not available. Install openpyxl.")
                    return
                self.rate_card_data = load_excel_rate_card(str(file_path))
            else:
                # JSON file
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.rate_card_data = json.load(f)
            
            self.current_file = file_path
            self.current_master_card_name = None  # Reset master card name since this is a selected file
            
            # Display info
            info = f"""
Name: {self.rate_card_data.get('name', 'N/A')}
Sponsor: {self.rate_card_data.get('sponsor', 'N/A')}
Type: {self.rate_card_data.get('type', 'itemized')}
Languages: {len(self.rate_card_data.get('languages', {}))}
Services: {len(self.rate_card_data.get('services', []))}
Source: {self.rate_card_data.get('source', 'Unknown')}
            """.strip()
            
            self.info_text.configure(text=info)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    def on_file_double_click(self, event):
        """Handle double-click to open file."""
        self.on_open()
    
    def on_browse(self):
        """Open file browser."""
        file_path = filedialog.askopenfilename(
            title="Select Rate Card",
            initialdir=str(Path(__file__).parent),
            filetypes=[
                ("All Supported", ("*.json", "*.xlsx")),
                ("JSON Rate Cards", "*.json"),
                ("Excel Rate Cards", "*.xlsx"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                file_path = Path(file_path)
                
                # Load based on file type
                if file_path.suffix.lower() == '.xlsx':
                    if load_excel_rate_card is None:
                        messagebox.showerror("Error", "Excel support not available. Install openpyxl and pandas.")
                        return
                    self.rate_card_data = load_excel_rate_card(str(file_path))
                else:
                    # JSON file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.rate_card_data = json.load(f)
                
                self.current_file = file_path
                self.current_master_card_name = None  # Reset master card name since this is a browsed file
                
                # Display info
                info = f"""
Name: {self.rate_card_data.get('name', 'N/A')}
Sponsor: {self.rate_card_data.get('sponsor', 'N/A')}
Type: {self.rate_card_data.get('type', 'itemized')}
Languages: {len(self.rate_card_data.get('languages', {}))}
Services: {len(self.rate_card_data.get('services', []))}
                """.strip()
                
                self.info_text.configure(text=info)
                messagebox.showinfo("File Loaded", f"Rate card loaded:\n{file_path.name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
                import traceback
                traceback.print_exc()

    def _save_rate_card_from_editor(self, updated_data):
        """Save edited data either to standalone file or to selected master entry."""
        if self.current_master_card_name:
            master_path = self.get_master_rate_cards_path()
            with open(master_path, "r", encoding="utf-8") as file_handle:
                master_data = json.load(file_handle)

            master_data.setdefault("rate_cards", {})
            master_data["rate_cards"][self.current_master_card_name] = updated_data

            with open(master_path, "w", encoding="utf-8") as file_handle:
                json.dump(master_data, file_handle, indent=2, ensure_ascii=False)
        else:
            with open(str(self.current_file), "w", encoding="utf-8") as file_handle:
                json.dump(updated_data, file_handle, indent=2, ensure_ascii=False)

        self.rate_card_data = updated_data
        self.populate_file_list()

    def _populate_editor_from_rate_card(self, editor):
        """Load self.rate_card_data into the itemized editor grid."""
        data = self.rate_card_data or {}

        loaded_iso_codes = data.get("iso_codes", {})
        if isinstance(loaded_iso_codes, dict):
            editor.local_iso_codes = {
                str(language_name).strip(): str(iso_code).strip()
                for language_name, iso_code in loaded_iso_codes.items()
                if str(language_name).strip() and str(iso_code).strip()
            }
        else:
            editor.local_iso_codes = {}

        global_services = editor._load_global_services()
        loaded_services = editor._extract_services_from_loaded_card(data)
        merged_services = editor._merge_service_names(global_services, loaded_services)
        if not merged_services:
            merged_services = editor._merge_service_names(global_services, editor.base_service_columns)

        editor._set_service_columns(merged_services, persist=False)
        editor._normalize_hidden_service_columns()

        current_name = data.get("name", "")
        if not current_name and self.current_master_card_name:
            current_name = self.current_master_card_name

        editor.name_entry.delete(0, "end")
        editor.name_entry.insert(0, current_name)

        editor.sponsor_entry.delete(0, "end")
        editor.sponsor_entry.insert(0, data.get("sponsor", ""))

        editor.languages_data = {}
        editor.missing_languages = []
        editor.error_label.configure(text="")

        for lang_name, lang_info in data.get("languages", {}).items():
            iso_code = lang_info.get("iso_code", "")
            loaded_rates = lang_info.get("rates", {}) if isinstance(lang_info.get("rates", {}), dict) else {}

            if lang_name in editor.local_iso_codes:
                iso_code = editor.local_iso_codes[lang_name]

            iso_data = editor.language_manager.get_by_code(iso_code) if iso_code else None
            is_found = iso_data is not None if iso_code else False

            editor.languages_data[lang_name] = {
                "iso_code": iso_code,
                "found": is_found,
                "rates": {
                    service_name: loaded_rates.get(service_name, "")
                    for service_name in editor.DEFAULT_SERVICES
                }
            }

            if iso_code:
                editor._set_local_iso_code(lang_name, iso_code)

            if iso_code and not is_found:
                editor.missing_languages.append(lang_name)

        editor._refresh_tree_structure()
        editor.update_table()
        editor.language_text.delete("1.0", "end")
    
    def on_open(self):
        """Open selected rate card in the itemized grid editor."""
        if not self.current_file or not self.rate_card_data:
            messagebox.showwarning("No Selection", "Please select a rate card first.")
            return

        if ItemizedRateCardEditor is None:
            messagebox.showerror(
                "Editor Unavailable",
                "Itemized editor module could not be imported."
            )
            return

        editor_window = ctk.CTkToplevel(self.window)
        if self.current_master_card_name:
            editor_window.title(f"Editing Master Rate Card: {self.current_master_card_name}")
        else:
            editor_window.title(f"Editing: {self.rate_card_data.get('name', 'Rate Card')}")
        editor_window.state("zoomed")

        host_frame = ctk.CTkFrame(editor_window, corner_radius=0)
        host_frame.pack(fill="both", expand=True)

        self.active_editor = LoadedRateCardEditor(
            host_frame,
            editor_window,
            self._save_rate_card_from_editor
        )
        self._populate_editor_from_rate_card(self.active_editor)
        
    def on_delete(self):
        """Delete selected rate card (file) or selected master rate card entry."""
        # Master-card delete path: remove only one entry from Core/master_rate_cards.json
        if self.current_master_card_name:
            confirm = messagebox.askyesno(
                "Confirm Delete",
                f"Delete master rate card '{self.current_master_card_name}'?\n\n"
                "This removes only this card from master_rate_cards.json."
            )
            if not confirm:
                return

            try:
                master_path = self.get_master_rate_cards_path()
                with open(master_path, "r", encoding="utf-8") as f:
                    master_data = json.load(f)

                cards = master_data.get("rate_cards", {})
                if self.current_master_card_name not in cards:
                    messagebox.showwarning(
                        "Not Found",
                        f"Master rate card '{self.current_master_card_name}' no longer exists."
                    )
                    return

                cards.pop(self.current_master_card_name, None)

                with open(master_path, "w", encoding="utf-8") as f:
                    json.dump(master_data, f, indent=2, ensure_ascii=False)

                messagebox.showinfo(
                    "Deleted",
                    f"Master rate card '{self.current_master_card_name}' deleted successfully."
                )

                self.populate_file_list()
                self.info_text.configure(text="Select a rate card to view details")
                self.current_file = None
                self.rate_card_data = None
                self.current_master_card_name = None
                return
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete master rate card:\n{str(e)}")
                return

        # Standalone file delete path
        if not self.current_file:
            messagebox.showwarning("No Selection", "Please select a rate card first.")
            return

        if messagebox.askyesno("Confirm Delete", f"Delete {self.current_file.name}?"):
            try:
                self.current_file.unlink()
                messagebox.showinfo("Deleted", "Rate card deleted successfully!")
                self.populate_file_list()
                self.info_text.configure(text="Select a rate card to view details")
                self.current_file = None
                self.rate_card_data = None
                self.current_master_card_name = None
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete:\n{str(e)}")
