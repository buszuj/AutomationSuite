"""
One Stop Shop - Main GUI
Central hub for job data import and GLE API integration
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, Menu
import tkinterdnd2 as tkdnd
import pandas as pd
import requests
import json
from pathlib import Path
import sys
import subprocess
import importlib.util
import os
from datetime import datetime

# Add Core to path for PA Template modules
core_path = Path(__file__).parent.parent / "Core"
sys.path.insert(0, str(core_path))

# Add Rate_Card_Builder to path for integration
rate_card_path = Path(__file__).parent.parent / "Rate_Card_Builder"
sys.path.insert(0, str(rate_card_path))

from pa_template_manager import PATemplateManager
from pa_template_processor import PATemplateProcessor
from quoteme_email_parser import QuoteeMEmailParser, get_parse_cache
from account_workflow_manager import AccountWorkflowManager
from language_normalizer import LanguageNormalizer
from service_mapper import ServiceMapper
from quoteme_value_mapper import QuoteMeValueMapper
from excel_rate_card_loader import load_excel_rate_card

# Import the parser UI (from same directory)
from quoteme_parser_ui import create_parser_tab

# Import Rate Card Builder integrated component
try:
    from rate_card_builder_integrated import setup_rate_cards_tab
except ImportError:
    setup_rate_cards_tab = None


class DataViewerWindow:
    """Window to display raw data in a spreadsheet-like view with pagination and search"""
    
    def __init__(self, parent, data_df):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Raw Data Viewer")
        self.window.geometry("1400x800")
        
        # Make window stay on top initially
        self.window.attributes('-topmost', True)
        self.window.after(100, lambda: self.window.attributes('-topmost', False))
        
        self.full_data_df = data_df
        self.data_df = data_df  # Current view (may be filtered)
        self.current_page = 0
        self.rows_per_page = 100
        self.search_text = ""
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the data viewer UI with search and pagination"""
        # Title
        title_label = ctk.CTkLabel(
            self.window,
            text="Raw Data Viewer",
            font=("Arial", 20, "bold")
        )
        title_label.pack(pady=15)
        
        # Search bar
        search_frame = ctk.CTkFrame(self.window, fg_color="#1f538d")
        search_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        search_inner = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_inner.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(
            search_inner,
            text="🔍 Search:",
            font=("Arial", 11, "bold"),
            text_color="white"
        ).pack(side="left", padx=5)
        
        self.search_entry = ctk.CTkEntry(
            search_inner,
            placeholder_text="Search in any column...",
            width=300,
            height=30
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind('<Return>', lambda e: self.apply_search())
        
        ctk.CTkButton(
            search_inner,
            text="Search",
            command=self.apply_search,
            width=80,
            height=30,
            fg_color="#2ecc71"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            search_inner,
            text="Clear",
            command=self.clear_search,
            width=80,
            height=30,
            fg_color="#e74c3c"
        ).pack(side="left", padx=5)
        
        # Info label
        self.info_label = ctk.CTkLabel(
            self.window,
            text="",
            font=("Arial", 11)
        )
        self.info_label.pack(pady=5)
        self.update_info_label()
        
        # Create main container frame
        container_frame = ctk.CTkFrame(self.window)
        container_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create canvas with scrollbars for horizontal and vertical scrolling
        canvas = ctk.CTkCanvas(container_frame, bg="#2b2b2b", highlightthickness=0)
        
        # Create scrollbars
        v_scrollbar = ctk.CTkScrollbar(container_frame, orientation="vertical", command=canvas.yview)
        h_scrollbar = ctk.CTkScrollbar(container_frame, orientation="horizontal", command=canvas.xview)
        
        # Create scrollable frame inside canvas
        scrollable_frame = ctk.CTkFrame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Create window in canvas
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and canvas
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Create header row with distinct styling
        header_frame = ctk.CTkFrame(scrollable_frame, fg_color="#1f538d")
        header_frame.pack(fill="x", pady=(0, 2))
        
        for col_idx, col_name in enumerate(self.data_df.columns):
            header_label = ctk.CTkLabel(
                header_frame,
                text=str(col_name),
                font=("Arial", 12, "bold"),
                width=200,
                height=40,
                anchor="w",
                fg_color="#1f538d",
                text_color="white",
                corner_radius=0
            )
            header_label.grid(row=0, column=col_idx, padx=1, pady=1, sticky="ew")
        
        # Create data rows for current page
        start_row = self.current_page * self.rows_per_page
        end_row = min(start_row + self.rows_per_page, len(self.data_df))
        
        for row_idx in range(start_row, end_row):
            row_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=0)
            
            # Alternate row colors
            row_color = "#2b2b2b" if (row_idx - start_row) % 2 == 0 else "#333333"
            
            for col_idx, col_name in enumerate(self.data_df.columns):
                cell_value = str(self.data_df.iloc[row_idx, col_idx])
                if pd.isna(self.data_df.iloc[row_idx, col_idx]):
                    cell_value = ""
                
                cell_label = ctk.CTkLabel(
                    row_frame,
                    text=cell_value,
                    font=("Arial", 10),
                    width=200,
                    height=30,
                    anchor="w",
                    fg_color=row_color,
                    corner_radius=0
                )
                cell_label.grid(row=0, column=col_idx, padx=1, pady=0, sticky="ew")
        
        # Pagination controls
        total_pages = (len(self.data_df) + self.rows_per_page - 1) // self.rows_per_page
        
        pagination_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        pagination_frame.pack(pady=10)
        
        ctk.CTkButton(
            pagination_frame,
            text="◄◄ First",
            command=self.first_page,
            width=80,
            height=30,
            state="normal" if self.current_page > 0 else "disabled"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            pagination_frame,
            text="◄ Prev",
            command=self.prev_page,
            width=80,
            height=30,
            state="normal" if self.current_page > 0 else "disabled"
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            pagination_frame,
            text=f"Page {self.current_page + 1} of {max(1, total_pages)}",
            font=("Arial", 11, "bold")
        ).pack(side="left", padx=15)
        
        ctk.CTkButton(
            pagination_frame,
            text="Next ►",
            command=self.next_page,
            width=80,
            height=30,
            state="normal" if self.current_page < total_pages - 1 else "disabled"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            pagination_frame,
            text="Last ►►",
            command=self.last_page,
            width=80,
            height=30,
            state="normal" if self.current_page < total_pages - 1 else "disabled"
        ).pack(side="left", padx=5)
        
        # Close button
        close_btn = ctk.CTkButton(
            self.window,
            text="Close",
            command=self.window.destroy,
            width=150,
            height=35
        )
        close_btn.pack(pady=15)
    
    def update_info_label(self):
        """Update info label with current view stats"""
        total = len(self.full_data_df)
        showing = len(self.data_df)
        cols = len(self.data_df.columns)
        
        if showing < total:
            text = f"Showing {showing} of {total} rows × {cols} columns (filtered)"
        else:
            text = f"Showing {showing} rows × {cols} columns"
        
        self.info_label.configure(text=text)
    
    def apply_search(self):
        """Apply search filter"""
        self.search_text = self.search_entry.get().strip().lower()
        
        if not self.search_text:
            self.clear_search()
            return
        
        # Filter data
        mask = self.full_data_df.astype(str).apply(
            lambda row: row.str.lower().str.contains(self.search_text, na=False).any(),
            axis=1
        )
        self.data_df = self.full_data_df[mask]
        self.current_page = 0
        self.update_info_label()
        self.refresh_display()
    
    def clear_search(self):
        """Clear search filter"""
        self.search_entry.delete(0, 'end')
        self.search_text = ""
        self.data_df = self.full_data_df
        self.current_page = 0
        self.update_info_label()
        self.refresh_display()
    
    def first_page(self):
        """Go to first page"""
        self.current_page = 0
        self.refresh_display()
    
    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_display()
    
    def next_page(self):
        """Go to next page"""
        total_pages = (len(self.data_df) + self.rows_per_page - 1) // self.rows_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.refresh_display()
    
    def last_page(self):
        """Go to last page"""
        total_pages = (len(self.data_df) + self.rows_per_page - 1) // self.rows_per_page
        self.current_page = max(0, total_pages - 1)
        self.refresh_display()
    
    def refresh_display(self):
        """Refresh the entire display"""
        # Destroy current window and create new one
        self.window.destroy()
        self.window = ctk.CTkToplevel()
        self.window.title("Raw Data Viewer")
        self.window.geometry("1400x800")
        self.setup_ui()


class GLEAPIClient:
    """Client for TransPerfect GLE API"""
    
    TOKEN_URL = "https://sso.transperfect.com/connect/token"
    CLIENT_ID = "6wZh7rFrLCQh0ZWGrMz8AcZWVAg74BqT"
    CLIENT_SECRET = "c9H58gvpDyc46NY10Fp2eLVafTMtNzLg"
    SCOPES = "TransPort Read"
    ORG_ID = "51334c7b-d7fb-4d40-ae95-f2f6808d97da"
    BASE_API_URL = "https://portal.transperfect.com/api/projects/analytics-export/"
    
    def __init__(self):
        self.access_token = None
    
    def get_access_token(self):
        """Get OAuth access token"""
        try:
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.CLIENT_ID,
                "client_secret": self.CLIENT_SECRET,
                "scope": self.SCOPES
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            response = requests.post(self.TOKEN_URL, data=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            return self.access_token
            
        except Exception as e:
            raise Exception(f"Failed to get access token: {str(e)}")
    
    def fetch_project_data(self, job_id):
        """Fetch project data from GLE API"""
        try:
            if not self.access_token:
                self.get_access_token()
            
            api_url = f"{self.BASE_API_URL}{self.ORG_ID}"
            
            request_body = {
                "Sort": "CreatedDate",
                "SortDirection": 1,
                "Skip": 0,
                "Take": 1000,
                "Archived": False,
                "Search": job_id
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(api_url, json=request_body, headers=headers, timeout=30)
            response.raise_for_status()
            
            # The API returns an Excel file as binary data
            return response.content
            
        except Exception as e:
            raise Exception(f"Failed to fetch project data: {str(e)}")


class OneStopShopMain:
    """Main GUI for One Stop Shop"""
    
    def __init__(self):
        # Initialize main window with drag-and-drop support
        self.root = tkdnd.Tk()
        self.root.title("One Stop Shop - Main")
        
        # Make window fullscreen
        self.root.state('zoomed')  # Windows fullscreen
        
        # Set appearance to dark mode
        ctk.set_appearance_mode("dark")  # Force dark mode for consistency
        ctk.set_default_color_theme("blue")
        
        # Data storage
        self.current_data = None  # Stores DataFrame (full dataset)
        self.filtered_job_data = None  # Stores aggregated job data when job ID is filtered
        self.current_account = None  # Selected account for configurations
        self.visible_columns = []  # Track which columns user wants to see
        self.column_prefs_file = Path(__file__).parent.parent / "Core" / "column_preferences.json"
        self.job_config_file = Path(__file__).parent.parent / "Core" / "job_data_config.json"
        self.current_job_id = None  # Currently filtered job ID
        self.index_column = None  # Column configured as job index
        
        # Drag-and-drop state for reordering
        self.drag_source = None
        self.drag_source_index = None
        
        # Initialize PA Template system
        self.template_manager = PATemplateManager()
        self.template_processor = PATemplateProcessor(self.template_manager)
        self.last_generated_file = None  # Track last generated Excel file
        
        # API client
        self.api_client = GLEAPIClient()
        
        # Account & Workflow Manager
        self.account_workflow_manager = AccountWorkflowManager()
        
        # Language Normalizer
        self.language_normalizer = LanguageNormalizer()
        
        # Service Mapper for rate card normalization
        self.service_mapper = ServiceMapper()
        
        # QuoteMe Value Mapper for word count field mapping
        self.quoteme_value_mapper = QuoteMeValueMapper()
        
        # Rate card and workflow tracking
        self.selected_workflow = None
        self.selected_rate_card = None
        self.cached_rate_card = None  # Cache normalized rate card to persist across workflow changes
        self.quoteme_data = None  # Stores parsed QuoteMe data
        self.language_pairs = []  # Language pairs from QuoteMe
        self.workflow_service_data = {}  # Stores service data: {service_name: {lp: {quantity, rate}}}
        
        # Setup menu bar BEFORE UI
        self.setup_menu_bar()
        
        self.setup_ui()
    
    def setup_menu_bar(self):
        """Setup menu bar with configuration options"""
        menubar = Menu(self.root, bg="#1f538d", fg="white", activebackground="#2b7dbc", activeforeground="white", font=("Arial", 11, "bold"))
        self.root.configure(menu=menubar)
        
        # Configuration menu
        config_menu = Menu(menubar, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#1f538d", activeforeground="white", font=("Arial", 10))
        menubar.add_cascade(label="  Configuration  ", menu=config_menu)
        config_menu.add_command(label="Select Account", command=self.select_account)
        config_menu.add_separator()
        config_menu.add_command(label="QuoteMe Email Parser", command=self.open_quoteme_parser_fixed)
        config_menu.add_separator()
        config_menu.add_command(label="Manage Entities", command=self.open_entity_manager)
        config_menu.add_command(label="Map Services", command=self.open_service_mapper)
        config_menu.add_command(label="Configure Workflows", command=self.open_workflow_manager)
        
        # PA Template menu
        pa_menu = Menu(menubar, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#1f538d", activeforeground="white", font=("Arial", 10))
        menubar.add_cascade(label="  PA Template  ", menu=pa_menu)
        pa_menu.add_command(label="Configure Template Mapper", command=self.open_template_mapper)
        pa_menu.add_command(label="Preview Integration Data", command=self.preview_integration_data)
        pa_menu.add_separator()
        pa_menu.add_command(label="Generate PA Worksheets", command=self.generate_pa_worksheets)
        pa_menu.add_command(label="Kick Off Automation", command=self.kick_off_automation)
        
        # Store menu references for enabling/disabling
        self.config_menu = config_menu
        self.pa_menu = pa_menu
        
        # View menu
        view_menu = Menu(menubar, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#1f538d", activeforeground="white", font=("Arial", 10))
        menubar.add_cascade(label="  View  ", menu=view_menu)
        view_menu.add_command(label="Show Raw Data", command=self.show_raw_data)
        view_menu.add_command(label="Configure Index Column", command=self.configure_index_column)
        view_menu.add_command(label="Refresh", command=self.refresh_ui)
        
        # Help menu
        help_menu = Menu(menubar, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#1f538d", activeforeground="white", font=("Arial", 10))
        menubar.add_cascade(label="  Help  ", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def select_account(self):
        """Modal dialog to select/create/edit/delete accounts"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Manage Accounts")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()  # Make modal
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f'500x600+{x}+{y}')
        
        # Title
        ctk.CTkLabel(
            dialog,
            text="Manage Accounts",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        # Info label
        ctk.CTkLabel(
            dialog,
            text="Select, create, edit, or delete accounts",
            font=("Arial", 11),
            text_color="gray"
        ).pack(pady=10)
        
        # Load accounts from Core
        try:
            core_path = Path(__file__).parent.parent / "Core"
            sys.path.insert(0, str(core_path))
            from account_workflow_manager import AccountWorkflowManager
            
            manager = AccountWorkflowManager()
            accounts = manager.get_accounts()
            
            # Account list
            listbox_frame = ctk.CTkScrollableFrame(dialog, height=250)
            listbox_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            selected_account = ctk.StringVar(value=self.current_account or "")
            
            if not accounts:
                ctk.CTkLabel(
                    listbox_frame,
                    text="No accounts found. Create one below.",
                    text_color="orange"
                ).pack(pady=20)
            else:
                for account in accounts:
                    radio = ctk.CTkRadioButton(
                        listbox_frame,
                        text=account,
                        variable=selected_account,
                        value=account,
                        font=("Arial", 12)
                    )
                    radio.pack(anchor="w", padx=10, pady=5)
            
            # Account management buttons
            mgmt_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            mgmt_frame.pack(pady=10)
            
            def create_new_account():
                new_dialog = ctk.CTkToplevel(dialog)
                new_dialog.title("Create Account")
                new_dialog.geometry("400x200")
                new_dialog.transient(dialog)
                new_dialog.grab_set()
                
                ctk.CTkLabel(new_dialog, text="Enter Account Name:", font=("Arial", 12)).pack(pady=20)
                name_entry = ctk.CTkEntry(new_dialog, width=300, font=("Arial", 12))
                name_entry.pack(pady=10)
                
                def save_account():
                    account_name = name_entry.get().strip()
                    if not account_name:
                        messagebox.showwarning("Invalid Name", "Account name cannot be empty")
                        return
                    
                    if manager.create_account(account_name):
                        # Account created successfully
                        new_dialog.destroy()
                        dialog.destroy()
                        self.select_account()  # Reopen with updated list
                    else:
                        messagebox.showerror("Error", "Account already exists or creation failed")
                
                ctk.CTkButton(new_dialog, text="Create", command=save_account, width=120).pack(pady=10)
            
            def delete_account():
                if not selected_account.get():
                    messagebox.showwarning("No Selection", "Please select an account to delete")
                    return
                
                confirm = messagebox.askyesno(
                    "Confirm Delete",
                    f"Are you sure you want to delete '{selected_account.get()}'?\n\nThis will delete all workflows and configurations for this account."
                )
                
                if confirm:
                    if manager.delete_account(selected_account.get()):
                        # Account deleted successfully
                        if self.current_account == selected_account.get():
                            self.current_account = None
                        dialog.destroy()
                        self.select_account()  # Reopen with updated list
                        self.refresh_ui()
                    else:
                        messagebox.showerror("Error", "Failed to delete account")
            
            def rename_account():
                if not selected_account.get():
                    messagebox.showwarning("No Selection", "Please select an account to rename")
                    return
                
                rename_dialog = ctk.CTkToplevel(dialog)
                rename_dialog.title("Rename Account")
                rename_dialog.geometry("400x200")
                rename_dialog.transient(dialog)
                rename_dialog.grab_set()
                
                ctk.CTkLabel(rename_dialog, text=f"Rename '{selected_account.get()}' to:", font=("Arial", 12)).pack(pady=20)
                name_entry = ctk.CTkEntry(rename_dialog, width=300, font=("Arial", 12))
                name_entry.insert(0, selected_account.get())
                name_entry.pack(pady=10)
                
                def save_rename():
                    new_name = name_entry.get().strip()
                    if not new_name:
                        messagebox.showwarning("Invalid Name", "Account name cannot be empty")
                        return
                    
                    if manager.rename_account(selected_account.get(), new_name):
                        # Account renamed successfully
                        if self.current_account == selected_account.get():
                            self.current_account = new_name
                        rename_dialog.destroy()
                        dialog.destroy()
                        self.select_account()  # Reopen with updated list
                        self.refresh_ui()
                    else:
                        messagebox.showerror("Error", "Account already exists or rename failed")
                
                ctk.CTkButton(rename_dialog, text="Rename", command=save_rename, width=120).pack(pady=10)
            
            ctk.CTkButton(mgmt_frame, text="➕ Create New", command=create_new_account, width=140, fg_color="green").pack(side="left", padx=5)
            ctk.CTkButton(mgmt_frame, text="✏️ Rename", command=rename_account, width=140, fg_color="orange").pack(side="left", padx=5)
            ctk.CTkButton(mgmt_frame, text="🗑️ Delete", command=delete_account, width=140, fg_color="#d32f2f").pack(side="left", padx=5)
            
            # Selection buttons
            button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            button_frame.pack(pady=20)
            
            def confirm_selection():
                if selected_account.get():
                    self.current_account = selected_account.get()
                    # Clear rate card cache when account changes
                    self.selected_rate_card = None
                    self.cached_rate_card = None
                    self.update_account_display()
                    self.update_status(f"Active account: {self.current_account}")
                    # Account set as active
                    dialog.destroy()
                    self.refresh_ui()
                    # Refresh workflow and rate card dropdowns for Job Data tab
                    self.refresh_workflow_dropdown()
                    self.refresh_rate_card_dropdown()
                else:
                    messagebox.showwarning("No Selection", "Please select an account")
            
            ctk.CTkButton(
                button_frame,
                text="Select Account",
                command=confirm_selection,
                width=150,
                height=35,
                font=("Arial", 12, "bold")
            ).pack(side="left", padx=10)
            
            ctk.CTkButton(
                button_frame,
                text="Cancel",
                command=dialog.destroy,
                width=120,
                height=35,
                fg_color="gray",
                text_color="white"
            ).pack(side="left", padx=10)
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load accounts: {str(e)}")
            dialog.destroy()
    
    def open_quoteme_parser_fixed(self):
        """Open the QuoteMe Email Parser window with proper close handling"""
        parser_window = None
        
        def check_parser_window():
            nonlocal parser_window
            if parser_window is not None:
                try:
                    if parser_window.winfo_exists():
                        parser_window.lift()
                        parser_window.focus()
                        return
                except:
                    pass
            
            def on_parser_apply(lp_code: str, lp_data):
                """Callback when parser applies data"""
                messagebox.showinfo("Success", f"Parsed data for:\n{lp_code}\n\nData cached and ready for use.")
            
            def on_parser_complete(parse_result):
                """Callback when parsing completes - update Job Data tab"""
                if parse_result and parse_result.success and parse_result.language_pairs:
                    try:
                        self.set_language_pairs_from_quoteme(parse_result.language_pairs)
                    except Exception as e:
                        print(f"Error updating Job Data with parsed language pairs: {e}")
            
            # Create floating window
            parser_window = ctk.CTkToplevel(self.root)
            parser_window.title("QuoteMe Email Parser")
            parser_window.geometry("1000x700")
            parser_window.transient(self.root)
            parser_window.attributes('-topmost', True)
            parser_window.after(100, lambda: parser_window.attributes('-topmost', False))
            
            try:
                # Create parser tab
                parser_tab = create_parser_tab(parser_window, on_apply_callback=on_parser_apply, on_parse_complete_callback=on_parser_complete)
                
                # FIXED: Proper window close handling
                def on_closing():
                    nonlocal parser_window
                    try:
                        if parser_window is not None and parser_window.winfo_exists():
                            parser_window.destroy()
                    except:
                        pass
                    parser_window = None
                
                parser_window.protocol("WM_DELETE_WINDOW", on_closing)
                
                # Ensure parser window can be properly closed
                parser_window.bind('<Escape>', lambda e: on_closing())
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open parser: {str(e)}")
                if parser_window:
                    try:
                        parser_window.destroy()
                    except:
                        pass
                parser_window = None
        
        check_parser_window()
    
    def update_account_display(self):
        """Update account display and show/hide tabs based on account selection"""
        if self.current_account:
            self.account_info_label.configure(text=self.current_account)
            # Show tabs
            if hasattr(self, 'account_prompt') and hasattr(self, 'main_tabs'):
                self.account_prompt.pack_forget()
                self.main_tabs.pack(fill="both", expand=True)
            # Reload PA Template Mapper with the newly selected account
            self.refresh_pa_integration_tab()
        else:
            self.account_info_label.configure(text="None Selected")
            # Hide tabs, show prompt
            if hasattr(self, 'account_prompt') and hasattr(self, 'main_tabs'):
                self.main_tabs.pack_forget()
                self.account_prompt.pack(fill="both", expand=True, padx=50, pady=50)
            # Clear the mapper
            self.refresh_pa_integration_tab()
    
    def open_entity_manager(self):
        """Launch Entity Manager in modal mode"""
        try:
            # Import and run entity manager
            launch_path = Path(__file__).parent / "launch_entity_manager.py"
            
            if not launch_path.exists():
                messagebox.showerror("Error", "Entity Manager not found")
                return
            
            # Run as subprocess to keep it modal-like
            subprocess.Popen([sys.executable, str(launch_path)])
            
            # Wait a moment then refresh
            self.root.after(500, self.refresh_ui)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Entity Manager: {str(e)}")
    
    def open_service_mapper(self):
        """Open service mapping management dialog"""
        if not self.current_account:
            messagebox.showwarning("Warning", "Please select an account first")
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Service Mapper - {self.current_account}")
        dialog.geometry("700x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Title
        title_label = ctk.CTkLabel(
            dialog,
            text=f"Manage Service Mappings for {self.current_account}",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=15, padx=20)
        
        # Info
        info_text = ctk.CTkLabel(
            dialog,
            text="Select a rate card to view and edit its service mappings.",
            font=("Arial", 10),
            text_color="#888"
        )
        info_text.pack(pady=5, padx=20)
        
        # Rate card selection frame
        selection_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        selection_frame.pack(fill="x", padx=20, pady=10)
        
        selection_label = ctk.CTkLabel(selection_frame, text="Rate Card:", font=("Arial", 10, "bold"))
        selection_label.pack(side="left", padx=(0, 10))
        
        available_rate_cards = self.get_available_rate_cards()
        rate_card_dropdown = ctk.CTkComboBox(
            selection_frame,
            values=available_rate_cards,
            state="readonly",
            width=300,
            font=("Arial", 10)
        )
        rate_card_dropdown.pack(side="left")
        
        # Mappings frame
        mappings_frame = ctk.CTkFrame(dialog, fg_color="#2b2b2b")
        mappings_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        mappings_label = ctk.CTkLabel(
            mappings_frame,
            text="Service Mappings:",
            font=("Arial", 11, "bold")
        )
        mappings_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Scrollable area for mappings
        scroll_frame = ctk.CTkScrollableFrame(mappings_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        def on_rate_card_select(rc_name: str):
            """Update mappings display when rate card is selected"""
            # Clear current mappings display
            for widget in scroll_frame.winfo_children():
                widget.destroy()
            
            if not rc_name:
                return
            
            # Load mappings for this rate card
            mappings = self.service_mapper.load_mapping(self.current_account, rc_name)
            
            if not mappings:
                no_mappings_label = ctk.CTkLabel(
                    scroll_frame,
                    text="No custom mappings for this rate card. Services are using canonical names.",
                    font=("Arial", 10),
                    text_color="#888"
                )
                no_mappings_label.pack(pady=20)
                return
            
            # Display mappings
            for rate_card_service, canonical_service in sorted(mappings.items()):
                mapping_frame = ctk.CTkFrame(scroll_frame, fg_color="#3b3b3b", corner_radius=5)
                mapping_frame.pack(fill="x", pady=5)
                
                # Rate card service name
                rc_label = ctk.CTkLabel(
                    mapping_frame,
                    text=f"Rate Card: {rate_card_service}",
                    font=("Arial", 10),
                    text_color="#aaa",
                    anchor="w"
                )
                rc_label.pack(fill="x", padx=10, pady=(8, 2))
                
                # Arrow
                arrow_label = ctk.CTkLabel(
                    mapping_frame,
                    text="↓",
                    font=("Arial", 12),
                    text_color="#2b7dbc"
                )
                arrow_label.pack()
                
                # Canonical name
                canonical_label = ctk.CTkLabel(
                    mapping_frame,
                    text=f"Canonical: {canonical_service}",
                    font=("Arial", 10, "bold"),
                    text_color="#fff",
                    anchor="w"
                )
                canonical_label.pack(fill="x", padx=10, pady=(2, 8))
        
        # Bind selection change
        rate_card_dropdown.configure(command=on_rate_card_select)
        
        # Close button
        close_btn = ctk.CTkButton(
            dialog,
            text="Close",
            command=dialog.destroy,
            fg_color="#555",
            width=120
        )
        close_btn.pack(pady=15)

    
    def open_workflow_manager(self):
        """Launch Workflow Manager in modal mode"""
        try:
            launch_path = Path(__file__).parent / "launch_workflow_manager.py"
            
            if not launch_path.exists():
                messagebox.showerror("Error", "Workflow Manager not found")
                return
            
            # Run as subprocess
            subprocess.Popen([sys.executable, str(launch_path)])
            self.root.after(500, self.refresh_ui)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Workflow Manager: {str(e)}")
    
    def open_template_mapper(self):
        """Launch PA Template Mapper GUI"""
        if not self.current_account:
            messagebox.showwarning("No Account", "Please select an account first")
            return
        
        # Import the mapper GUI
        from gui.pa_template_mapper_gui import launch_template_mapper
        
        # Launch with current data if available
        launch_template_mapper(self.root, self.current_account, self.current_data)
    
    def generate_pa_worksheets(self):
        """Generate PA worksheets from loaded job data"""
        # Use filtered job data if available, otherwise full data
        source_data = self.filtered_job_data if self.filtered_job_data is not None else self.current_data
        
        if source_data is None:
            messagebox.showwarning("No Data", "Please import job data first")
            return
        
        if not self.current_account:
            messagebox.showwarning("No Account", "Please select an account first")
            return
        
        # Check if template exists for this account
        template = self.template_manager.get_template(self.current_account)
        if not template:
            result = messagebox.askyesno(
                "No Template",
                f"No PA template configured for account '{self.current_account}'.\n\n"
                "Would you like to configure one now?"
            )
            if result:
                self.open_template_mapper()
            return
        
        try:
            # Use configured index column if available, otherwise auto-detect
            group_col = self.index_column
            
            if not group_col:
                # Determine grouping column (look for Sub_ID or similar)
                for col in ["Sub_ID", "Job_ID", "ID", "sub_id", "job_id"]:
                    if col in source_data.columns:
                        group_col = col
                        break
            
            if not group_col:
                messagebox.showwarning(
                    "No ID Column",
                    "Could not find Sub_ID or Job_ID column in data.\n\n"
                    "Please configure the index column using View → Configure Index Column."
                )
                return
            
            # Process data
            self.update_status("Processing PA templates...")
            results = self.template_processor.process_multiple_rows(
                source_data,
                self.current_account,
                group_by_column=group_col
            )
            
            if not results:
                messagebox.showwarning("No Results", "No worksheets generated")
                return
            
            # Ask where to save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"PA_Import_{self.current_account}_{timestamp}.xlsx"
            
            filepath = filedialog.asksaveasfilename(
                title="Save PA Worksheets",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=default_filename
            )
            
            if not filepath:
                return
            
            # Export to Excel
            self.update_status("Exporting to Excel...")
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                for sub_id, df in results.items():
                    # Create worksheet name
                    ws_name = f"Sub_{sub_id}"
                    if len(ws_name) > 31:  # Excel limit
                        ws_name = ws_name[:31]
                    
                    # Write DataFrame
                    df.to_excel(writer, sheet_name=ws_name, index=False)
            
            self.last_generated_file = filepath
            self.update_status(f"Generated {len(results)} worksheet(s)")
            
            # Update inline status labels in the Generate Worksheets sub-tab
            if hasattr(self, 'pa_generate_status'):
                self.pa_generate_status.configure(
                    text=f"✅ {len(results)} worksheet(s) generated", text_color="#2ecc71"
                )
            if hasattr(self, 'pa_last_file_label'):
                self.pa_last_file_label.configure(
                    text=f"Last file: {Path(filepath).name}", text_color="#95a5a6"
                )
            
            # Ask if user wants to open the file
            result = messagebox.askyesno(
                "Export Complete",
                f"Successfully generated {len(results)} PA worksheet(s):\n\n"
                f"{filepath}\n\n"
                "Would you like to open the file?"
            )
            
            if result:
                os.startfile(filepath)
            
        except Exception as e:
            messagebox.showerror("Generation Error", f"Failed to generate PA worksheets:\n\n{str(e)}")
            self.update_status("Error generating worksheets")
            if hasattr(self, 'pa_generate_status'):
                self.pa_generate_status.configure(text="⚠️ Generation failed", text_color="#e74c3c")
    
    def preview_integration_data(self):
        """Preview PA integration data before exporting"""
        # Use filtered job data if available, otherwise full data
        source_data = self.filtered_job_data if self.filtered_job_data is not None else self.current_data
        
        if source_data is None:
            messagebox.showwarning("No Data", "Please import job data first")
            return
        
        if not self.current_account:
            messagebox.showwarning("No Account", "Please select an account first")
            return
        
        # Check if template exists
        template = self.template_manager.get_template(self.current_account)
        if not template:
            messagebox.showwarning(
                "No Template",
                f"No PA template configured for account '{self.current_account}'.\n\n"
                "Please configure a template first."
            )
            return
        
        try:
            self.update_status("Generating preview...")
            
            # Process first row as preview
            preview_df = self.template_processor.process_dataframe(
                source_data,
                source_data,
                self.current_account,
                row_index=0
            )
            
            if preview_df is None or len(preview_df) == 0:
                messagebox.showerror("Preview Error", "Failed to generate preview - no data returned")
                self.update_status("Preview failed")
                return
            
            self.update_status("Displaying preview...")
            
            # Create preview window
            preview_window = ctk.CTkToplevel(self.root)
            preview_window.title(f"PA Integration Preview - {self.current_account}")
            preview_window.geometry("900x700")
            preview_window.transient(self.root)
            preview_window.grab_set()
            
            # Header
            header_frame = ctk.CTkFrame(preview_window, fg_color="#1f538d")
            header_frame.pack(fill="x")
            
            ctk.CTkLabel(
                header_frame,
                text="📄 PA Integration Data Preview",
                font=("Arial", 18, "bold"),
                text_color="white"
            ).pack(pady=15)
            
            ctk.CTkLabel(
                header_frame,
                text=f"Account: {self.current_account} | Template: {template.get('template_name', 'Unknown')} | Rows: {len(preview_df)}",
                font=("Arial", 11),
                text_color="#e0e0e0"
            ).pack(pady=(0, 15))
            
            # Preview scrollable frame
            preview_scroll = ctk.CTkScrollableFrame(preview_window, fg_color="#1e1e1e")
            preview_scroll.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Get column names
            if len(preview_df.columns) < 2:
                messagebox.showerror("Preview Error", f"Expected 2 columns, got {len(preview_df.columns)}")
                preview_window.destroy()
                return
            
            key_col = preview_df.columns[0]
            data_col = preview_df.columns[1]
            
            # Header row
            header_row = ctk.CTkFrame(preview_scroll, fg_color="#2b7dbc")
            header_row.pack(fill="x", pady=(5, 10), padx=5)
            
            ctk.CTkLabel(
                header_row,
                text=key_col,
                font=("Arial", 12, "bold"),
                text_color="white",
                width=300,
                anchor="w"
            ).pack(side="left", padx=15, pady=10)
            
            ctk.CTkLabel(
                header_row,
                text=data_col,
                font=("Arial", 12, "bold"),
                text_color="white",
                anchor="w"
            ).pack(side="left", padx=15, pady=10, fill="x", expand=True)
            
            # Data rows
            for idx, row in preview_df.iterrows():
                row_frame = ctk.CTkFrame(
                    preview_scroll,
                    fg_color="#252525" if idx % 2 == 0 else "#2b2b2b"
                )
                row_frame.pack(fill="x", pady=2, padx=5)
                
                # Key
                ctk.CTkLabel(
                    row_frame,
                    text=str(row[key_col]),
                    font=("Arial", 11),
                    text_color="#3498db",
                    width=300,
                    anchor="w"
                ).pack(side="left", padx=15, pady=8)
                
                # Value
                value_text = str(row[data_col]) if pd.notna(row[data_col]) else ""
                ctk.CTkLabel(
                    row_frame,
                    text=value_text,
                    font=("Arial", 11),
                    text_color="white",
                    anchor="w",
                    wraplength=500,
                    justify="left"
                ).pack(side="left", padx=15, pady=8, fill="x", expand=True)
            
            # Close button
            ctk.CTkButton(
                preview_window,
                text="Close",
                command=preview_window.destroy,
                width=150,
                height=35,
                font=("Arial", 12, "bold")
            ).pack(pady=(0, 20))
            
            self.update_status("Preview displayed")
            
        except Exception as e:
            error_msg = f"Failed to generate preview:\n\n{str(e)}\n\nType: {type(e).__name__}"
            messagebox.showerror("Preview Error", error_msg)
            self.update_status("Preview error")
            print(f"Preview error details: {e}")  # Debug output
    
    def kick_off_automation(self):
        """Trigger ProjectA import automation using KickOff.py"""
        if not self.last_generated_file or not os.path.exists(self.last_generated_file):
            messagebox.showwarning(
                "No File",
                "Please generate PA worksheets first.\n\n"
                "Use 'Generate PA Worksheets' to create the Excel file."
            )
            return
        
        result = messagebox.askyesno(
            "Kick Off Automation",
            f"This will trigger the ProjectA import automation for:\n\n"
            f"{self.last_generated_file}\n\n"
            "The automation will:\n"
            "1. Open the Excel file\n"
            "2. Process each Sub_ID worksheet pair\n"
            "3. Trigger TransPerfect ProjectA import\n\n"
            "Continue?"
        )
        
        if not result:
            return
        
        try:
            # Import KickOff module
            kickoff_path = Path(__file__).parent.parent / "CEVA_Launcher" / "KickOff.py"
            
            if not kickoff_path.exists():
                messagebox.showerror(
                    "KickOff Not Found",
                    f"KickOff.py not found at:\n{kickoff_path}"
                )
                return
            
            # Import the module
            spec = importlib.util.spec_from_file_location("KickOff", str(kickoff_path))
            kickoff_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(kickoff_module)
            
            # Run the process
            self.update_status("Starting ProjectA automation...")
            kickoff_module.process_excel_file(self.last_generated_file)
            self.update_status("Automation complete")
            
        except Exception as e:
            messagebox.showerror("Automation Error", f"Failed to run automation:\n\n{str(e)}")
            self.update_status("Automation failed")
    
    def show_gle_dialog(self):
        """Show GLE API dialog to pull data"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Pull from GLE API")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (250)
        y = (dialog.winfo_screenheight() // 2) - (150)
        dialog.geometry(f'500x300+{x}+{y}')
        
        # Title
        ctk.CTkLabel(
            dialog,
            text="🌐 Pull Data from GLE API",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        # Info
        ctk.CTkLabel(
            dialog,
            text="Enter the GL Portal Number (Job ID) to fetch data",
            font=("Arial", 11),
            text_color="gray"
        ).pack(pady=5)
        
        # Job ID input
        input_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        input_frame.pack(pady=30)
        
        ctk.CTkLabel(
            input_frame,
            text="Job ID:",
            font=("Arial", 13, "bold")
        ).pack(side="left", padx=(0, 10))
        
        job_id_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Enter GL Portal Number",
            width=250,
            height=40,
            font=("Arial", 13)
        )
        job_id_entry.pack(side="left", padx=10)
        job_id_entry.focus()
        
        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=20)
        
        def pull_data():
            job_id = job_id_entry.get().strip()
            
            if not job_id:
                messagebox.showwarning("Missing Input", "Please enter a Job ID")
                return
            
            dialog.destroy()
            
            try:
                self.update_status("Fetching data from GLE API...")
                
                # Fetch data from API
                excel_data = self.api_client.fetch_project_data(job_id)
                
                # Save to temporary file and read
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    tmp_file.write(excel_data)
                    tmp_path = tmp_file.name
                
                # Read Excel data
                df = pd.read_excel(tmp_path)
                
                # Clean up temp file
                Path(tmp_path).unlink()
                
                # Store data
                self.current_data = df
                self.data_source = 'api'

                # Load index column configuration if available
                if not self.index_column and self.current_account:
                    self.index_column = self.load_index_column(self.current_account)

                # Default to GL Portal No for API pulls if not configured
                if not self.index_column and "GL Portal No" in df.columns:
                    self.index_column = "GL Portal No"

                # Set current job id from GL Portal No (first row) and pre-filter data
                if self.index_column and self.index_column in df.columns and len(df) > 0:
                    first_job_id = df.iloc[0][self.index_column]
                    if pd.notna(first_job_id) and str(first_job_id).strip():
                        self.current_job_id = str(first_job_id).strip()
                        filtered_df = df[df[self.index_column].astype(str) == self.current_job_id]
                        if not filtered_df.empty:
                            self.filtered_job_data = self.aggregate_job_data(filtered_df)
                            if hasattr(self, "job_id_entry"):
                                self.job_id_entry.delete(0, "end")
                                self.job_id_entry.insert(0, self.current_job_id)
                            if hasattr(self, "filter_status_label"):
                                self.filter_status_label.configure(
                                    text=f"✅ Showing job: {self.current_job_id} ({len(filtered_df)} rows aggregated)",
                                    text_color="#2ecc71"
                                )
                
                # Update UI
                self.update_status(f"✅ GLE data pulled for Job ID: {job_id}")
                self.update_data_info()
                
                messagebox.showinfo(
                    "Success",
                    f"Data pulled successfully!\\n\\nJob ID: {job_id}\\nRows: {len(df)}\\nColumns: {len(df.columns)}"
                )
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to pull GLE data:\\n{str(e)}")
                self.update_status("❌ Failed to pull GLE data")
        
        # Bind Enter key to pull data
        job_id_entry.bind("<Return>", lambda e: pull_data())
        
        ctk.CTkButton(
            button_frame,
            text="Pull Data",
            command=pull_data,
            width=150,
            height=40,
            font=("Arial", 13, "bold"),
            fg_color="#2ecc71",
            hover_color="#27ae60"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            width=120,
            height=40,
            fg_color="gray",
            text_color="white"
        ).pack(side="left", padx=10)
    
    def pull_gle_data_from_entry(self):
        """Pull GLE data using the job ID from the entry field"""
        job_id = self.gle_entry.get().strip()
        
        if not job_id:
            messagebox.showwarning("Missing Input", "Please enter a Job ID in the GLE entry field")
            return
        
        try:
            self.update_status("Fetching data from GLE API...")
            # Fetch data from API
            excel_data = self.api_client.fetch_project_data(job_id)
            
            # Save to temporary file and read
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                tmp_file.write(excel_data)
                tmp_path = tmp_file.name

            # Read Excel data
            df = pd.read_excel(tmp_path)
            Path(tmp_path).unlink()  # Clean up temp file

            # Store data
            self.current_data = df
            self.data_source = 'api'

            #load index column configuration if available
            if not self.index_column and self.current_account:
                self.index_column = self.load_index_column(self.current_account)

            # Default to GL Portal No for API pulls if not configured
            if not self.index_column and "GL Portal No" in df.columns:
                self.index_column = "GL Portal No"

            # Set current job id from GL Portal No (first row) and pre-filter data
            if self.index_column and self.index_column in df.columns and len(df) > 0:
                first_job_id = df.iloc[0][self.index_column]
                if pd.notna(first_job_id) and str(first_job_id).strip():
                    self.current_job_id = str(first_job_id).strip()
                    filtered_df = df[df[self.index_column].astype(str) == self.current_job_id]
                    if not filtered_df.empty:
                        self.filtered_job_data = self.aggregate_job_data(filtered_df)
                        if hasattr(self, "job_id_entry"):
                            self.job_id_entry.delete(0, "end")
                            self.job_id_entry.insert(0, self.current_job_id)
                        if hasattr(self, "filter_status_label"):
                            self.filter_status_label.configure(
                                text=f"✅ Showing job: {self.current_job_id} ({len(filtered_df)} rows aggregated)",
                                text_color="#2ecc71"
                            )
            # Update UI
            self.update_status(f"✅ GLE data pulled for Job ID: {job_id}")
            self.update_data_info()
            
            # Load and display data with default columns if not already configured
            if not self.visible_columns:
                # Auto-select first 5 columns as default
                self.visible_columns = list(self.current_data.columns[:5])
            
            self.update_data_display()
            
            # Enable configure columns button
            if hasattr(self, 'config_columns_btn'):
                self.config_columns_btn.configure(state="normal")

            messagebox.showinfo(
                "Success",
                f"Data pulled successfully!\n\nJob ID: {job_id}\nRows: {len(df)}\nColumns: {len(df.columns)}\n\nUse 'Configure Columns' to select which data to display."
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to pull GLE data:\n{str(e)}")
            self.update_status("❌ Failed to pull GLE data")


    

    def refresh_ui(self):
        """Refresh UI components"""
        self.update_data_info()
        self.update_account_info()
        self.update_status(f"UI refreshed - Account: {self.current_account or 'None'}")
    
    def update_account_info(self):
        """Update account info label"""
        if hasattr(self, 'account_info_label'):
            if self.current_account:
                self.account_info_label.configure(
                    text=self.current_account,
                    text_color="#4caf50"
                )
                if hasattr(self, 'account_frame'):
                    self.account_frame.configure(fg_color="#2e7d32")
            else:
                self.account_info_label.configure(
                    text="None Selected",
                    text_color="#ffeb3b"
                )
                if hasattr(self, 'account_frame'):
                    self.account_frame.configure(fg_color="#1f538d")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About One Stop Shop",
            "One Stop Shop v1.0\n\n"
            "Central hub for:\n"
            "• Job data import\n"
            "• GLE API integration\n"
            "• Entity/Workflow/Service configuration\n"
            "• PA template generation\n\n"
            "© 2025 BP TECH"
        )
    
    def setup_ui(self):
        """Setup the user interface"""
        
        # Create main container
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True)
        
        # TOP BANNER - Account Selection, GLE API, Import Data
        self.create_top_banner(main_container)
        
        # Main content frame with tabbed interface
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Account-gated tabbed interface (tabs will fill entire content area)
        self.create_tabbed_interface(content_frame)
        
        # Status bar
        self.status_label = ctk.CTkLabel(
            main_container,
            text="Ready",
            font=("Arial", 11),
            text_color="gray"
        )
        self.status_label.pack(pady=5)
    
    def create_top_banner(self, parent):
        """Create top banner with account selection, GLE API, and import data"""
        banner_frame = ctk.CTkFrame(parent, fg_color="#1f538d", corner_radius=10, height=80)
        banner_frame.pack(fill="x", padx=20, pady=(15, 20))
        banner_frame.pack_propagate(False)
        
        # Left section - Account info
        left_section = ctk.CTkFrame(banner_frame, fg_color="transparent")
        left_section.pack(side="left", fill="y", padx=(20, 15), pady=10)
        
        
        account_row = ctk.CTkFrame(left_section, fg_color="transparent")
        account_row.pack(fill="x", pady=(5, 0))
        
        self.account_info_label = ctk.CTkLabel(
            account_row,
            text="None Selected",
            font=("Arial", 13, "bold"),
            text_color="#ffeb3b"
        )
        self.account_info_label.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            account_row,
            text="Choose Account",
            command=self.select_account,
            width=120,
            height=28,
            font=("Arial", 10),
            fg_color="#2b7dbc",
            hover_color="#1f538d"
        ).pack(side="left")
        
        # Center section - GLE API Pull
        center_section = ctk.CTkFrame(banner_frame, fg_color="transparent")
        center_section.pack(side="left", fill="y", padx=15, pady=10)
        
        
        gle_row = ctk.CTkFrame(center_section, fg_color="transparent")
        gle_row.pack(fill="x", pady=(5, 0))
        
        self.gle_entry = ctk.CTkEntry(
            gle_row,
            placeholder_text="Enter GLE JOB ID...",
            width=200,
            height=28,
            font=("Arial", 10)
        )
        self.gle_entry.pack(side="left", padx=(0, 8))
        self.gle_entry.bind("<Return>", lambda e: self.pull_gle_data_from_entry())

        ctk.CTkButton(
            gle_row,
            text="Pull GLE Data",
            command=self.pull_gle_data_from_entry,
            width=80,
            height=28,
            font=("Arial", 10),
            fg_color="#27ae60",
            hover_color="#229954"
        ).pack(side="left", padx=(0, 5))
        
        
        # Right section - Import Job Data
        right_section = ctk.CTkFrame(banner_frame, fg_color="transparent")
        right_section.pack(side="right", fill="y", padx=(15, 20), pady=10)
        
        
        import_row = ctk.CTkFrame(right_section, fg_color="transparent")
        import_row.pack(fill="x", pady=(5, 0))
        
        ctk.CTkButton(
            import_row,
            text="Import Job Data",
            command=self.browse_file,
            width=150,
            height=28,
            font=("Arial", 13, "bold"),
            fg_color="#e74c3c",
            hover_color="#c0392b"
        ).pack()
    
    def create_tabbed_interface(self, parent):
        """Create account-gated tabbed interface"""
        # Container for tabs - only shows when account is selected
        self.tabs_container = ctk.CTkFrame(parent, fg_color="transparent")
        self.tabs_container.pack(fill="both", expand=True)
        
        # Account selection prompt (shows when no account selected)
        self.account_prompt = ctk.CTkFrame(self.tabs_container, fg_color="#34495e", corner_radius=15)
        self.account_prompt.pack(fill="both", expand=True, padx=50, pady=50)
        
        prompt_content = ctk.CTkFrame(self.account_prompt, fg_color="transparent")
        prompt_content.pack(expand=True, pady=80)
        
        ctk.CTkLabel(
            prompt_content,
            text="🏢",
            font=("Arial", 48)
        ).pack(pady=(0, 20))
        
        ctk.CTkLabel(
            prompt_content,
            text="Please select an account to continue",
            font=("Arial", 18, "bold"),
            text_color="white"
        ).pack(pady=(0, 10))
        
        ctk.CTkLabel(
            prompt_content,
            text="Use the 'Choose Account' button in the banner above",
            font=("Arial", 12),
            text_color="#95a5a6"
        ).pack(pady=(0, 20))
        
        ctk.CTkButton(
            prompt_content,
            text="Choose Account",
            command=self.select_account,
            width=200,
            height=40,
            font=("Arial", 14, "bold"),
            fg_color="#3498db",
            hover_color="#2980b9"
        ).pack()
        
        # Tabbed interface (initially hidden)
        self.main_tabs = ctk.CTkTabview(self.tabs_container)
        self.main_tabs.pack(fill="both", expand=True)
        
        # Create tabs - Data View first, then QuoteMe, PA Integration, Rate Cards, and Configuration
        self.setup_data_view_tab()
        self.setup_quoteme_parser_tab()
        self.setup_pa_integration_tab()
        self.setup_rate_cards_tab()
        self.setup_configuration_tab()
        
        # Initially hide tabs until account is selected
        if not self.current_account:
            self.main_tabs.pack_forget()
    
    def setup_data_view_tab(self):
        """Setup Job Data tab - split layout with data preview (25%) and workflow services (75%)"""
        data_tab = self.main_tabs.add("Job Data")
        
        # Main container with grid layout - now resizable
        main_container = ctk.CTkFrame(data_tab, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Configure grid columns with initial split (1:3) - left gets 25%, right gets 75%
        main_container.grid_columnconfigure(0, weight=1, minsize=200)  # Min 200px for left pane
        main_container.grid_columnconfigure(2, weight=3, minsize=300)  # Min 300px for right pane
        main_container.grid_rowconfigure(0, weight=1)
        
        # Store references for resizing
        self._pane_weights = [1, 3]  # Track column weights for resizing
        
        # ─── LEFT PANE: Data Preview (25%) ───────────────────────────────────────
        left_pane = ctk.CTkFrame(main_container, fg_color="transparent")
        left_pane.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Header for left pane
        left_header = ctk.CTkFrame(left_pane, fg_color="transparent")
        left_header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            left_header,
            text="📊 Job Data Preview",
            font=("Arial", 16, "bold")
        ).pack(side="left", pady=(0, 10))
        
        # Data info label
        self.data_info_label = ctk.CTkLabel(
            left_header,
            text="No data loaded",
            font=("Arial", 10),
            text_color="gray"
        )
        self.data_info_label.pack(side="left", padx=15)
        
        # Configure Columns button
        self.config_columns_btn = ctk.CTkButton(
            left_header,
            text="⚙️ Configure Columns",
            command=self.configure_visible_columns,
            width=160,
            height=30,
            font=("Arial", 10, "bold"),
            fg_color="#9b59b6",
            hover_color="#8e44ad",
            state="disabled"
        )
        self.config_columns_btn.pack(side="right")
        
        # Data display scrollable area
        self.data_display_scroll = ctk.CTkScrollableFrame(left_pane, fg_color="transparent")
        self.data_display_scroll.pack(fill="both", expand=True)
        
        # Initial message
        self.no_data_label = ctk.CTkLabel(
            self.data_display_scroll,
            text="No data loaded\n\nPull data from GLE API or import job data using the buttons in the banner above",
            font=("Arial", 12),
            text_color="gray"
        )
        self.no_data_label.pack(expand=True, pady=50)
        
        # ─── RESIZABLE SEPARATOR ───────────────────────────────────────
        separator = ctk.CTkFrame(main_container, fg_color="gray40", width=3)
        separator.grid(row=0, column=1, sticky="ns", padx=0)
        
        # Make separator draggable for resizing
        def on_separator_drag(event):
            """Handle dragging the separator to resize panes"""
            # Calculate new weights based on mouse position
            total_width = main_container.winfo_width()
            left_width = event.x
            
            # Update column weights to maintain aspect ratio
            if left_width > 200 and (total_width - left_width) > 300:  # Respect minimums
                new_left_weight = max(1, left_width // 50)
                new_right_weight = max(1, (total_width - left_width) // 50)
                main_container.grid_columnconfigure(0, weight=new_left_weight)
                main_container.grid_columnconfigure(2, weight=new_right_weight)
        
        separator.bind("<B1-Motion>", on_separator_drag)
        separator.configure(cursor="sb_h_double_arrow")
        
        # ─── RIGHT PANE: Workflow Services (75%) ────────────────────────────────────
        right_pane = ctk.CTkFrame(main_container, fg_color="gray20", corner_radius=10)
        right_pane.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        right_pane.grid_columnconfigure(0, weight=1)
        right_pane.grid_rowconfigure(4, weight=1)  # Services table gets remaining space
        
        # Right pane header
        right_header = ctk.CTkFrame(right_pane, fg_color="transparent")
        right_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 10))
        
        header_left = ctk.CTkFrame(right_header, fg_color="transparent")
        header_left.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            header_left,
            text="⚙️ Workflow Configuration",
            font=("Arial", 14, "bold")
        ).pack(anchor="w")
        
        ctk.CTkButton(
            right_header,
            text="✏️ Edit Workflows",
            command=self.open_current_account_workflow_editor,
            width=140,
            height=30,
            font=("Arial", 10, "bold"),
            fg_color="#3498db",
            hover_color="#2980b9"
        ).pack(side="right", padx=(5, 0))
        
        # Workflow selector section
        wf_frame = ctk.CTkFrame(right_pane, fg_color="transparent")
        wf_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)
        
        ctk.CTkLabel(
            wf_frame,
            text="Choose Workflow:",
            font=("Arial", 11, "bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.workflow_dropdown = ctk.CTkComboBox(
            wf_frame,
            values=[],
            command=self.on_workflow_selected,
            state="readonly",
            font=("Arial", 11),
            height=32
        )
        self.workflow_dropdown.pack(fill="x")
        
        # Rate card selector section
        rc_frame = ctk.CTkFrame(right_pane, fg_color="transparent")
        rc_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=10)
        
        ctk.CTkLabel(
            rc_frame,
            text="Select Rate Card:",
            font=("Arial", 11, "bold")
        ).pack(anchor="w", pady=(0, 5))
        
        rc_dropdown_frame = ctk.CTkFrame(rc_frame, fg_color="transparent")
        rc_dropdown_frame.pack(fill="x", pady=(0, 5))
        
        self.rate_card_dropdown = ctk.CTkComboBox(
            rc_dropdown_frame,
            values=[],
            command=self.on_rate_card_selected,
            state="readonly",
            font=("Arial", 11),
            height=32
        )
        self.rate_card_dropdown.pack(side="left", fill="x", expand=True)
        
        # Browse button to load rate card files
        ctk.CTkButton(
            rc_dropdown_frame,
            text="📁 Browse",
            command=self.browse_rate_card_file,
            width=80,
            height=32,
            font=("Arial", 10, "bold"),
            fg_color="#27ae60",
            hover_color="#229954"
        ).pack(side="left", padx=(5, 0))
        
        # Rate card info message (inside rc_frame)
        self.rate_card_info = ctk.CTkLabel(
            rc_frame,
            text="ℹ️ No rate card loaded. Select from dropdown or browse for a file.",
            font=("Arial", 9),
            text_color="#f39c12",
            wraplength=350,
            justify="left"
        )
        self.rate_card_info.pack(fill="x", pady=(5, 0))
        
        # Services table section
        table_label = ctk.CTkLabel(
            right_pane,
            text="Services by Language Pair:",
            font=("Arial", 11, "bold")
        )
        table_label.grid(row=3, column=0, sticky="ew", padx=15, pady=(15, 5))
        
        # Create scrollable table frame
        self.services_table_frame = ctk.CTkScrollableFrame(
            right_pane,
            fg_color="gray25",
            corner_radius=5
        )
        self.services_table_frame.grid(row=4, column=0, sticky="nsew", padx=15, pady=(0, 15))
        
        # Initial message for services table
        self.services_empty_label = ctk.CTkLabel(
            self.services_table_frame,
            text="Select a workflow to view services",
            font=("Arial", 10),
            text_color="gray"
        )
        self.services_empty_label.pack(expand=True, pady=20)
        
        # Store references for workflow management
        self.workflow_service_widgets = {}  # Maps service_name to {lp: {quantity_entry, rate_entry}}
    
    def setup_configuration_tab(self):
        """Setup Configuration tab with sub-tabs - all UIs embedded inline"""
        from gui.entity_manager_gui import EntityManagerGUI
        from gui.workflow_manager_gui import WorkflowManagerGUI
        from gui.service_mapping_gui import ServiceMappingWindow

        config_tab = self.main_tabs.add("Configuration")

        # Create sub-tabview for configuration options
        config_subtabs = ctk.CTkTabview(config_tab)
        config_subtabs.pack(fill="both", expand=True)

        # ── 1.1 Manage Entities ──────────────────────────────────────────────
        entities_tab = config_subtabs.add("Manage Entities")
        try:
            EntityManagerGUI(frame=entities_tab)
        except Exception as e:
            ctk.CTkLabel(
                entities_tab,
                text=f"⚠️ Failed to load Entity Manager:\n{str(e)}",
                font=("Arial", 12),
                text_color="#e74c3c"
            ).pack(expand=True, pady=50)

        # ── 1.2 Map Services ─────────────────────────────────────────────────
        services_tab = config_subtabs.add("Map Services")

        # Entity picker header
        picker_frame = ctk.CTkFrame(services_tab, fg_color="#1f538d", height=60)
        picker_frame.pack(fill="x", padx=0, pady=(0, 5))
        picker_frame.pack_propagate(False)

        picker_inner = ctk.CTkFrame(picker_frame, fg_color="transparent")
        picker_inner.pack(expand=True)

        ctk.CTkLabel(
            picker_inner,
            text="Select Entity to Map:",
            font=("Arial", 12, "bold"),
            text_color="white"
        ).pack(side="left", padx=(10, 10), pady=15)

        # Load entity names from WF_Matrix
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / "Core"))
            from WF_Matrix import PA_SERVICES
            entity_names = sorted([e for e in PA_SERVICES.keys() if e != "TPUS"])
        except Exception:
            entity_names = []

        entity_var = ctk.StringVar(value=entity_names[0] if entity_names else "")
        entity_dropdown = ctk.CTkComboBox(
            picker_inner,
            values=entity_names,
            variable=entity_var,
            width=200,
            font=("Arial", 12)
        )
        entity_dropdown.pack(side="left", padx=(0, 10), pady=15)

        # Container for the mapping UI (reloaded when entity changes)
        mapping_container = ctk.CTkFrame(services_tab, fg_color="transparent")
        mapping_container.pack(fill="both", expand=True)

        def load_entity_mapping(*_):
            # Clear previous mapping UI
            for widget in mapping_container.winfo_children():
                widget.destroy()
            entity = entity_var.get()
            if not entity:
                return
            try:
                ServiceMappingWindow(self.root, entity, frame=mapping_container)
            except Exception as e:
                ctk.CTkLabel(
                    mapping_container,
                    text=f"⚠️ Failed to load mapping for '{entity}':\n{str(e)}",
                    font=("Arial", 12),
                    text_color="#e74c3c"
                ).pack(expand=True, pady=30)

        entity_dropdown.configure(command=load_entity_mapping)

        # Load first entity by default
        if entity_names:
            load_entity_mapping()

        # ── 1.3 Configure Workflows ──────────────────────────────────────────
        workflows_tab = config_subtabs.add("Configure Workflows")
        try:
            WorkflowManagerGUI(frame=workflows_tab)
        except Exception as e:
            ctk.CTkLabel(
                workflows_tab,
                text=f"⚠️ Failed to load Workflow Manager:\n{str(e)}",
                font=("Arial", 12),
                text_color="#e74c3c"
            ).pack(expand=True, pady=50)

    def setup_quoteme_parser_tab(self):
        """Setup QuoteMe Email Parser tab - embedded directly in the viewing pane"""
        parser_tab = self.main_tabs.add("QuoteMe Parser")

        def on_parser_apply(lp_code: str, lp_data):
            self.update_status(f"✅ QuoteMe parsed: {lp_code}")

        def on_parser_complete(parse_result):
            """Callback when parsing completes - update Job Data tab"""
            if parse_result and parse_result.success and parse_result.language_pairs:
                try:
                    self.set_language_pairs_from_quoteme(parse_result.language_pairs)
                    self.update_status(f"✅ Job Data updated with {len(parse_result.language_pairs)} language pair(s)")
                except Exception as e:
                    print(f"Error updating Job Data with parsed language pairs: {e}")

        try:
            create_parser_tab(parser_tab, on_apply_callback=on_parser_apply, on_parse_complete_callback=on_parser_complete)
        except Exception as e:
            ctk.CTkLabel(
                parser_tab,
                text=f"⚠️ Failed to load QuoteMe Parser:\n{str(e)}",
                font=("Arial", 12),
                text_color="#e74c3c"
            ).pack(expand=True, pady=60)

    def setup_pa_integration_tab(self):
        """Setup PA Integration tab with embedded sub-tabs"""
        pa_tab = self.main_tabs.add("PA Integration")

        pa_subtabs = ctk.CTkTabview(pa_tab)
        pa_subtabs.pack(fill="both", expand=True)

        # ── Sub-tab 1: Configure Template (default) ───────────────────────────
        mapper_tab = pa_subtabs.add("Configure Template")

        # Placeholder shown until account is selected
        self.pa_mapper_container = ctk.CTkFrame(mapper_tab, fg_color="transparent")
        self.pa_mapper_container.pack(fill="both", expand=True)

        self._pa_mapper_placeholder = ctk.CTkLabel(
            self.pa_mapper_container,
            text="Select an account to load the Template Mapper",
            font=("Arial", 13),
            text_color="gray"
        )
        self._pa_mapper_placeholder.pack(expand=True, pady=60)

        # ── Sub-tab 2: Data Preview ───────────────────────────────────────────
        preview_tab = pa_subtabs.add("Data Preview")

        preview_outer = ctk.CTkFrame(preview_tab, fg_color="transparent")
        preview_outer.pack(fill="both", expand=True, padx=15, pady=10)

        # Run preview button
        preview_btn_row = ctk.CTkFrame(preview_outer, fg_color="#2c3e50", corner_radius=8)
        preview_btn_row.pack(fill="x", pady=(0, 10))

        preview_btn_inner = ctk.CTkFrame(preview_btn_row, fg_color="transparent")
        preview_btn_inner.pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(
            preview_btn_inner,
            text="👁️ Data Preview",
            font=("Arial", 14, "bold"),
            text_color="white"
        ).pack(side="left", padx=(0, 20))

        self.pa_preview_status = ctk.CTkLabel(
            preview_btn_inner,
            text="",
            font=("Arial", 11),
            text_color="#3498db"
        )
        self.pa_preview_status.pack(side="left", padx=(0, 15))

        ctk.CTkButton(
            preview_btn_inner,
            text="▶ Run Preview",
            command=self._run_inline_preview,
            width=140,
            height=32,
            font=("Arial", 11, "bold"),
            fg_color="#2ecc71",
            hover_color="#27ae60"
        ).pack(side="right")

        # Scrollable results area
        self.pa_preview_scroll = ctk.CTkScrollableFrame(preview_outer, fg_color="#1e1e1e", corner_radius=8)
        self.pa_preview_scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.pa_preview_scroll,
            text="Click 'Run Preview' to generate a preview of PA integration data.",
            font=("Arial", 12),
            text_color="gray"
        ).pack(expand=True, pady=40)

        # ── Sub-tab 3: Generate Worksheets ────────────────────────────────────
        generate_tab = pa_subtabs.add("Generate Worksheets")

        gen_outer = ctk.CTkFrame(generate_tab, fg_color="transparent")
        gen_outer.pack(fill="both", expand=True, padx=15, pady=10)

        # Info card
        info_card = ctk.CTkFrame(gen_outer, fg_color="#2c3e50", corner_radius=8)
        info_card.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            info_card,
            text="✨ Generate PA Integration Worksheets",
            font=("Arial", 16, "bold"),
            text_color="white"
        ).pack(pady=(15, 5), padx=20, anchor="w")

        ctk.CTkLabel(
            info_card,
            text="Generates a multi-sheet Excel file with one worksheet per Sub_ID,\n"
                 "ready for import into ProjectA.",
            font=("Arial", 11),
            text_color="#95a5a6",
            justify="left"
        ).pack(pady=(0, 15), padx=20, anchor="w")

        # Generate button
        gen_btn_frame = ctk.CTkFrame(gen_outer, fg_color="#e74c3c", corner_radius=10)
        gen_btn_frame.pack(fill="x", pady=(0, 15))

        gen_inner = ctk.CTkFrame(gen_btn_frame, fg_color="transparent")
        gen_inner.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(
            gen_inner,
            text="✨ Generate PA Integration",
            command=self.generate_pa_worksheets,
            width=280,
            height=55,
            font=("Arial", 15, "bold"),
            fg_color="#c0392b",
            hover_color="#a93226"
        ).pack(side="left")

        self.pa_generate_status = ctk.CTkLabel(
            gen_inner,
            text="",
            font=("Arial", 11),
            text_color="#2ecc71"
        )
        self.pa_generate_status.pack(side="left", padx=20)

        # Last generated file info
        self.pa_last_file_label = ctk.CTkLabel(
            gen_outer,
            text="No file generated yet",
            font=("Arial", 10),
            text_color="gray"
        )
        self.pa_last_file_label.pack(anchor="w", pady=(5, 0))

    def setup_rate_cards_tab(self):
        """Setup Rate Cards tab - embedded Rate Card Builder component"""
        rate_cards_tab = self.main_tabs.add("Rate Cards")
        
        if setup_rate_cards_tab is None:
            # Show error if Rate Card Builder is not available
            ctk.CTkLabel(
                rate_cards_tab,
                text="⚠️ Rate Card Builder not available\n\nThe Rate_Card_Builder module could not be imported.",
                font=("Arial", 12),
                text_color="#e74c3c"
            ).pack(expand=True, pady=60)
            return
        
        try:
            # Setup the Rate Card Builder component
            self.rate_card_builder = setup_rate_cards_tab(rate_cards_tab, self.root)
        except Exception as e:
            ctk.CTkLabel(
                rate_cards_tab,
                text=f"⚠️ Failed to load Rate Cards:\n{str(e)}",
                font=("Arial", 12),
                text_color="#e74c3c"
            ).pack(expand=True, pady=60)
            print(f"Error setting up Rate Cards tab: {e}")

    # ──────────────────── Workflow & Rate Card Management ────────────────────
    
    def get_available_workflows(self) -> list:
        """Get workflows for current account"""
        if not self.current_account:
            return []
        workflows = self.account_workflow_manager.get_workflows(self.current_account)
        return list(workflows.keys()) if workflows else []
    
    def get_available_rate_cards(self) -> list:
        """Get list of available rate card files and master rate cards"""
        try:
            available = []
            
            # Get file-based rate cards
            rate_card_path = Path(__file__).parent.parent / "Rate_Card_Builder"
            rate_card_files = list(rate_card_path.glob("rate_cards_*.json"))
            available.extend(sorted([f.stem.replace("rate_cards_", "") for f in rate_card_files]))
            
            # Get master rate cards
            master_data = self.load_master_rate_cards()
            master_names = list(master_data.get("rate_cards", {}).keys())
            # Prefix master cards with [Master] for clarity
            available.extend(sorted([f"[Master] {name}" for name in master_names]))
            
            return available
        except Exception as e:
            print(f"Error loading rate cards: {e}")
            return []
    
    def load_rate_card(self, rate_card_name: str) -> dict:
        """Load a rate card JSON file or from master rate cards"""
        try:
            print(f"\n=== DEBUG: Loading Rate Card ===")
            print(f"Rate Card Name: {rate_card_name}")
            
            # Check if loading from master rate cards
            if rate_card_name.startswith("[Master] "):
                # Load from master rate cards
                master_name = rate_card_name.replace("[Master] ", "")
                master_data = self.load_master_rate_cards()
                if master_name in master_data.get("rate_cards", {}):
                    print(f"Loading from master: {master_name}")
                    return master_data["rate_cards"][master_name]
                else:
                    print(f"Master rate card not found: {master_name}")
                    return {}
            else:
                # Load from file
                rate_card_path = Path(__file__).parent.parent / "Rate_Card_Builder" / f"rate_cards_{rate_card_name}.json"
                
                print(f"Looking for file: {rate_card_path}")
                print(f"File exists: {rate_card_path.exists()}")
                
                if rate_card_path.exists():
                    with open(rate_card_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    print(f"Successfully loaded from: {rate_card_path}")
                    return data
                else:
                    print(f"File not found at: {rate_card_path}")
                    # List what files are available
                    rate_card_dir = rate_card_path.parent
                    if rate_card_dir.exists():
                        available_files = list(rate_card_dir.glob("rate_cards_*.json"))
                        print(f"Available rate card files: {[f.name for f in available_files]}")
                return {}
        except Exception as e:
            print(f"Error loading rate card {rate_card_name}: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def get_rate_from_card(self, rate_card: dict, service: str, target_language: str = None) -> str:
        """
        Get rate for a service from a loaded rate card
        
        Args:
            rate_card: Loaded rate card data
            service: Service name
            target_language: Target language from language pair (e.g., "Polish (Poland)" or "Polish")
            
        Returns:
            Rate as string or empty string if not found
        """
        if not rate_card or "languages" not in rate_card:
            return ""
        
        if not target_language:
            return ""
        
        # Normalize the target language using language normalizer
        iso_code, lang_name, display_name = self.language_normalizer.normalize(target_language)
        
        # Try to find the language in the rate card
        languages_dict = rate_card.get("languages", {})
        
        # Build list of potential language key matches to try in order
        potential_keys = []
        
        # Add normalized variants
        if display_name:
            potential_keys.append(display_name)
        if lang_name:
            potential_keys.append(lang_name)
        potential_keys.append(target_language)
        
        # Add fuzzy matches for common language variants (e.g., Traditional Chinese with typos)
        if "Taiwan" in target_language or "Tawain" in target_language:
            potential_keys.extend([
                "Traditional Chinese (Taiwan)",
                "Traditional Chinese (Tawain)",  # Handle typo in rate card
                "Traditional Chinese",
                "Chinese (Taiwan)",
                "Chinese (Tawain)"
            ])
        
        # Try each potential key
        matched_lang = None
        for potential_key in potential_keys:
            # Exact match (case-insensitive)
            for lang_key in languages_dict.keys():
                if lang_key.lower() == potential_key.lower():
                    matched_lang = lang_key
                    break
            if matched_lang:
                break
        
        # If still no match, try partial/fuzzy matching
        if not matched_lang:
            for lang_key, lang_data in languages_dict.items():
                # Partial match - if lang_key starts with any of our potential keys
                for potential_key in potential_keys:
                    if lang_key.lower().startswith(potential_key.lower()):
                        matched_lang = lang_key
                        break
                if matched_lang:
                    break
        
        # Try reverse match - if potential key contains the language key
        if not matched_lang:
            for lang_key in languages_dict.keys():
                if lang_key.lower() in target_language.lower():
                    matched_lang = lang_key
                    break
        
        if matched_lang:
            lang_data = languages_dict[matched_lang]
            if isinstance(lang_data, dict) and "rates" in lang_data:
                rates = lang_data["rates"]
                
                # Try exact service match first
                if service in rates:
                    rate = rates[service]
                    return str(rate) if rate else ""
                
                # Try case-insensitive match
                for rate_service, rate_value in rates.items():
                    if rate_service.lower() == service.lower():
                        return str(rate_value) if rate_value else ""
                
                # Debug: print available services for this language
                print(f"DEBUG: Language '{matched_lang}' found for target '{target_language}'")
                print(f"  Services available: {list(rates.keys())}")
                print(f"  Looking for service: '{service}'")
        
        return ""
    
    def refresh_workflow_dropdown(self):
        """Refresh workflow dropdown for current account"""
        workflows = self.get_available_workflows()
        self.workflow_dropdown.configure(values=workflows)
        if workflows:
            self.workflow_dropdown.set(workflows[0])
            self.on_workflow_selected(workflows[0])
        else:
            self.workflow_dropdown.set("")
            self.services_empty_label.pack(expand=True, pady=20)
    
    def refresh_rate_card_dropdown(self):
        """Refresh rate card dropdown - allows user to choose"""
        rate_cards = self.get_available_rate_cards()
        self.rate_card_dropdown.configure(values=rate_cards)
        # Don't auto-select; let user choose manually or use Browse button
        self.rate_card_dropdown.set("")
        self.selected_rate_card = None
        self.rate_card_info.configure(text="ℹ️ No rate card loaded. Select from dropdown or browse for a file.")
    
    def open_current_account_workflow_editor(self):
        """Open simplified workflow editor for current account only"""
        if not self.current_account:
            messagebox.showwarning("No Account", "Please select an account first")
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Edit Workflows - {self.current_account}")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f'600x500+{x}+{y}')
        
        # Header
        header = ctk.CTkFrame(dialog, fg_color="transparent")
        header.pack(pady=15, padx=15, fill="x")
        
        ctk.CTkLabel(
            header,
            text=f"Workflows for {self.current_account}",
            font=("Arial", 14, "bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header,
            text="Create, edit, or delete workflows. Select services for each workflow.",
            font=("Arial", 9),
            text_color="gray"
        ).pack(anchor="w", pady=(5, 0))
        
        # Main content frame with scrollable workflows list
        content_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Workflows list label and button frame
        list_header = ctk.CTkFrame(content_frame, fg_color="transparent")
        list_header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            list_header,
            text="Workflows:",
            font=("Arial", 11, "bold")
        ).pack(anchor="w", side="left")
        
        ctk.CTkButton(
            list_header,
            text="➕ Add New",
            command=lambda: self._add_workflow_dialog(dialog),
            width=100,
            height=28,
            font=("Arial", 9, "bold"),
            fg_color="green"
        ).pack(anchor="e", side="right")
        
        # Scrollable workflows list
        workflows_scroll = ctk.CTkScrollableFrame(
            content_frame,
            fg_color="gray25",
            corner_radius=8
        )
        workflows_scroll.pack(fill="both", expand=True, pady=(0, 10))
        
        # Bind mouse wheel to scrollable frame
        def on_mousewheel(event):
            workflows_scroll._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        workflows_scroll.bind("<MouseWheel>", on_mousewheel)
        
        # Get workflows for current account
        workflows = self.account_workflow_manager.get_workflows(self.current_account)
        
        if not workflows:
            ctk.CTkLabel(
                workflows_scroll,
                text="No workflows yet. Create one with the button above.",
                text_color="orange"
            ).pack(pady=20)
        else:
            for workflow_name in workflows:
                wf_frame = ctk.CTkFrame(workflows_scroll, fg_color="gray20", corner_radius=6)
                wf_frame.pack(fill="x", pady=5, padx=5)
                
                wf_info_frame = ctk.CTkFrame(wf_frame, fg_color="transparent")
                wf_info_frame.pack(fill="both", expand=True, padx=10, pady=8)
                
                # Workflow name and service count
                services = self.account_workflow_manager.get_workflow_services(
                    self.current_account,
                    workflow_name
                )
                
                ctk.CTkLabel(
                    wf_info_frame,
                    text=f"📋 {workflow_name}",
                    font=("Arial", 11, "bold")
                ).pack(anchor="w")
                
                ctk.CTkLabel(
                    wf_info_frame,
                    text=f"Services: {', '.join(services) if services else 'None'}",
                    font=("Arial", 9),
                    text_color="gray",
                    wraplength=400,
                    justify="left"
                ).pack(anchor="w", pady=(3, 0))
                
                # Edit and Delete buttons
                btn_frame = ctk.CTkFrame(wf_frame, fg_color="transparent")
                btn_frame.pack(fill="x", padx=10, pady=(0, 8))
                
                ctk.CTkButton(
                    btn_frame,
                    text="✏️ Edit",
                    command=lambda wf=workflow_name: self._edit_workflow_dialog(dialog, wf),
                    width=80,
                    height=26,
                    font=("Arial", 9),
                    fg_color="#3498db"
                ).pack(side="left", padx=(0, 5))
                
                ctk.CTkButton(
                    btn_frame,
                    text="🗑️ Delete",
                    command=lambda wf=workflow_name: self._delete_workflow(dialog, wf),
                    width=80,
                    height=26,
                    font=("Arial", 9),
                    fg_color="#e74c3c"
                ).pack(side="left")
        
        # Bottom buttons
        btn_footer = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_footer.pack(pady=15, padx=15, fill="x")
        
        ctk.CTkButton(
            btn_footer,
            text="Close",
            command=dialog.destroy,
            width=150,
            height=32,
            font=("Arial", 11, "bold")
        ).pack()
    
    def _add_workflow_dialog(self, parent_dialog):
        """Dialog to add new workflow for current account"""
        add_dialog = ctk.CTkToplevel(parent_dialog)
        add_dialog.title("Add Workflow")
        add_dialog.geometry("600x500")
        add_dialog.transient(parent_dialog)
        add_dialog.grab_set()
        
        # Center on parent
        add_dialog.update_idletasks()
        x = (add_dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (add_dialog.winfo_screenheight() // 2) - (500 // 2)
        add_dialog.geometry(f'600x500+{x}+{y}')
        
        # Workflow name
        ctk.CTkLabel(add_dialog, text="Workflow Name:", font=("Arial", 11, "bold")).pack(pady=(15, 5), padx=15, anchor="w")
        name_entry = ctk.CTkEntry(add_dialog, width=400, font=("Arial", 11))
        name_entry.pack(padx=15, pady=(0, 15))
        
        # Main content frame with two columns
        content = ctk.CTkFrame(add_dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # LEFT: Available services with search
        left_frame = ctk.CTkFrame(content, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(left_frame, text="Available Services:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        # Search entry for filtering
        search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            left_frame,
            textvariable=search_var,
            placeholder_text="🔍 Search services...",
            font=("Arial", 9),
            height=28
        )
        search_entry.pack(fill="x", pady=(0, 8))
        search_entry.focus()
        
        services_scroll = ctk.CTkScrollableFrame(left_frame, fg_color="gray25", corner_radius=6)
        services_scroll.pack(fill="both", expand=True)
        
        def on_mousewheel(event):
            services_scroll._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        services_scroll.bind("<MouseWheel>", on_mousewheel)
        
        # Get canonical services
        canonical_services = self.service_mapper.canonical_services
        selected_services_list = []  # Track order
        service_widgets = {}
        service_frames = {}  # Track frames for visibility toggling
        
        def on_search_change(*args):
            """Filter services based on search query"""
            query = search_var.get().lower().strip()
            
            for service, frame in service_frames.items():
                if query == "":
                    # Show all if search is empty
                    frame.pack(anchor="w", padx=10, pady=2, fill="x")
                elif query in service.lower():
                    # Show if service name contains query
                    frame.pack(anchor="w", padx=10, pady=2, fill="x")
                else:
                    # Hide if doesn't match
                    frame.pack_forget()
        
        search_var.trace("w", on_search_change)
        
        def on_service_selected(service_name, cb_var):
            """Handle service checkbox - add/remove from selected list"""
            if cb_var.get():
                selected_services_list.append(service_name)
                update_selected_list()
            else:
                if service_name in selected_services_list:
                    selected_services_list.remove(service_name)
                update_selected_list()
        
        # Create checkboxes for all canonical services
        for service in canonical_services:
            var = ctk.BooleanVar(value=False)
            
            def make_callback(svc, v):
                return lambda: on_service_selected(svc, v)
            
            cb_frame = ctk.CTkFrame(services_scroll, fg_color="transparent")
            cb_frame.pack(anchor="w", padx=10, pady=2, fill="x")
            service_frames[service] = cb_frame  # Store frame for search filtering
            
            cb = ctk.CTkCheckBox(
                cb_frame,
                text=service,
                variable=var,
                command=make_callback(service, var),
                font=("Arial", 9)
            )
            cb.pack(anchor="w", side="left")
            service_widgets[service] = (cb, var)
        
        # RIGHT: Selected services (ordered)
        right_frame = ctk.CTkFrame(content, fg_color="transparent")
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        ctk.CTkLabel(right_frame, text="Selected (Order):", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        selected_scroll = ctk.CTkScrollableFrame(right_frame, fg_color="gray25", corner_radius=6)
        selected_scroll.pack(fill="both", expand=True)
        selected_scroll.bind("<MouseWheel>", on_mousewheel)
        
        selected_widgets = []
        drag_data = {"source_idx": None, "source_widget": None, "dragging": False}
        
        def update_selected_list():
            """Refresh the selected services list with drag-and-drop support"""
            for widget in selected_widgets:
                widget.destroy()
            selected_widgets.clear()
            
            for idx, service in enumerate(selected_services_list):
                # Container frame for the service item
                item_frame = ctk.CTkFrame(selected_scroll, fg_color="gray20", corner_radius=4, height=40)
                item_frame.pack(fill="x", padx=5, pady=3)
                item_frame.pack_propagate(False)
                selected_widgets.append(item_frame)
                
                # Inner content frame
                content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
                content_frame.pack(fill="both", expand=True, padx=2, pady=2)
                
                # Drag handle
                drag_handle = ctk.CTkLabel(
                    content_frame,
                    text="⋮⋮",
                    font=("Arial", 12, "bold"),
                    text_color="#666",
                    width=30
                )
                drag_handle.pack(side="left", padx=(4, 8), pady=5)
                
                # Service label
                service_label = ctk.CTkLabel(
                    content_frame,
                    text=f"{idx + 1}. {service}",
                    font=("Arial", 10),
                    justify="left"
                )
                service_label.pack(side="left", fill="x", expand=True, pady=5)
                
                # Create closure for this index
                def make_drag_handlers(current_idx, frame, handle):
                    def on_press(event):
                        drag_data["source_idx"] = current_idx
                        drag_data["source_widget"] = frame
                        drag_data["dragging"] = True
                        frame.configure(fg_color="#3498db")
                        handle.configure(text_color="#ffffff")
                        # Bind motion to root window for global tracking
                        add_dialog.bind("<Motion>", on_motion)
                    
                    def on_motion(event):
                        if not drag_data["dragging"] or drag_data["source_idx"] is None:
                            return
                        
                        # Find which service we're hovering over
                        y_pos = event.y
                        for check_idx, check_widget in enumerate(selected_widgets):
                            widget_y = check_widget.winfo_y()
                            widget_height = check_widget.winfo_height()
                            if widget_y <= y_pos <= widget_y + widget_height:
                                if check_idx != drag_data["source_idx"]:
                                    check_widget.configure(fg_color="#2ecc71")
                                else:
                                    check_widget.configure(fg_color="#3498db")
                            elif check_widget != drag_data["source_widget"]:
                                check_widget.configure(fg_color="gray20")
                    
                    def on_release(event):
                        if not drag_data["dragging"] or drag_data["source_idx"] is None:
                            return
                        
                        drag_data["dragging"] = False
                        # Find target index
                        y_pos = event.y
                        target_idx = drag_data["source_idx"]
                        for check_idx, check_widget in enumerate(selected_widgets):
                            widget_y = check_widget.winfo_y()
                            widget_height = check_widget.winfo_height()
                            if widget_y <= y_pos <= widget_y + widget_height:
                                target_idx = check_idx
                                break
                        
                        # Perform swap if different positions
                        if target_idx != drag_data["source_idx"]:
                            src = drag_data["source_idx"]
                            # Swap items in the list
                            selected_services_list[src], selected_services_list[target_idx] = (
                                selected_services_list[target_idx], 
                                selected_services_list[src]
                            )
                        
                        # Reset drag state
                        drag_data["source_idx"] = None
                        drag_data["source_widget"] = None
                        add_dialog.unbind("<Motion>")
                        
                        # Refresh display
                        update_selected_list()
                    
                    return on_press, on_release
                
                on_press_fn, on_release_fn = make_drag_handlers(idx, item_frame, drag_handle)
                
                # Bind to multiple elements for better drag capture
                for element in [item_frame, content_frame, drag_handle, service_label]:
                    element.bind("<Button-1>", on_press_fn)
                    element.bind("<ButtonRelease-1>", on_release_fn)
                
                # Controls on the right
                ctrl_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
                ctrl_frame.pack(side="right", padx=5, pady=2)
                
                # Remove button
                def make_remove_cmd(service_name):
                    def remove_service():
                        selected_services_list.remove(service_name)
                        service_widgets[service_name][1].set(False)
                        update_selected_list()
                    return remove_service
                
                ctk.CTkButton(
                    ctrl_frame,
                    text="✕",
                    command=make_remove_cmd(service),
                    width=24,
                    height=24,
                    font=("Arial", 10),
                    fg_color="#e74c3c"
                ).pack(side="left", padx=2)
        
        # Initial population of selected list
        update_selected_list()
        
        # Buttons
        btn_frame = ctk.CTkFrame(add_dialog, fg_color="transparent")
        btn_frame.pack(pady=15, padx=15)
        
        def save_workflow():
            wf_name = name_entry.get().strip()
            if not wf_name:
                messagebox.showwarning("Invalid", "Workflow name cannot be empty")
                return
            
            if not selected_services_list:
                messagebox.showwarning("Invalid", "Select at least one service")
                return
            
            if self.account_workflow_manager.create_workflow(
                self.current_account,
                wf_name,
                selected_services_list  # Preserves order
            ):
                add_dialog.destroy()
                messagebox.showinfo("Success", f"Workflow '{wf_name}' created successfully")
                # Refresh parent dialog
                parent_dialog.destroy()
                self.open_current_account_workflow_editor()
                self.refresh_workflow_dropdown()
            else:
                messagebox.showerror("Error", f"Workflow '{wf_name}' already exists")
        
        ctk.CTkButton(
            btn_frame,
            text="Create",
            command=save_workflow,
            width=120,
            height=32,
            font=("Arial", 11, "bold"),
            fg_color="green"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=add_dialog.destroy,
            width=120,
            height=32,
            font=("Arial", 11),
            fg_color="gray"
        ).pack(side="left", padx=5)
    
    def _edit_workflow_dialog(self, parent_dialog, workflow_name):
        """Dialog to edit existing workflow for current account"""
        edit_dialog = ctk.CTkToplevel(parent_dialog)
        edit_dialog.title(f"Edit Workflow: {workflow_name}")
        edit_dialog.geometry("600x500")
        edit_dialog.transient(parent_dialog)
        edit_dialog.grab_set()
        
        # Center on parent
        edit_dialog.update_idletasks()
        x = (edit_dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (edit_dialog.winfo_screenheight() // 2) - (500 // 2)
        edit_dialog.geometry(f'600x500+{x}+{y}')
        
        # Title
        ctk.CTkLabel(edit_dialog, text=f"Workflow: {workflow_name}", font=("Arial", 12, "bold")).pack(pady=(15, 15), padx=15)
        
        # Main content frame with two columns
        content = ctk.CTkFrame(edit_dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # LEFT: Available services with search
        left_frame = ctk.CTkFrame(content, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(left_frame, text="Available Services:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        # Search entry for filtering
        search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(
            left_frame,
            textvariable=search_var,
            placeholder_text="🔍 Search services...",
            font=("Arial", 9),
            height=28
        )
        search_entry.pack(fill="x", pady=(0, 8))
        search_entry.focus()
        
        services_scroll = ctk.CTkScrollableFrame(left_frame, fg_color="gray25", corner_radius=6)
        services_scroll.pack(fill="both", expand=True)
        
        def on_mousewheel(event):
            services_scroll._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        services_scroll.bind("<MouseWheel>", on_mousewheel)
        
        # Get current workflow services
        current_services = self.account_workflow_manager.get_workflow_services(
            self.current_account,
            workflow_name
        )
        
        # Get canonical services
        canonical_services = self.service_mapper.canonical_services
        selected_services_list = list(current_services)  # Maintain current order
        service_widgets = {}
        service_frames = {}  # Track frames for visibility toggling
        
        def on_search_change(*args):
            """Filter services based on search query"""
            query = search_var.get().lower().strip()
            
            for service, frame in service_frames.items():
                if query == "":
                    # Show all if search is empty
                    frame.pack(anchor="w", padx=10, pady=2, fill="x")
                elif query in service.lower():
                    # Show if service name contains query
                    frame.pack(anchor="w", padx=10, pady=2, fill="x")
                else:
                    # Hide if doesn't match
                    frame.pack_forget()
        
        search_var.trace("w", on_search_change)
        
        def on_service_selected(service_name, cb_var):
            """Handle service checkbox - add/remove from selected list"""
            if cb_var.get():
                if service_name not in selected_services_list:
                    selected_services_list.append(service_name)
                update_selected_list()
            else:
                if service_name in selected_services_list:
                    selected_services_list.remove(service_name)
                update_selected_list()
        
        # Create checkboxes for all canonical services
        for service in canonical_services:
            var = ctk.BooleanVar(value=service in current_services)
            
            def make_callback(svc, v):
                return lambda: on_service_selected(svc, v)
            
            cb_frame = ctk.CTkFrame(services_scroll, fg_color="transparent")
            cb_frame.pack(anchor="w", padx=10, pady=2, fill="x")
            service_frames[service] = cb_frame  # Store frame for search filtering
            
            cb = ctk.CTkCheckBox(
                cb_frame,
                text=service,
                variable=var,
                command=make_callback(service, var),
                font=("Arial", 9)
            )
            cb.pack(anchor="w", side="left")
            service_widgets[service] = (cb, var)
        
        # RIGHT: Selected services (ordered)
        right_frame = ctk.CTkFrame(content, fg_color="transparent")
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        ctk.CTkLabel(right_frame, text="Selected (Order):", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        selected_scroll = ctk.CTkScrollableFrame(right_frame, fg_color="gray25", corner_radius=6)
        selected_scroll.pack(fill="both", expand=True)
        selected_scroll.bind("<MouseWheel>", on_mousewheel)
        
        selected_widgets = []
        drag_data = {"source_idx": None, "source_widget": None, "dragging": False}
        
        def update_selected_list():
            """Refresh the selected services list with drag-and-drop support"""
            for widget in selected_widgets:
                widget.destroy()
            selected_widgets.clear()
            
            for idx, service in enumerate(selected_services_list):
                # Container frame for the service item
                item_frame = ctk.CTkFrame(selected_scroll, fg_color="gray20", corner_radius=4, height=40)
                item_frame.pack(fill="x", padx=5, pady=3)
                item_frame.pack_propagate(False)
                selected_widgets.append(item_frame)
                
                # Inner content frame
                content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
                content_frame.pack(fill="both", expand=True, padx=2, pady=2)
                
                # Drag handle
                drag_handle = ctk.CTkLabel(
                    content_frame,
                    text="⋮⋮",
                    font=("Arial", 12, "bold"),
                    text_color="#666",
                    width=30
                )
                drag_handle.pack(side="left", padx=(4, 8), pady=5)
                
                # Service label
                service_label = ctk.CTkLabel(
                    content_frame,
                    text=f"{idx + 1}. {service}",
                    font=("Arial", 10),
                    justify="left"
                )
                service_label.pack(side="left", fill="x", expand=True, pady=5)
                
                # Create closure for this index
                def make_drag_handlers(current_idx, frame, handle):
                    def on_press(event):
                        drag_data["source_idx"] = current_idx
                        drag_data["source_widget"] = frame
                        drag_data["dragging"] = True
                        frame.configure(fg_color="#3498db")
                        handle.configure(text_color="#ffffff")
                        # Bind motion to root window for global tracking
                        edit_dialog.bind("<Motion>", on_motion)
                    
                    def on_motion(event):
                        if not drag_data["dragging"] or drag_data["source_idx"] is None:
                            return
                        
                        # Find which service we're hovering over
                        y_pos = event.y
                        for check_idx, check_widget in enumerate(selected_widgets):
                            widget_y = check_widget.winfo_y()
                            widget_height = check_widget.winfo_height()
                            if widget_y <= y_pos <= widget_y + widget_height:
                                if check_idx != drag_data["source_idx"]:
                                    check_widget.configure(fg_color="#2ecc71")
                                else:
                                    check_widget.configure(fg_color="#3498db")
                            elif check_widget != drag_data["source_widget"]:
                                check_widget.configure(fg_color="gray20")
                    
                    def on_release(event):
                        if not drag_data["dragging"] or drag_data["source_idx"] is None:
                            return
                        
                        drag_data["dragging"] = False
                        # Find target index
                        y_pos = event.y
                        target_idx = drag_data["source_idx"]
                        for check_idx, check_widget in enumerate(selected_widgets):
                            widget_y = check_widget.winfo_y()
                            widget_height = check_widget.winfo_height()
                            if widget_y <= y_pos <= widget_y + widget_height:
                                target_idx = check_idx
                                break
                        
                        # Perform swap if different positions
                        if target_idx != drag_data["source_idx"]:
                            src = drag_data["source_idx"]
                            # Swap items in the list
                            selected_services_list[src], selected_services_list[target_idx] = (
                                selected_services_list[target_idx], 
                                selected_services_list[src]
                            )
                        
                        # Reset drag state
                        drag_data["source_idx"] = None
                        drag_data["source_widget"] = None
                        edit_dialog.unbind("<Motion>")
                        
                        # Refresh display
                        update_selected_list()
                    
                    return on_press, on_release
                
                on_press_fn, on_release_fn = make_drag_handlers(idx, item_frame, drag_handle)
                
                # Bind to multiple elements for better drag capture
                for element in [item_frame, content_frame, drag_handle, service_label]:
                    element.bind("<Button-1>", on_press_fn)
                    element.bind("<ButtonRelease-1>", on_release_fn)
                
                # Controls on the right
                ctrl_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
                ctrl_frame.pack(side="right", padx=5, pady=2)
                
                # Remove button
                def make_remove_cmd(service_name):
                    def remove_service():
                        selected_services_list.remove(service_name)
                        service_widgets[service_name][1].set(False)
                        update_selected_list()
                    return remove_service
                
                ctk.CTkButton(
                    ctrl_frame,
                    text="✕",
                    command=make_remove_cmd(service),
                    width=24,
                    height=24,
                    font=("Arial", 10),
                    fg_color="#e74c3c"
                ).pack(side="left", padx=2)
        
        # Initial population of selected list
        update_selected_list()
        
        # Buttons
        btn_frame = ctk.CTkFrame(edit_dialog, fg_color="transparent")
        btn_frame.pack(pady=15, padx=15)
        
        def save_changes():
            if not selected_services_list:
                messagebox.showwarning("Invalid", "Select at least one service")
                return
            
            if self.account_workflow_manager.update_workflow(
                self.current_account,
                workflow_name,
                selected_services_list  # Preserves order
            ):
                edit_dialog.destroy()
                messagebox.showinfo("Success", f"Workflow '{workflow_name}' updated successfully")
                # Refresh parent dialog
                parent_dialog.destroy()
                self.open_current_account_workflow_editor()
                self.refresh_workflow_dropdown()
            else:
                messagebox.showerror("Error", "Failed to update workflow")
        
        ctk.CTkButton(
            btn_frame,
            text="Save",
            command=save_changes,
            width=120,
            height=32,
            font=("Arial", 11, "bold"),
            fg_color="#27ae60"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=edit_dialog.destroy,
            width=120,
            height=32,
            font=("Arial", 11),
            fg_color="gray"
        ).pack(side="left", padx=5)
    
    def _delete_workflow(self, parent_dialog, workflow_name):
        """Delete workflow for current account"""
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete workflow '{workflow_name}'?\n\nThis cannot be undone."
        )
        
        if confirm:
            if self.account_workflow_manager.delete_workflow(self.current_account, workflow_name):
                messagebox.showinfo("Success", f"Workflow '{workflow_name}' deleted")
                # Refresh parent dialog
                parent_dialog.destroy()
                self.open_current_account_workflow_editor()
                self.refresh_workflow_dropdown()
            else:
                messagebox.showerror("Error", "Failed to delete workflow")
    
    def on_workflow_selected(self, workflow_name: str):
        """Handle workflow selection - populate services table and check for QuoteMe mapping"""
        if not workflow_name or not self.current_account:
            return
        
        self.selected_workflow = workflow_name
        services = self.account_workflow_manager.get_workflow_services(
            self.current_account,
            workflow_name
        )
        
        # Check if we have QuoteMe data and need to map values to services
        if self.quoteme_data and services:
            existing_mapping = self.quoteme_value_mapper.load_mapping(
                self.current_account
            )
            # Show dialog if new services exist that aren't in the mapping
            unmapped_services = [s for s in services if s not in existing_mapping]
            if unmapped_services:
                # New services need mapping
                self._show_quoteme_mapping_dialog(services, workflow_name)
            elif not existing_mapping:
                # No mapping exists at all for this account
                self._show_quoteme_mapping_dialog(services, workflow_name)
        
        self.populate_services_table(services)
    
    def _show_quoteme_mapping_dialog(self, services: List[str], workflow_name: str):
        """
        Show dialog to map QuoteMe word count fields to workflow services.
        Allows users to assign one or more QuoteMe fields to each service.
        Supports hourly service configuration (divider, increment, minimum).
        Loads existing account-level mappings (services mapped in other workflows).
        """
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Map QuoteMe Values - {self.current_account}")
        dialog.geometry("800x650")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (dialog.winfo_screenheight() // 2) - (650 // 2)
        dialog.geometry(f'800x650+{x}+{y}')
        
        # Header
        ctk.CTkLabel(
            dialog,
            text=f"Map QuoteMe Word Count Fields to Services",
            font=("Arial", 12, "bold")
        ).pack(pady=(15, 5), padx=15)
        
        ctk.CTkLabel(
            dialog,
            text=f"For each service, select which QuoteMe fields to use (can combine multiple)\nMappings are account-level and reused across all workflows",
            font=("Arial", 9),
            text_color="gray"
        ).pack(padx=15, pady=(0, 15))
        
        # Load existing account-level mapping
        existing_mapping = self.quoteme_value_mapper.load_mapping(self.current_account)
        
        # Main scrollable frame
        main_scroll = ctk.CTkScrollableFrame(dialog, fg_color="gray25", corner_radius=6)
        main_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        def on_mousewheel(event):
            main_scroll._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_scroll.bind("<MouseWheel>", on_mousewheel)
        
        # Track configuration for each service
        service_configs = {}
        
        # Create a frame for each service
        for service in services:
            service_frame = ctk.CTkFrame(main_scroll, fg_color="gray20", corner_radius=4)
            service_frame.pack(fill="x", padx=5, pady=5)
            
            # Header with service name and config button
            header_frame = ctk.CTkFrame(service_frame, fg_color="transparent")
            header_frame.pack(fill="x", padx=10, pady=(8, 3))
            
            ctk.CTkLabel(
                header_frame,
                text=f"📌 {service}",
                font=("Arial", 10, "bold"),
                text_color="white"
            ).pack(anchor="w", side="left", expand=True)
            
            # Config button for hourly settings
            def make_config_button(svc_name):
                def open_config():
                    self._show_service_config_dialog(dialog, svc_name, service_configs)
                return open_config
            
            ctk.CTkButton(
                header_frame,
                text="⚙️ Config",
                command=make_config_button(service),
                width=80,
                height=24,
                font=("Arial", 9),
                fg_color="#555"
            ).pack(side="right", padx=5)
            
            # Checkboxes for QuoteMe fields
            field_vars = {}
            fields_frame = ctk.CTkFrame(service_frame, fg_color="transparent")
            fields_frame.pack(fill="x", padx=20, pady=(3, 8))
            
            # Load existing fields for this service if available
            existing_fields = []
            if service in existing_mapping:
                existing_fields = existing_mapping[service].get("fields", [])
            
            for field in self.quoteme_value_mapper.available_fields:
                var = ctk.BooleanVar(value=(field in existing_fields))
                field_vars[field] = var
                
                cb = ctk.CTkCheckBox(
                    fields_frame,
                    text=field,
                    variable=var,
                    font=("Arial", 9),
                    onvalue=True,
                    offvalue=False
                )
                cb.pack(anchor="w", side="left", padx=5, pady=2)
            
            # Initialize service config
            if service in existing_mapping:
                service_configs[service] = existing_mapping[service].copy()
            else:
                service_configs[service] = {
                    "fields": [],
                    "hourly": False,
                    "divider": 1.0,
                    "increment": 1.0,
                    "minimum": 0
                }
            
            service_configs[service]["field_vars"] = field_vars
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=15, padx=15)
        
        def save_mapping():
            # Build mapping dict from checkbox states
            mapping = {}
            for service, config in service_configs.items():
                field_vars = config.pop("field_vars", {})
                selected_fields = [field for field, var in field_vars.items() if var.get()]
                
                if selected_fields or config.get("hourly", False):
                    # Save config even if no fields selected (might be pre-filled with hourly settings)
                    config["fields"] = selected_fields
                    mapping[service] = config
            
            if not mapping:
                messagebox.showwarning(
                    "No Fields Selected",
                    "Please select at least one field for at least one service"
                )
                return
            
            # Save the account-level mapping
            self.quoteme_value_mapper.save_mapping(
                self.current_account,
                mapping
            )
            
            messagebox.showinfo(
                "Mapping Saved",
                f"QuoteMe value mapping saved for account {self.current_account}\n(applies to all workflows)"
            )
            dialog.destroy()
        
        def skip_mapping():
            dialog.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text="Save Mapping",
            command=save_mapping,
            width=150,
            height=32,
            font=("Arial", 11, "bold"),
            fg_color="green"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Skip for Now",
            command=skip_mapping,
            width=150,
            height=32,
            font=("Arial", 11),
            fg_color="gray"
        ).pack(side="left", padx=5)
    
    def _show_service_config_dialog(self, parent_dialog, service_name: str, service_configs: dict):
        """
        Show configuration dialog for hourly service settings.
        Allows setting divider, increment, and minimum values.
        """
        config_dialog = ctk.CTkToplevel(parent_dialog)
        config_dialog.title(f"Configure: {service_name}")
        config_dialog.geometry("400x350")
        config_dialog.transient(parent_dialog)
        config_dialog.grab_set()
        
        # Center dialog
        config_dialog.update_idletasks()
        x = (config_dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (config_dialog.winfo_screenheight() // 2) - (350 // 2)
        config_dialog.geometry(f'400x350+{x}+{y}')
        
        current_config = service_configs[service_name]
        
        # Header
        ctk.CTkLabel(
            config_dialog,
            text=f"Service Configuration: {service_name}",
            font=("Arial", 11, "bold")
        ).pack(pady=(15, 20), padx=15)
        
        # Hourly checkbox
        hourly_var = ctk.BooleanVar(value=current_config.get("hourly", False))
        
        hourly_check = ctk.CTkCheckBox(
            config_dialog,
            text="Hourly Service (apply hourly calculations)",
            variable=hourly_var,
            font=("Arial", 10),
            onvalue=True,
            offvalue=False
        )
        hourly_check.pack(anchor="w", padx=30, pady=10)
        
        # Divider field
        divider_frame = ctk.CTkFrame(config_dialog, fg_color="transparent")
        divider_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(
            divider_frame,
            text="Divider (e.g., 8 for 8-hour day):",
            font=("Arial", 10)
        ).pack(anchor="w")
        
        divider_entry = ctk.CTkEntry(
            divider_frame,
            placeholder_text="1.0"
        )
        divider_entry.pack(fill="x", pady=(5, 0))
        divider_entry.insert(0, str(current_config.get("divider", 1.0)))
        
        # Increment field
        increment_frame = ctk.CTkFrame(config_dialog, fg_color="transparent")
        increment_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(
            increment_frame,
            text="Increment (e.g., 0.5 for rounding):",
            font=("Arial", 10)
        ).pack(anchor="w")
        
        increment_entry = ctk.CTkEntry(
            increment_frame,
            placeholder_text="1.0"
        )
        increment_entry.pack(fill="x", pady=(5, 0))
        increment_entry.insert(0, str(current_config.get("increment", 1.0)))
        
        # Minimum field
        minimum_frame = ctk.CTkFrame(config_dialog, fg_color="transparent")
        minimum_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(
            minimum_frame,
            text="Minimum Value:",
            font=("Arial", 10)
        ).pack(anchor="w")
        
        minimum_entry = ctk.CTkEntry(
            minimum_frame,
            placeholder_text="0"
        )
        minimum_entry.pack(fill="x", pady=(5, 0))
        minimum_entry.insert(0, str(current_config.get("minimum", 0)))
        
        # Help text
        help_label = ctk.CTkLabel(
            config_dialog,
            text="Formula: ((base_value / divider) rounded to increment) with minimum",
            font=("Arial", 8),
            text_color="gray"
        )
        help_label.pack(padx=30, pady=(15, 0))
        
        # Buttons
        btn_frame = ctk.CTkFrame(config_dialog, fg_color="transparent")
        btn_frame.pack(pady=15)
        
        def save_config():
            try:
                divider = float(divider_entry.get() or 1.0)
                increment = float(increment_entry.get() or 1.0)
                minimum = int(minimum_entry.get() or 0)
                
                if divider <= 0:
                    messagebox.showerror("Invalid", "Divider must be greater than 0")
                    return
                if increment <= 0:
                    messagebox.showerror("Invalid", "Increment must be greater than 0")
                    return
                
                service_configs[service_name]["hourly"] = hourly_var.get()
                service_configs[service_name]["divider"] = divider
                service_configs[service_name]["increment"] = increment
                service_configs[service_name]["minimum"] = minimum
                
                config_dialog.destroy()
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers")
        
        ctk.CTkButton(
            btn_frame,
            text="Save Config",
            command=save_config,
            width=120,
            fg_color="#2b7dbc"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Close",
            command=config_dialog.destroy,
            width=120,
            fg_color="gray"
        ).pack(side="left", padx=5)
    
    
    def set_language_pairs_from_quoteme(self, quoteme_data):
        """
        Set language pairs from parsed QuoteMe data
        
        Args:
            quoteme_data: List of LanguagePairData objects from QuoteMe parser
        """
        self.quoteme_data = quoteme_data
        self.language_pairs = []
        
        if quoteme_data:
            for lp_data in quoteme_data:
                if lp_data.lp_code:
                    # Extract only the language pair name ("Source > Target") without parsed data
                    lp_name = self._extract_lp_name(lp_data.lp_code)
                    self.language_pairs.append(lp_name)
        
        # Refresh the services table to show the new language pairs
        if self.selected_workflow and self.current_account:
            services = self.account_workflow_manager.get_workflow_services(
                self.current_account,
                self.selected_workflow
            )
            if services:
                self.populate_services_table(services)
    
    @staticmethod
    def _extract_lp_name(lp_code: str) -> str:
        """
        Extract only the 'Source > Target' part from an lp_code string
        Handles multi-line lp_code that may contain parsed data
        Preserves full language names including regions in parentheses
        """
        import re
        first_line = lp_code.split('\n')[0].strip()
        
        # Split on > separator and reconstruct with proper handling of regions
        parts = first_line.split('>')
        if len(parts) >= 2:
            source = parts[0].strip()
            # Join remaining parts (in case of multiple >)
            target = '>'.join(parts[1:]).strip()
            # Remove any trailing metadata that starts with double-space or common keywords
            target = re.split(r'\s{2,}|Context|Remote|TM Configuration', target)[0].strip()
            return f"{source} > {target}"
        
        # Fallback: return first line if it contains >
        if '>' in first_line:
            return first_line.split(':')[0].strip()
        
        return first_line[:80]

    def on_rate_card_selected(self, rate_card_name: str):
        """Handle rate card selection - update rates in table"""
        if not rate_card_name:
            return
        
        self.selected_rate_card = rate_card_name
        rate_card = self.load_rate_card(rate_card_name)
        
        if rate_card:
            # Get clean name for display (remove [Master] prefix if present)
            display_name = rate_card_name.replace("[Master] ", "")
            
            # Normalize rate card services and cache it
            rate_card = self.normalize_rate_card_services(rate_card, display_name)
            self.rate_card_info.configure(text=f"✓ Using rate card: {display_name}")
            # Update rates in the table
            self.update_rates_in_table(rate_card)
        else:
            display_name = rate_card_name.replace("[Master] ", "")
            self.rate_card_info.configure(text=f"⚠️ Failed to load rate card: {display_name}")
    
    def browse_rate_card_file(self):
        """Open file dialog to browse and load a rate card JSON or XLSX file"""
        rate_card_dir = Path(__file__).parent.parent / "Rate_Card_Builder"
        
        file_path = filedialog.askopenfilename(
            title="Select a Rate Card File",
            initialdir=str(rate_card_dir),
            filetypes=[("Rate Card Files", "*.json *.xlsx"), ("JSON files", "*.json"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                file_ext = Path(file_path).suffix.lower()
                
                print(f"\n=== DEBUG: Browsing Rate Card File ===")
                print(f"Selected file path: {file_path}")
                print(f"File extension: {file_ext}")
                
                # Load rate card based on file format
                if file_ext == ".xlsx":
                    # Load Excel rate card
                    rate_card = load_excel_rate_card(file_path)
                    print(f"Loaded from Excel file")
                elif file_ext == ".json":
                    # Load JSON rate card
                    with open(file_path, 'r', encoding='utf-8') as f:
                        rate_card = json.load(f)
                    print(f"Loaded from JSON file")
                else:
                    messagebox.showerror("Error", f"Unsupported file format: {file_ext}\nSupported formats: .json, .xlsx")
                    return
                
                # Extract rate card name from filename
                filename = Path(file_path).stem
                if filename.startswith("rate_cards_"):
                    rate_card_name = filename.replace("rate_cards_", "")
                else:
                    rate_card_name = filename
                
                print(f"Extracted rate card name: {rate_card_name}")
                # Normalize services to canonical names
                if rate_card:
                    rate_card = self.normalize_rate_card_services(rate_card, rate_card_name)
                
                # Update selection and load
                self.selected_rate_card = rate_card_name
                self.rate_card_dropdown.set(rate_card_name)
                
                # Update rates in table
                if rate_card:
                    self.rate_card_info.configure(text=f"✓ Using rate card: {rate_card_name}")
                    self.update_rates_in_table(rate_card)
                    
                    # Offer to save as master rate card
                    save_master = messagebox.askyesno(
                        "Save to Master",
                        f"Would you like to save '{rate_card_name}' to your master rate cards?\n\n(You can then load it directly from the dropdown without browsing)"
                    )
                    if save_master:
                        saved_name = self.save_master_rate_card(rate_card, rate_card_name)
                        if saved_name:
                            # Update dropdown and selection to the new master card
                            self.refresh_rate_card_dropdown()
                            master_card_name = f"[Master] {saved_name}"
                            self.selected_rate_card = master_card_name
                            self.rate_card_dropdown.set(master_card_name)
                            self.rate_card_info.configure(text=f"✓ Using rate card: {saved_name} (Master)")
                else:
                    self.rate_card_info.configure(text=f"⚠️ Failed to load rate card: {rate_card_name}")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load rate card file:\n{str(e)}")
                self.rate_card_info.configure(text=f"⚠️ Error loading rate card: {str(e)[:50]}")
    
    def normalize_rate_card_services(self, rate_card: dict, rate_card_name: str) -> dict:
        """
        Normalize rate card services to canonical names.
        Prompts user to map any unmapped services.
        Caches the normalized rate card for use across workflow changes.
        
        Args:
            rate_card: Loaded rate card dictionary
            rate_card_name: Name of the rate card (for saving mappings)
            
        Returns:
            Rate card with normalized service names
        """
        if "languages" not in rate_card:
            return rate_card
        
        # Columns to ignore (metadata, not services)
        ignore_columns = {"Iso Code", "iso code", "ISO Code", "ISO CODE"}
        
        # Extract services from rate card
        rate_card_services = []
        for lang_data in rate_card.get("languages", {}).values():
            if isinstance(lang_data, dict) and "rates" in lang_data:
                for service in lang_data["rates"].keys():
                    # Skip ignored columns
                    if service not in ignore_columns:
                        rate_card_services.append(service)
        
        rate_card_services = list(set(rate_card_services))  # Unique services
        
        # Normalize services using service mapper
        mapping, unmapped = self.service_mapper.normalize_services(
            rate_card_services,
            account_name=self.current_account,
            rate_card_name=rate_card_name
        )
        
        # If there are unmapped services, show mapping dialog
        if unmapped and self.current_account:
            self._show_service_mapping_dialog(
                unmapped, 
                mapping,
                rate_card_name
            )
        
        # Apply mapping to rate card
        normalized_card = self.service_mapper.apply_service_mapping(rate_card, mapping)
        
        # Save mapping for future use
        if self.current_account and mapping:
            self.service_mapper.save_mapping(
                self.current_account,
                rate_card_name,
                mapping
            )
        
        # Cache the normalized rate card for use across workflow changes
        self.cached_rate_card = normalized_card
        
        return normalized_card
    
    def get_master_rate_cards_path(self) -> Path:
        """Get path to master rate cards file"""
        core_path = Path(__file__).parent.parent / "Core"
        return core_path / "master_rate_cards.json"
    
    def load_master_rate_cards(self) -> dict:
        """Load all master rate cards from JSON file"""
        master_path = self.get_master_rate_cards_path()
        try:
            if master_path.exists():
                with open(master_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"rate_cards": {}}
        except Exception as e:
            print(f"Error loading master rate cards: {e}")
            return {"rate_cards": {}}
    
    def save_master_rate_card(self, rate_card: dict, suggested_name: str):
        """
        Save rate card to master list.
        Opens dialog for user to confirm name and optionally overwrite.
        Shows existing rate cards as clickable options.
        Returns the saved name if successful, None otherwise.
        """
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Save to Master Rate Cards")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (450 // 2)
        dialog.geometry(f'500x450+{x}+{y}')
        
        saved_name = [None]  # Use list to capture in closure
        
        ctk.CTkLabel(
            dialog,
            text="Save as Master Rate Card",
            font=("Arial", 12, "bold")
        ).pack(pady=(15, 10), padx=15)
        
        # Name entry section
        ctk.CTkLabel(
            dialog,
            text="Rate Card Name:",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=15, pady=(0, 5))
        
        name_entry = ctk.CTkEntry(dialog, font=("Arial", 11))
        name_entry.insert(0, suggested_name)
        name_entry.pack(fill="x", padx=15, pady=(0, 15))
        name_entry.select_range(0, len(suggested_name))
        name_entry.focus()
        
        # Divider
        ctk.CTkLabel(
            dialog,
            text="Or select an existing rate card to overwrite:",
            font=("Arial", 10, "bold"),
            text_color="orange"
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Load existing rate cards
        master_data = self.load_master_rate_cards()
        existing_names = list(master_data.get("rate_cards", {}).keys())
        
        # Scrollable frame for existing rate cards
        if existing_names:
            scroll_frame = ctk.CTkScrollableFrame(dialog, fg_color="gray20", corner_radius=6)
            scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
            
            def on_mousewheel(event):
                scroll_frame._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            scroll_frame.bind("<MouseWheel>", on_mousewheel)
            
            def select_existing(selected_name):
                # Populate the name entry with selected name
                name_entry.delete(0, "end")
                name_entry.insert(0, selected_name)
                name_entry.select_range(0, len(selected_name))
                # Update button highlights
                for btn, btn_name in existing_buttons:
                    if btn_name == selected_name:
                        btn.configure(fg_color="#2b7dbc")  # Highlight selected
                    else:
                        btn.configure(fg_color="#555")
            
            existing_buttons = []
            for existing_name in sorted(existing_names):
                btn = ctk.CTkButton(
                    scroll_frame,
                    text=existing_name,
                    command=lambda name=existing_name: select_existing(name),
                    font=("Arial", 10),
                    height=32,
                    fg_color="#555",
                    hover_color="#666",
                    corner_radius=4
                )
                btn.pack(fill="x", padx=5, pady=3)
                existing_buttons.append((btn, existing_name))
        else:
            ctk.CTkLabel(
                dialog,
                text="No existing rate cards yet",
                font=("Arial", 9),
                text_color="gray"
            ).pack(padx=15, pady=(5, 15))
        
        # Status label for feedback
        status_label = ctk.CTkLabel(
            dialog,
            text="",
            font=("Arial", 9),
            text_color="orange"
        )
        status_label.pack(anchor="w", padx=15, pady=(0, 10))
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=15, padx=15)
        
        def do_save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Invalid Name", "Please enter a name for the rate card")
                return
            
            # Load current master data
            master_data = self.load_master_rate_cards()
            
            # Check if name exists
            if name in master_data.get("rate_cards", {}):
                overwrite = messagebox.askyesno(
                    "Overwrite Existing",
                    f"'{name}' already exists.\n\nDo you want to overwrite it?"
                )
                if not overwrite:
                    status_label.configure(text="❌ Save cancelled. You can edit the name and try again.")
                    return
            
            # Save the rate card
            master_data["rate_cards"][name] = rate_card
            
            master_path = self.get_master_rate_cards_path()
            try:
                master_path.parent.mkdir(parents=True, exist_ok=True)
                with open(master_path, 'w', encoding='utf-8') as f:
                    json.dump(master_data, f, indent=2, ensure_ascii=False)
                
                saved_name[0] = name
                messagebox.showinfo("Success", f"Rate card '{name}' saved successfully!")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save rate card: {str(e)}")
        
        def do_cancel():
            saved_name[0] = None
            dialog.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text="Save",
            command=do_save,
            width=120,
            height=32,
            font=("Arial", 11, "bold"),
            fg_color="green"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=do_cancel,
            width=120,
            height=32,
            font=("Arial", 11),
            fg_color="gray"
        ).pack(side="left", padx=5)
        
        dialog.wait_window()
        return saved_name[0]
    
    def _show_service_mapping_dialog(self, unmapped_services: list, current_mapping: dict, rate_card_name: str):
        """
        Show dialog for user to map unmapped services to canonical names.
        
        Args:
            unmapped_services: List of services from rate card that don't have exact matches
            current_mapping: Current mapping dict (will be updated)
            rate_card_name: Name of the rate card
        """
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Map Services - {rate_card_name}")
        dialog.geometry("700x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Title
        title_label = ctk.CTkLabel(
            dialog,
            text=f"Map Unmapped Services from {rate_card_name}",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=10, padx=20)
        
        # Info text
        info_label = ctk.CTkLabel(
            dialog,
            text=f"The following {len(unmapped_services)} service(s) need to be mapped to canonical names:\n(Select a canonical name from the dropdown for each service)",
            font=("Arial", 10),
            text_color="#888",
            wraplength=650
        )
        info_label.pack(pady=5, padx=20)
        
        # Main content frame with custom scrolling
        content_frame = ctk.CTkFrame(dialog, fg_color="#2b2b2b")
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Use Canvas + Frame for scrolling to avoid CTkScrollableFrame issues
        canvas = ctk.CTkCanvas(content_frame, bg="#2b2b2b", highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(content_frame, orientation="vertical", command=canvas.yview)
        scrollable_frame = ctk.CTkFrame(canvas, fg_color="#2b2b2b")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create dropdown for each unmapped service
        service_dropdowns = {}
        for idx, unmapped_service in enumerate(unmapped_services):
            frame = ctk.CTkFrame(scrollable_frame, fg_color="#3b3b3b", corner_radius=5)
            frame.pack(fill="x", pady=8, padx=5)
            
            # Service name label
            service_label = ctk.CTkLabel(
                frame,
                text=f"{idx + 1}. {unmapped_service}",
                font=("Arial", 11, "bold"),
                text_color="#fff",
                anchor="w"
            )
            service_label.pack(fill="x", padx=10, pady=(8, 4))
            
            # Dropdown for canonical names
            dropdown_frame = ctk.CTkFrame(frame, fg_color="transparent")
            dropdown_frame.pack(fill="x", padx=10, pady=(0, 8))
            
            dropdown_label = ctk.CTkLabel(
                dropdown_frame,
                text="Map to:",
                font=("Arial", 9),
                text_color="#aaa"
            )
            dropdown_label.pack(side="left", padx=(0, 10))
            
            # Use StringVar to track dropdown value
            var = ctk.StringVar(value="")
            
            dropdown = ctk.CTkComboBox(
                dropdown_frame,
                variable=var,
                values=self.service_mapper.canonical_services,
                state="readonly",
                width=400,
                font=("Arial", 10)
            )
            dropdown.pack(side="left", fill="x", expand=True)
            service_dropdowns[unmapped_service] = var
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        dialog.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Skip/Cancel buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=15, padx=20, fill="x")
        
        def on_skip():
            """Skip mapping for now"""
            dialog.destroy()
        
        def on_save():
            """Save the mappings"""
            mapped_count = 0
            for service, var in service_dropdowns.items():
                selected = var.get()
                if selected:
                    current_mapping[service] = selected
                    mapped_count += 1
            
            # Save to file
            if self.current_account:
                self.service_mapper.save_mapping(
                    self.current_account,
                    rate_card_name,
                    current_mapping
                )
                messagebox.showinfo(
                    "Success",
                    f"Service mappings saved for {rate_card_name}\n({mapped_count} service(s) mapped)"
                )
            
            dialog.destroy()
        
        skip_btn = ctk.CTkButton(
            button_frame,
            text="Skip for Now",
            command=on_skip,
            fg_color="#555",
            width=150
        )
        skip_btn.pack(side="right", padx=5)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save Mappings",
            command=on_save,
            fg_color="#2b7dbc",
            width=150
        )
        save_btn.pack(side="right", padx=5)

    
    def populate_services_table(self, services: list):
        """
        Populate the services table with workflow services and language pair columns.
        Uses pure grid layout for perfect alignment of LP headers with Qty/Rate columns.
        """
        # Clear existing widgets
        for widget in self.services_table_frame.winfo_children():
            widget.destroy()
        
        self.workflow_service_widgets = {}
        
        if not services or not self.language_pairs:
            msg_text = "Select a workflow to view services"
            if not self.language_pairs:
                msg_text = "No language pairs available. Parse QuoteMe data first."
            
            self.services_empty_label = ctk.CTkLabel(
                self.services_table_frame,
                text=msg_text,
                font=("Arial", 10),
                text_color="gray"
            )
            self.services_empty_label.pack(expand=True, pady=20)
            return
        
        # Create a main table frame using grid layout
        table_frame = ctk.CTkFrame(self.services_table_frame, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Configure columns: Service column (column 0) + LP columns (2 per LP)
        table_frame.grid_columnconfigure(0, minsize=150, weight=0)  # Service column - fixed
        for lp_idx in range(len(self.language_pairs)):
            col_qty = 1 + lp_idx * 2
            col_rate = 2 + lp_idx * 2
            table_frame.grid_columnconfigure(col_qty, minsize=50, weight=1)
            table_frame.grid_columnconfigure(col_rate, minsize=60, weight=1)
        
        # Create header row (row 0) - Service column header
        service_header = ctk.CTkLabel(
            table_frame,
            text="Services",
            font=("Arial", 9, "bold"),
            text_color="white",
            fg_color="gray30"
        )
        service_header.grid(row=0, column=0, sticky="ew", padx=1, pady=1)
        
        # Create LP header containers (row 0, spanning columns for each LP)
        for lp_idx, lp in enumerate(self.language_pairs):
            col_start = 1 + lp_idx * 2
            col_span = 2
            
            # Container frame for this LP (spans 2 columns: Qty and Rate)
            lp_header_container = ctk.CTkFrame(
                table_frame,
                fg_color="#2b5f8f",
                corner_radius=3,
                border_width=1,
                border_color="#1f4470"
            )
            lp_header_container.grid(
                row=0,
                column=col_start,
                columnspan=col_span,
                sticky="ew",
                padx=1,
                pady=1
            )
            lp_header_container.grid_columnconfigure(0, weight=1)
            lp_header_container.grid_rowconfigure(0, weight=1)
            lp_header_container.grid_rowconfigure(1, weight=1)
            
            # LP name (top part of container)
            ctk.CTkLabel(
                lp_header_container,
                text=lp,
                font=("Arial", 7, "bold"),
                text_color="white",
                wraplength=105,
                justify="center"
            ).grid(row=0, column=0, sticky="ew", padx=3, pady=(2, 1))
            
            # Qty | Rate sub-header (bottom part of container)
            ctk.CTkLabel(
                lp_header_container,
                text="Qty | Rate",
                font=("Arial", 6),
                text_color="#b0c4de"
            ).grid(row=1, column=0, sticky="ew", padx=3, pady=(1, 2))
        
        # Create service rows
        for row_idx, service in enumerate(services, start=1):
            row_bg = "gray22" if row_idx % 2 == 1 else "gray20"
            
            # Service name cell
            service_label = ctk.CTkLabel(
                table_frame,
                text=service,
                font=("Arial", 9),
                text_color="white",
                fg_color=row_bg,
                anchor="w",
                wraplength=140,
                justify="left"
            )
            service_label.grid(row=row_idx, column=0, sticky="ew", padx=1, pady=1)
            
            # Create entries for each language pair
            service_data = {}
            for lp_idx, lp in enumerate(self.language_pairs):
                col_qty = 1 + lp_idx * 2
                col_rate = 2 + lp_idx * 2
                
                # Quantity entry
                quantity_entry = ctk.CTkEntry(
                    table_frame,
                    width=40,
                    height=28,
                    font=("Arial", 8),
                    placeholder_text="0",
                    fg_color="#3a3a3a",
                    border_color="#505050"
                )
                quantity_entry.grid(row=row_idx, column=col_qty, sticky="ew", padx=1, pady=1)
                
                # Rate entry
                rate_entry = ctk.CTkEntry(
                    table_frame,
                    width=50,
                    height=28,
                    font=("Arial", 8),
                    placeholder_text="0.00",
                    fg_color="#3a3a3a",
                    border_color="#505050"
                )
                rate_entry.grid(row=row_idx, column=col_rate, sticky="ew", padx=1, pady=1)
                
                service_data[lp] = {
                    "quantity": quantity_entry,
                    "rate": rate_entry
                }
            
            self.workflow_service_widgets[service] = service_data
        
        # Try to populate rates from current rate card (use cached version if available)
        if self.selected_rate_card:
            # Use cached normalized rate card if available
            if self.cached_rate_card:
                rate_card = self.cached_rate_card
            else:
                # Fall back to loading from file (will be normalized on next selection)
                rate_card = self.load_rate_card(self.selected_rate_card)
            
            if rate_card:
                self.update_rates_in_table(rate_card)
        
        # Try to populate quantities from QuoteMe mapping (if available)
        if self.quoteme_data and self.selected_workflow:
            self.update_quantities_from_quoteme(self.selected_workflow)
    
    def update_rates_in_table(self, rate_card: dict):
        """Update rate values in the services table from a rate card"""
        if not self.workflow_service_widgets:
            return
        
        # Debug: Print rate card structure
        print("\n=== DEBUG: Rate Card Structure ===")
        if "languages" in rate_card:
            print(f"Languages in rate card: {list(rate_card['languages'].keys())}")
            # Show first language's structure
            for lang_name, lang_data in list(rate_card['languages'].items())[:1]:
                if isinstance(lang_data, dict) and "rates" in lang_data:
                    print(f"Services in {lang_name}: {list(lang_data['rates'].keys())}")
        
        for service, service_data in self.workflow_service_widgets.items():
            for lp, widgets in service_data.items():
                # Extract target language from language pair (e.g., "Polish" from "English > Polish")
                if ">" in lp:
                    _, target_lang = lp.split(">", 1)
                    target_lang = target_lang.strip()
                else:
                    target_lang = lp
                
                # Get rate based on target language
                rate = self.get_rate_from_card(rate_card, service, target_lang)
                print(f"DEBUG: Service='{service}', LP='{lp}', Target='{target_lang}' -> Rate='{rate}'")
                
                if rate:
                    widgets["rate"].delete(0, "end")
                    widgets["rate"].insert(0, rate)
    
    def update_quantities_from_quoteme(self, workflow_name: str):
        """
        Populate service quantities from QuoteMe data based on saved account-level mapping.
        Applies calculations including hourly service conversions.
        """
        if not self.quoteme_data or not workflow_name:
            return
        
        # Load the account-level mapping (shared across all workflows)
        mapping = self.quoteme_value_mapper.load_mapping(
            self.current_account
        )
        
        if not mapping:
            return  # No mapping defined for this account
        
        # Get the first language pair's QuoteMe data (word counts are same for all LPs in QuoteMe)
        if not self.quoteme_data or not self.quoteme_data[0]:
            return
        
        quoteme_lp_data = self.quoteme_data[0]  # Get word count data from first LP
        word_count_data = quoteme_lp_data.get_effective_wc(use_cumulative=True)
        
        # Apply quantities to services based on account-level mapping
        for service, service_config in mapping.items():
            if service not in self.workflow_service_widgets:
                continue
            
            # Calculate quantity using service config (handles hourly calculations)
            quantity = self.quoteme_value_mapper.calculate_service_value(
                word_count_data,
                service_config
            )
            
            # Apply quantity to all language pairs for this service
            service_data = self.workflow_service_widgets[service]
            for lp, widgets in service_data.items():
                widgets["quantity"].delete(0, "end")
                widgets["quantity"].insert(0, str(quantity))

    def refresh_pa_integration_tab(self):
        """Reload PA Template Mapper in the Configure Template sub-tab for current account"""
        if not hasattr(self, 'pa_mapper_container'):
            return

        # Clear existing content
        for widget in self.pa_mapper_container.winfo_children():
            widget.destroy()

        if not self.current_account:
            ctk.CTkLabel(
                self.pa_mapper_container,
                text="Select an account to load the Template Mapper",
                font=("Arial", 13),
                text_color="gray"
            ).pack(expand=True, pady=60)
            return

        try:
            from gui.pa_template_mapper_gui import PATemplateMapperGUI
            PATemplateMapperGUI(
                self.root,
                self.current_account,
                dataframe=self.current_data,
                frame=self.pa_mapper_container
            )
        except Exception as e:
            ctk.CTkLabel(
                self.pa_mapper_container,
                text=f"⚠️ Failed to load Template Mapper:\n{str(e)}",
                font=("Arial", 12),
                text_color="#e74c3c"
            ).pack(expand=True, pady=40)

    def _run_inline_preview(self):
        """Run PA data preview and show results in the Data Preview sub-tab"""
        source_data = self.filtered_job_data if self.filtered_job_data is not None else self.current_data

        if source_data is None:
            self.pa_preview_status.configure(text="⚠️ No data loaded", text_color="#e74c3c")
            return
        if not self.current_account:
            self.pa_preview_status.configure(text="⚠️ No account selected", text_color="#e74c3c")
            return

        template = self.template_manager.get_template(self.current_account)
        if not template:
            self.pa_preview_status.configure(text="⚠️ No template configured", text_color="#e74c3c")
            return

        try:
            self.pa_preview_status.configure(text="Generating…", text_color="#3498db")
            self.root.update_idletasks()

            preview_df = self.template_processor.process_dataframe(
                source_data, source_data, self.current_account, row_index=0
            )

            # Clear scroll area
            for widget in self.pa_preview_scroll.winfo_children():
                widget.destroy()

            if preview_df is None or len(preview_df) == 0:
                ctk.CTkLabel(
                    self.pa_preview_scroll,
                    text="No data returned from preview.",
                    font=("Arial", 12),
                    text_color="#e74c3c"
                ).pack(pady=30)
                self.pa_preview_status.configure(text="⚠️ Empty result", text_color="#e74c3c")
                return

            key_col = preview_df.columns[0]
            data_col = preview_df.columns[1]

            # Header row
            hdr = ctk.CTkFrame(self.pa_preview_scroll, fg_color="#2b7dbc")
            hdr.pack(fill="x", pady=(5, 8), padx=5)
            ctk.CTkLabel(hdr, text=key_col, font=("Arial", 12, "bold"), text_color="white",
                         width=280, anchor="w").pack(side="left", padx=12, pady=8)
            ctk.CTkLabel(hdr, text=data_col, font=("Arial", 12, "bold"), text_color="white",
                         anchor="w").pack(side="left", padx=12, pady=8, fill="x", expand=True)

            # Data rows
            for idx, row in preview_df.iterrows():
                bg = "#252525" if idx % 2 == 0 else "#2b2b2b"
                rf = ctk.CTkFrame(self.pa_preview_scroll, fg_color=bg)
                rf.pack(fill="x", pady=1, padx=5)
                ctk.CTkLabel(rf, text=str(row[key_col]), font=("Arial", 11),
                             text_color="#3498db", width=280, anchor="w").pack(side="left", padx=12, pady=6)
                val = str(row[data_col]) if pd.notna(row[data_col]) else ""
                ctk.CTkLabel(rf, text=val, font=("Arial", 11), text_color="white",
                             anchor="w", wraplength=500, justify="left").pack(
                    side="left", padx=12, pady=6, fill="x", expand=True)

            self.pa_preview_status.configure(
                text=f"✅ {len(preview_df)} fields previewed", text_color="#2ecc71"
            )

        except Exception as e:
            self.pa_preview_status.configure(text=f"⚠️ Error: {str(e)[:60]}", text_color="#e74c3c")

    def load_column_preferences(self, account_name):
        """Load saved column preferences for an account"""
        try:
            if self.column_prefs_file.exists():
                with open(self.column_prefs_file, 'r') as f:
                    prefs = json.load(f)
                    return prefs.get(account_name, [])
        except Exception as e:
            print(f"Error loading column preferences: {e}")
        return []
    
    def load_index_column(self, account_name):
        """Load saved index column for an account"""
        try:
            if self.job_config_file.exists():
                with open(self.job_config_file, 'r') as f:
                    config = json.load(f)
                    return config.get(account_name, {}).get('index_column')
        except Exception as e:
            print(f"Error loading index column: {e}")
        return None
    
    def save_index_column(self, account_name, column_name):
        """Save index column for an account"""
        try:
            config = {}
            if self.job_config_file.exists():
                with open(self.job_config_file, 'r') as f:
                    config = json.load(f)
            
            if account_name not in config:
                config[account_name] = {}
            
            config[account_name]['index_column'] = column_name
            
            # Ensure directory exists
            self.job_config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.job_config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.index_column = column_name
        except Exception as e:
            print(f"Error saving index column: {e}")
    
    def save_column_preferences(self, account_name, columns):
        """Save column preferences for an account"""
        try:
            prefs = {}
            if self.column_prefs_file.exists():
                with open(self.column_prefs_file, 'r') as f:
                    prefs = json.load(f)
            
            prefs[account_name] = columns
            
            # Ensure directory exists
            self.column_prefs_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.column_prefs_file, 'w') as f:
                json.dump(prefs, f, indent=2)
        except Exception as e:
            print(f"Error saving column preferences: {e}")
    
    def configure_index_column(self):
        """Show dialog to configure which column is the job index"""
        if self.current_data is None:
            messagebox.showwarning("No Data", "Please load data first")
            return
        
        if not self.current_account:
            messagebox.showwarning("No Account", "Please select an account first")
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Configure Job Index Column")
        dialog.geometry("550x550")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 275
        y = (dialog.winfo_screenheight() // 2) - 275
        dialog.geometry(f'550x550+{x}+{y}')
        
        # Title
        ctk.CTkLabel(
            dialog,
            text="Configure Job Index Column",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        # Info
        info_text = (
            f"Account: {self.current_account}\n\n"
            "Select which column contains the job identifier.\n"
            "This will be used to filter and aggregate job data."
        )
        ctk.CTkLabel(
            dialog,
            text=info_text,
            font=("Arial", 11),
            justify="left"
        ).pack(pady=10, padx=20)
        
        # Column selection
        selection_frame = ctk.CTkFrame(dialog)
        selection_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(
            selection_frame,
            text="Available Columns:",
            font=("Arial", 12, "bold")
        ).pack(pady=(10, 5))
        
        # Scrollable list of columns
        scroll_frame = ctk.CTkScrollableFrame(selection_frame, height=150)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        selected_var = ctk.StringVar(value=self.index_column or "")
        
        for col in self.current_data.columns:
            radio = ctk.CTkRadioButton(
                scroll_frame,
                text=col,
                variable=selected_var,
                value=col,
                font=("Arial", 11)
            )
            radio.pack(anchor="w", padx=10, pady=3)
        
        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=15)
        
        def save_selection():
            if selected_var.get():
                column = selected_var.get()
                self.save_index_column(self.current_account, column)
                self.index_column = column  # Ensure it's set immediately
                self.update_status(f"✅ Index column set to: {column}")
                messagebox.showinfo(
                    "Configuration Saved",
                    f"Index column has been set to:\n\n'{column}'\n\n"
                    f"For account: {self.current_account}\n\n"
                    "You can now use the job filter to search for specific jobs."
                )
                dialog.destroy()
            else:
                messagebox.showwarning("No Selection", "Please select a column")
        
        ctk.CTkButton(
            button_frame,
            text="Save",
            command=save_selection,
            width=120,
            height=35,
            font=("Arial", 12, "bold"),
            fg_color="#2ecc71"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            width=120,
            height=35,
            fg_color="gray",
            text_color="white"
        ).pack(side="left", padx=10)
    
    def configure_visible_columns(self):
        """Show dialog to select which columns to display"""
        if self.current_data is None:
            messagebox.showwarning("No Data", "Please load data first")
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Configure Visible Columns")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (250)
        y = (dialog.winfo_screenheight() // 2) - (300)
        dialog.geometry(f'500x600+{x}+{y}')
        
        # Title
        ctk.CTkLabel(
            dialog,
            text="Select Columns to Display",
            font=("Arial", 16, "bold")
        ).pack(pady=15)
        
        # Info
        ctk.CTkLabel(
            dialog,
            text="Check columns you want to see in the main window",
            font=("Arial", 11),
            text_color="gray"
        ).pack(pady=5)
        
        # Scrollable checkbox area
        checkbox_frame = ctk.CTkScrollableFrame(dialog, height=400)
        checkbox_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Load saved preferences to maintain column order
        saved_columns = self.load_column_preferences(self.current_account) if self.current_account else []
        
        # Build column list: keep saved order, then add new columns at bottom
        all_columns = list(self.current_data.columns)
        ordered_columns = []
        
        # First, add columns in saved order
        for col in saved_columns:
            if col in all_columns:
                ordered_columns.append(col)
        
        # Then, add any new columns not in saved preferences (at the bottom)
        for col in all_columns:
            if col not in ordered_columns:
                ordered_columns.append(col)
        
        # Create checkboxes for each column in preserved order
        column_vars = {}
        for col in ordered_columns:
            var = ctk.BooleanVar(value=col in self.visible_columns)
            column_vars[col] = var
            
            cb = ctk.CTkCheckBox(
                checkbox_frame,
                text=col,
                variable=var,
                font=("Arial", 12)
            )
            cb.pack(anchor="w", padx=10, pady=5)
        
        # Buttons
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(pady=15)
        
        def apply_selection():
            self.visible_columns = [col for col, var in column_vars.items() if var.get()]
            
            # Save preferences if account is selected
            if self.current_account:
                self.save_column_preferences(self.current_account, self.visible_columns)
            
            self.update_data_display()
            dialog.destroy()
            # Columns configured (status updated via display)
        
        def select_all():
            for var in column_vars.values():
                var.set(True)
        
        def deselect_all():
            for var in column_vars.values():
                var.set(False)
        
        ctk.CTkButton(
            button_frame,
            text="Select All",
            command=select_all,
            width=100,
            fg_color="#27ae60"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Clear All",
            command=deselect_all,
            width=100,
            fg_color="#e67e22"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Apply",
            command=apply_selection,
            width=100,
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            width=100,
            fg_color="gray",
            text_color="white"
        ).pack(side="left", padx=5)
    
    def update_data_display(self):
        """Update the data display area with selected columns"""
        # Clear existing display
        for widget in self.data_display_scroll.winfo_children():
            widget.destroy()
        
        if self.current_data is None:
            self.no_data_label = ctk.CTkLabel(
                self.data_display_scroll,
                text="No data loaded\n\nUse File menu to import job data or pull from GLE API",
                font=("Arial", 13),
                text_color="gray"
            )
            self.no_data_label.pack(expand=True, pady=50)
            return
        
        if not self.visible_columns:
            ctk.CTkLabel(
                self.data_display_scroll,
                text="⚙️ No columns configured\n\nClick the purple 'Configure Columns' button on the right →",
                font=("Arial", 13),
                text_color="#9b59b6"
            ).pack(expand=True, pady=50)
            return
        
        # Use filtered data if available, otherwise use full dataset
        display_data = self.filtered_job_data if self.filtered_job_data is not None else self.current_data
        
        # Display first row of data in Excel-like grid format with drag-to-reorder
        if len(display_data) > 0:
            first_row = display_data.iloc[0]
            
            # Create grid container with dark background
            grid_frame = ctk.CTkFrame(self.data_display_scroll, fg_color="#1e1e1e", corner_radius=8)
            grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Add each column as a draggable row in the grid
            for idx, col in enumerate(self.visible_columns):
                if col in first_row:
                    # Row frame for each field
                    row_frame = ctk.CTkFrame(grid_frame, fg_color="transparent")
                    row_frame.pack(fill="x", padx=15, pady=0)
                    
                    # Alternating row colors for better readability
                    row_bg = "#252525" if idx % 2 == 0 else "#1e1e1e"
                    
                    # Inner frame with background color
                    inner_frame = ctk.CTkFrame(row_frame, fg_color=row_bg, corner_radius=4)
                    inner_frame.pack(fill="x", pady=1)
                    
                    # Container for header and value (side by side)
                    content_frame = ctk.CTkFrame(inner_frame, fg_color="transparent")
                    content_frame.pack(fill="x", padx=8, pady=6)
                    
                    # Drag handle - visual indicator
                    drag_handle = ctk.CTkLabel(
                        content_frame,
                        text="☰",  # Hamburger menu icon
                        font=("Arial", 14),
                        text_color="#666666",
                        width=25,
                        cursor="hand2"
                    )
                    drag_handle.pack(side="left", padx=(5, 10))
                    
                    # Bind drag events to the drag handle
                    drag_handle.bind("<Button-1>", lambda e, c=col, i=idx: self.start_drag(e, c, i))
                    drag_handle.bind("<B1-Motion>", self.on_drag)
                    drag_handle.bind("<ButtonRelease-1>", self.end_drag)
                    
                    # Also bind to inner_frame for easier dragging
                    inner_frame.bind("<Button-1>", lambda e, c=col, i=idx: self.start_drag(e, c, i))
                    inner_frame.bind("<B1-Motion>", self.on_drag)
                    inner_frame.bind("<ButtonRelease-1>", self.end_drag)
                    inner_frame.configure(cursor="hand2")
                    
                    # Header (column name) - wider fixed width on left
                    header_label = ctk.CTkLabel(
                        content_frame,
                        text=col,
                        font=("Arial", 11, "bold"),
                        text_color="#3498db",
                        anchor="w",
                        width=300
                    )
                    header_label.pack(side="left", padx=(0, 20))
                    
                    # Value - expandable on right with wrapping
                    value = str(first_row[col]) if pd.notna(first_row[col]) else "N/A"
                    value_label = ctk.CTkLabel(
                        content_frame,
                        text=value,
                        font=("Arial", 11),
                        text_color="white",
                        anchor="w",
                        wraplength=600,
                        justify="left"
                    )
                    value_label.pack(side="left", fill="x", expand=True)
        else:
            empty_msg = "Filtered data is empty" if self.filtered_job_data is not None else "Data loaded but empty"
            ctk.CTkLabel(
                self.data_display_scroll,
                text=empty_msg,
                font=("Arial", 13),
                text_color="orange"
            ).pack(expand=True, pady=50)

    def start_drag(self, event, column, index):
        """Start dragging a row"""
        self.drag_source = column
        self.drag_source_index = index
        # Visual feedback - could highlight the row
        self.update_status(f"Dragging: {column}")
    
    def on_drag(self, event):
        """Handle drag motion"""
        # Could add visual feedback during drag
        pass
    
    def end_drag(self, event):
        """End drag and reorder if over a valid drop target"""
        if self.drag_source is None:
            return
        
        # Find which row we're over
        widget = event.widget.winfo_containing(event.x_root, event.y_root)
        
        # Try to find the target column by traversing parent widgets
        target_col = None
        target_idx = None
        
        # Get all visible column frames and check which one we're over
        for idx, col in enumerate(self.visible_columns):
            if col == self.drag_source:
                continue  # Skip the source itself
        
        # Use y-coordinate to determine drop position
        if widget and hasattr(widget, 'winfo_rooty'):
            # Calculate approximate drop index based on vertical position
            drop_y = event.y_root - self.data_display_scroll.winfo_rooty()
            row_height = 45  # Approximate height per row
            target_idx = int(drop_y / row_height)
            
            # Clamp to valid range
            target_idx = max(0, min(target_idx, len(self.visible_columns) - 1))
            
            # Reorder the columns
            if target_idx != self.drag_source_index and 0 <= target_idx < len(self.visible_columns):
                # Remove from old position
                col_to_move = self.visible_columns.pop(self.drag_source_index)
                # Insert at new position
                self.visible_columns.insert(target_idx, col_to_move)
                
                # Save the new order
                if self.current_account:
                    self.save_column_preferences(self.current_account, self.visible_columns)
                
                # Refresh display
                self.update_data_display()
                self.update_status(f"✓ Moved '{col_to_move}' to position {target_idx + 1}")
        
        # Reset drag state
        self.drag_source = None
        self.drag_source_index = None
    
    def browse_file(self):
        """Open file browser dialog"""
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[
                ("Excel files", "*.xlsx *.xls *.xlsm"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.load_file(file_path)
    
    def load_file(self, file_path):
        """Load Excel file into memory"""
        try:
            self.update_status("Loading file...")
            
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Store data
            self.current_data = df
            self.data_source = 'file'
            
            # Load index column configuration for current account
            if self.current_account:
                self.index_column = self.load_index_column(self.current_account)
            
            # Load and display data with default columns if not already configured
            if not self.visible_columns:
                # Auto-select first 5 columns as default
                self.visible_columns = list(self.current_data.columns[:5])
            
            self.update_data_display()
            
            # Update UI
            self.update_status(f"✅ File loaded: {Path(file_path).name}")
            self.update_data_info()
            self.enable_data_actions()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
            self.update_status("❌ Failed to load file")
    

    def filter_by_job_id(self):
        """Filter and aggregate data by job ID"""
        if self.current_data is None:
            messagebox.showwarning("No Data", "Please load data first")
            return
        
        if not self.index_column:
            messagebox.showwarning(
                "No Index Column",
                "Please configure the job index column first.\n\n"
                "Use View → Configure Index Column"
            )
            return
        
        job_id = self.job_id_entry.get().strip()
        if not job_id:
            messagebox.showwarning("No Job ID", "Please enter a job ID")
            return
        
        try:
            # Filter data by job ID
            filtered_df = self.current_data[self.current_data[self.index_column].astype(str) == job_id]
            
            if filtered_df.empty:
                messagebox.showinfo(
                    "No Results",
                    f"No data found for Job ID: {job_id}"
                )
                self.filter_status_label.configure(
                    text=f"❌ No data found for: {job_id}",
                    text_color="#e74c3c"
                )
                return
            
            # Aggregate the data
            self.filtered_job_data = self.aggregate_job_data(filtered_df)
            self.current_job_id = job_id
            
            # Update display
            self.update_data_display()
            
            self.filter_status_label.configure(
                text=f"✅ Showing job: {job_id} ({len(filtered_df)} rows aggregated)",
                text_color="#2ecc71"
            )
            self.update_status(f"Filtered by Job ID: {job_id}")
            
        except Exception as e:
            messagebox.showerror("Filter Error", f"Failed to filter data:\n{str(e)}")
    
    def clear_job_filter(self):
        """Clear job ID filter and show all data"""
        self.job_id_entry.delete(0, 'end')
        self.current_job_id = None
        self.filtered_job_data = None
        self.filter_status_label.configure(text="")
        self.update_data_display()
        self.update_status("Filter cleared")
    
    def aggregate_job_data(self, filtered_df):
        """Aggregate multiple rows for same job ID into single row
        
        Rules:
        - Duplicate values: Keep only unique value
        - Multiple unique values: Join with ', '
        """
        if len(filtered_df) == 1:
            return filtered_df
        
        aggregated = {}
        
        for col in filtered_df.columns:
            # Get all non-null values
            values = filtered_df[col].dropna().astype(str).unique().tolist()
            
            if len(values) == 0:
                aggregated[col] = ""
            elif len(values) == 1:
                # Only one unique value (including duplicates)
                aggregated[col] = values[0]
            else:
                # Multiple unique values - join with comma
                aggregated[col] = ", ".join(sorted(values))
        
        # Return as single-row DataFrame
        return pd.DataFrame([aggregated])
    
    def show_raw_data(self):
        """Open data viewer window"""
        if self.current_data is not None:
            DataViewerWindow(self.root, self.current_data)
        else:
            messagebox.showwarning("No Data", "No data loaded to display")
    
    def clear_data(self):
        """Clear loaded data"""
        confirm = messagebox.askyesno(
            "Clear Data",
            "Are you sure you want to clear the loaded data?\n\nThis action cannot be undone."
        )
        
        if confirm:
            self.current_data = None
            self.visible_columns = []
            self.data_source = None
            
            # Update UI
            self.update_status("Data cleared")
            self.update_data_info()
            self.disable_data_actions()
    
    def update_data_info(self):
        """Update data info label"""
        if hasattr(self, 'data_info_label'):
            if self.current_data is not None:
                rows, cols = self.current_data.shape
                
                # Auto-load saved column preferences for current account
                if self.current_account and not self.visible_columns:
                    saved_columns = self.load_column_preferences(self.current_account)
                    if saved_columns:
                        # Filter to only columns that exist in current data
                        self.visible_columns = [col for col in saved_columns if col in self.current_data.columns]
                        if self.visible_columns:
                            self.update_status(f"✅ Loaded {len(self.visible_columns)} saved column preferences")
                
                self.data_info_label.configure(
                    text=f"Data loaded: {rows} rows × {cols} columns | Displaying: {len(self.visible_columns)} column(s)"
                )
                # Enable buttons
                if hasattr(self, 'show_data_btn'):
                    self.show_data_btn.configure(state="normal")
                if hasattr(self, 'clear_data_btn'):
                    self.clear_data_btn.configure(state="normal")
                if hasattr(self, 'config_columns_btn'):
                    self.config_columns_btn.configure(state="normal")
                
                # Update data display
                self.update_data_display()
            else:
                self.data_info_label.configure(text="No data loaded")
                # Disable buttons
                if hasattr(self, 'show_data_btn'):
                    self.show_data_btn.configure(state="disabled")
                if hasattr(self, 'clear_data_btn'):
                    self.clear_data_btn.configure(state="disabled")
                if hasattr(self, 'config_columns_btn'):
                    self.config_columns_btn.configure(state="disabled")
                
                # Clear data display
                self.update_data_display()
    
    def enable_data_actions(self):
        """Enable data action buttons"""
        self.show_data_btn.configure(state="normal")
        self.clear_data_btn.configure(state="normal")
        if hasattr(self, 'config_columns_btn'):
            self.config_columns_btn.configure(state="normal")
    
    def disable_data_actions(self):
        """Disable data action buttons"""
        self.show_data_btn.configure(state="disabled")
        self.clear_data_btn.configure(state="disabled")
        if hasattr(self, 'config_columns_btn'):
            self.config_columns_btn.configure(state="disabled")
    
    def update_status(self, message):
        """Update status bar"""
        self.status_label.configure(text=message)
        self.root.update()
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = OneStopShopMain()
    app.run()
