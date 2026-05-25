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


class LoadRateCardWindow:
    """Window for loading and editing existing rate cards."""
    
    def __init__(self, parent):
        """Initialize the load rate card window."""
        self.parent = parent
        self.current_file = None
        self.rate_card_data = None
        
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
            if not hasattr(self, '_file_paths'):
                self._file_paths = []
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
    
    def on_open(self):
        """Open selected rate card for editing."""
        if not self.current_file or not self.rate_card_data:
            messagebox.showwarning("No Selection", "Please select a rate card first.")
            return
        
        # Display rate card content
        content = json.dumps(self.rate_card_data, indent=2, ensure_ascii=False)
        
        # Create a view window
        view_window = ctk.CTkToplevel(self.window)
        view_window.title(f"Editing: {self.rate_card_data.get('name', 'Rate Card')}")
        view_window.geometry("800x600")
        
        # Text area to display content
        text_area = ctk.CTkTextbox(view_window, wrap="word")
        text_area.pack(fill="both", expand=True, padx=10, pady=10)
        text_area.insert("1.0", content)
        
        # Save button
        def save_changes():
            try:
                updated_data = json.loads(text_area.get("1.0", "end-1c"))
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    json.dump(updated_data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", "Rate card saved successfully!")
                view_window.destroy()
                self.populate_file_list()
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Invalid JSON format.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save:\n{str(e)}")
        
        button_frame = ctk.CTkFrame(view_window)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        save_btn = ctk.CTkButton(button_frame, text="Save", command=save_changes, fg_color="green")
        save_btn.pack(side="left", padx=5)
        
        close_btn = ctk.CTkButton(button_frame, text="Close", command=view_window.destroy, fg_color="gray40")
        close_btn.pack(side="left", padx=5)
    
    def on_delete(self):
        """Delete selected rate card."""
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
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete:\n{str(e)}")
