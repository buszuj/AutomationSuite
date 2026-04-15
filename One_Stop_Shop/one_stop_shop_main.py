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

from pa_template_manager import PATemplateManager
from pa_template_processor import PATemplateProcessor
from quoteme_email_parser import QuoteeMEmailParser, get_parse_cache

# Import the parser UI (from same directory)
from quoteme_parser_ui import create_parser_tab


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
        
        # Setup menu bar BEFORE UI
        self.setup_menu_bar()
        
        self.setup_ui()
    
    def setup_menu_bar(self):
        """Setup menu bar with configuration options"""
        menubar = Menu(self.root, bg="#1f538d", fg="white", activebackground="#2b7dbc", activeforeground="white", font=("Arial", 11, "bold"))
        self.root.config(menu=menubar)
        
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
                    self.update_account_display()
                    self.update_status(f"Active account: {self.current_account}")
                    # Account set as active
                    dialog.destroy()
                    self.refresh_ui()
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
            
            # Create floating window
            parser_window = ctk.CTkToplevel(self.root)
            parser_window.title("QuoteMe Email Parser")
            parser_window.geometry("1000x700")
            parser_window.transient(self.root)
            parser_window.attributes('-topmost', True)
            parser_window.after(100, lambda: parser_window.attributes('-topmost', False))
            
            try:
                # Create parser tab
                parser_tab = create_parser_tab(parser_window, on_apply_callback=on_parser_apply)
                
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
        """Launch Service Mapper in modal mode"""
        try:
            launch_path = Path(__file__).parent / "launch_service_mapper.py"
            
            if not launch_path.exists():
                messagebox.showerror("Error", "Service Mapper not found")
                return
            
            # Run as subprocess
            subprocess.Popen([sys.executable, str(launch_path)])
            self.root.after(500, self.refresh_ui)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Service Mapper: {str(e)}")
    
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
        
        # Create tabs - Data View first, then QuoteMe, PA Integration and Configuration,
        self.setup_data_view_tab()
        self.setup_quoteme_parser_tab()
        self.setup_pa_integration_tab()
        self.setup_configuration_tab()
        
        # Initially hide tabs until account is selected
        if not self.current_account:
            self.main_tabs.pack_forget()
    
    def setup_data_view_tab(self):
        """Setup Data View tab - shows imported/pulled data with configuration options"""
        data_tab = self.main_tabs.add("Data View")
        
        data_content = ctk.CTkFrame(data_tab, fg_color="transparent")
        data_content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(data_content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            header_frame,
            text="📊 Data View",
            font=("Arial", 18, "bold")
        ).pack(side="left", pady=(0, 10))
        
        # Data info label
        self.data_info_label = ctk.CTkLabel(
            header_frame,
            text="No data loaded",
            font=("Arial", 11),
            text_color="gray"
        )
        self.data_info_label.pack(side="left", padx=20)
        
        # Configure Columns button
        self.config_columns_btn = ctk.CTkButton(
            header_frame,
            text="⚙️ Configure Columns",
            command=self.configure_visible_columns,
            width=180,
            height=35,
            font=("Arial", 11, "bold"),
            fg_color="#9b59b6",
            hover_color="#8e44ad",
            state="disabled"
        )
        self.config_columns_btn.pack(side="right")
        
        # Data display scrollable area
        self.data_display_scroll = ctk.CTkScrollableFrame(data_content, fg_color="transparent")
        self.data_display_scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initial message
        self.no_data_label = ctk.CTkLabel(
            self.data_display_scroll,
            text="No data loaded\n\nPull data from GLE API or import job data using the buttons in the banner above",
            font=("Arial", 12),
            text_color="gray"
        )
        self.no_data_label.pack(expand=True, pady=50)
    
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

        try:
            create_parser_tab(parser_tab, on_apply_callback=on_parser_apply)
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
