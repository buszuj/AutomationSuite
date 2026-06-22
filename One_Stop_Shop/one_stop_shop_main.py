"""
One Stop Shop - Main GUI
Central hub for job data import and GLE API integration
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, Menu, BooleanVar
import tkinterdnd2 as tkdnd
import pandas as pd
import requests
import json
from pathlib import Path
import sys
import subprocess
import importlib.util
import importlib
import os
from datetime import datetime
from typing import List, Optional

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
try:
    from Rate_Card_Builder.excel_rate_card_loader import load_excel_rate_card
except ImportError:
    load_excel_rate_card = None

# Import the parser UI (from same directory)
from quoteme_parser_ui import create_parser_tab

# Import Rate Card Builder integrated component
try:
    from Rate_Card_Builder.rate_card_builder_integrated import setup_rate_cards_tab
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
        self._ensure_tpus_canonical_services()
        
        # QuoteMe Value Mapper for word count field mapping
        self.quoteme_value_mapper = QuoteMeValueMapper()
        
        # Rate card and workflow tracking
        self.selected_workflow = None
        self.selected_rate_card = None
        self.service_mapping_conflicts = {}  # Stores conflict report for the currently loaded rate card
        self.cached_rate_card = None  # Cache normalized rate card to persist across workflow changes
        self.quoteme_data = None  # Stores parsed QuoteMe data
        self.language_pairs = []  # Language pairs from QuoteMe
        self.source_type_var = ctk.StringVar(value="Dead Source")  # Live Source or Dead Source
        self.workflow_service_data = {}  # Stores service data: {service_name: {lp: {quantity, rate}}}
        self.selected_entity_var = ctk.StringVar(value="TPUS")
        self.entity_dropdown = None
        
        # Setup menu bar BEFORE UI
        self.setup_menu_bar()
        
        self.setup_ui()

    def _load_pa_services(self):
        """Load PA_SERVICES from WF_Matrix with a safe fallback."""
        try:
            from WF_Matrix import PA_SERVICES
            return PA_SERVICES
        except Exception as e:
            print(f"[DEBUG] Could not load PA_SERVICES: {e}")
            return {}

    def _infer_default_uom(self, service_name: str) -> str:
        """Best-effort UofM default for canonical services not yet present in TPUS."""
        lower = service_name.lower()
        if "fee" in lower or "courier" in lower or "rush" in lower or "notary" in lower or "apostille" in lower or "certification" in lower:
            return "Fee"
        if "desktop" in lower or "format" in lower or "review" in lower or "reconciliation" in lower or "proof" in lower or "editing" in lower or "management" in lower or "assessment" in lower or "engineering" in lower:
            return "Hour"
        return "Word"

    def _persist_tpus_services_to_wf_matrix(self, tpus_rows: list):
        """Persist TPUS_PA_SERVICES block in Core/WF_Matrix.py."""
        wf_path = Path(__file__).parent.parent / "Core" / "WF_Matrix.py"
        if not wf_path.exists():
            return

        marker = "TPUS_PA_SERVICES = ["
        with open(wf_path, "r", encoding="utf-8") as f:
            text = f.read()

        start = text.find(marker)
        if start == -1:
            return

        open_idx = text.find("[", start)
        if open_idx == -1:
            return

        depth = 0
        end_idx = -1
        for i in range(open_idx, len(text)):
            ch = text[i]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    end_idx = i
                    break

        if end_idx == -1:
            return

        new_block_lines = ["TPUS_PA_SERVICES = ["]
        for row in tpus_rows:
            safe_row = row[:4] if isinstance(row, list) else ["", "", "", ""]
            while len(safe_row) < 4:
                safe_row.append("")
            new_block_lines.append(f"    {repr(safe_row)},")
        new_block_lines.append("]")
        new_block = "\n".join(new_block_lines)

        updated_text = text[:start] + new_block + text[end_idx + 1:]
        with open(wf_path, "w", encoding="utf-8") as f:
            f.write(updated_text)

    def _ensure_tpus_canonical_services(self):
        """Ensure TPUS contains all canonical services and persist it for Entity Manager usage."""
        try:
            import WF_Matrix
            importlib.reload(WF_Matrix)

            pa_services = WF_Matrix.PA_SERVICES
            canonical_services = self.service_mapper.canonical_services or []
            if not canonical_services:
                return

            current_tpus = pa_services.get("TPUS", [])
            header = ["Service Group 1", "Service Group 2", "Service", "Default UofM"]
            if current_tpus and isinstance(current_tpus[0], list) and len(current_tpus[0]) >= 4:
                header = current_tpus[0][:4]

            existing_by_service = {}
            for row in current_tpus[1:]:
                if isinstance(row, list) and len(row) >= 4:
                    svc = str(row[2]).strip()
                    if svc:
                        existing_by_service[svc] = row[:4]

            canonical_rows = [header]
            for svc in canonical_services:
                if svc in existing_by_service:
                    canonical_rows.append(existing_by_service[svc])
                else:
                    canonical_rows.append([
                        "Language Services",
                        "Translation",
                        svc,
                        self._infer_default_uom(svc)
                    ])

            # Update in-memory and persist to file so Entity Manager reload sees canonical TPUS.
            WF_Matrix.PA_SERVICES["TPUS"] = canonical_rows
            self._persist_tpus_services_to_wf_matrix(canonical_rows)

            # Ensure every existing entity also contains all TPUS services.
            # This keeps legacy entities aligned with canonical service coverage.
            importlib.reload(WF_Matrix)
            import sync_entities
            importlib.reload(sync_entities)
            sync_entities.sync_all_entities_to_master()
            importlib.reload(WF_Matrix)
        except Exception as e:
            print(f"[DEBUG] Failed to enforce TPUS canonical services: {e}")

    def _get_available_entities(self):
        """Get available entities with TPUS first if present."""
        pa_services = self._load_pa_services()
        entities = sorted(pa_services.keys())
        if "TPUS" in entities:
            entities.remove("TPUS")
            entities.insert(0, "TPUS")
        return entities

    def _refresh_entity_dropdown(self):
        """Refresh Job Data entity dropdown values from WF_Matrix."""
        if not self.entity_dropdown:
            return

        entities = self._get_available_entities()
        current = self.selected_entity_var.get().strip()
        if not current or current not in entities:
            current = "TPUS" if "TPUS" in entities else (entities[0] if entities else "")

        self.entity_dropdown.configure(values=entities)
        self.selected_entity_var.set(current)
        if current:
            self.entity_dropdown.set(current)

    def _on_job_entity_changed(self, _choice=None):
        """Re-render services table when Job Data entity selection changes."""
        try:
            self._refresh_entity_dropdown()
            if self.selected_workflow and self.current_account:
                services = self.account_workflow_manager.get_workflow_services(
                    self.current_account,
                    self.selected_workflow
                )
                self.populate_services_table(services)
        except Exception as e:
            print(f"[DEBUG] Failed to refresh services on entity change: {e}")

    def _get_display_service_name(self, canonical_service: str) -> str:
        """Get service name to display in Services by LP for selected entity."""
        entity_name = self.selected_entity_var.get().strip() if hasattr(self, "selected_entity_var") else "TPUS"
        if not entity_name:
            entity_name = "TPUS"

        try:
            from entity_service_mapper import EntityServiceMapper
            entity_mapper = EntityServiceMapper()
            return self._resolve_service_for_entity(canonical_service, entity_name, entity_mapper)
        except Exception as e:
            print(f"[DEBUG] Display name resolution failed for {canonical_service}: {e}")
            return canonical_service

    def _get_entity_service_profile(self, entity_name: str):
        """
        Build lookup of service metadata for an entity.

        Returns dict keyed by exact service name with values:
        {"group1": str, "group2": str, "uom": str}
        """
        pa_services = self._load_pa_services()
        rows = pa_services.get(entity_name, [])
        profile = {}

        for row in rows[1:]:
            if not isinstance(row, list) or len(row) < 4:
                continue
            service_name = str(row[2]).strip()
            if not service_name:
                continue
            profile[service_name] = {
                "group1": str(row[0]).strip() if row[0] is not None else "",
                "group2": str(row[1]).strip() if row[1] is not None else "",
                "uom": str(row[3]).strip() if row[3] is not None else ""
            }

        return profile

    def _resolve_service_for_entity(self, canonical_service: str, entity_name: str, entity_mapper):
        """
        Resolve canonical service name to the selected entity's visible service name.
        Priority:
        1) TPUS canonical (identity)
        2) EntityServiceMapper reverse mapping
        3) ServiceMapper entity aliases
        4) Canonical fallback
        """
        if not entity_name or entity_name == "TPUS":
            return canonical_service

        entity_service = None
        try:
            entity_service = entity_mapper.get_reverse_mapping(entity_name, canonical_service)
        except Exception as e:
            print(f"[DEBUG] Failed reverse mapping for {canonical_service} -> {entity_name}: {e}")

        if entity_service:
            return entity_service

        try:
            aliases = self.service_mapper.load_entity_service_aliases(entity_name)
            alias_name = aliases.get(canonical_service, "")
            if alias_name:
                return alias_name
        except Exception as e:
            print(f"[DEBUG] Failed alias lookup for {canonical_service} in {entity_name}: {e}")

        return canonical_service
    
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
        
        # Appearance menu
        appearance_menu = Menu(menubar, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#1f538d", activeforeground="white", font=("Arial", 10))
        menubar.add_cascade(label="  Appearance  ", menu=appearance_menu)
        
        # Track current theme mode
        self.current_theme = "dark"
        
        def toggle_theme():
            """Toggle between dark and light mode"""
            if self.current_theme == "dark":
                ctk.set_appearance_mode("light")
                self.current_theme = "light"
                appearance_menu.entryconfig("🌙 Dark Mode", label="🌞 Light Mode")
                print("[DEBUG] Switched to light mode")
            else:
                ctk.set_appearance_mode("dark")
                self.current_theme = "dark"
                appearance_menu.entryconfig("🌞 Light Mode", label="🌙 Dark Mode")
                print("[DEBUG] Switched to dark mode")
        
        appearance_menu.add_command(label="🌙 Dark Mode", command=toggle_theme)
        
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
    
    def _refresh_account_list_ui(self):
        """Refresh the account list in the startup screen"""
        try:
            # Clear existing widgets
            for widget in self.account_list_frame.winfo_children():
                widget.destroy()
            
            # Load accounts
            accounts = self.account_workflow_manager.get_accounts()
            
            if not accounts:
                ctk.CTkLabel(
                    self.account_list_frame,
                    text="No accounts found.\nClick 'Create New' to get started.",
                    text_color="orange",
                    font=("Arial", 12),
                    justify="left"
                ).pack(pady=20)
            else:
                for account in accounts:
                    radio = ctk.CTkRadioButton(
                        self.account_list_frame,
                        text=account,
                        variable=self.selected_account_var,
                        value=account,
                        font=("Arial", 12),
                        text_color="white"
                    )
                    radio.pack(anchor="w", padx=15, pady=8)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load accounts: {str(e)}")
    
    def _switch_account(self):
        """Switch back to account selection screen"""
        self.current_account = None
        self.selected_rate_card = None
        self.cached_rate_card = None
        self.update_account_display()
        self.update_status("Account selection mode")
    
    def _select_account_from_ui(self):
        """Select account from the startup screen"""
        selected = self.selected_account_var.get()
        print(f"[DEBUG] _select_account_from_ui called - selected: {selected}")
        if not selected:
            messagebox.showwarning("No Selection", "Please select an account")
            return
        
        print(f"[DEBUG] Setting current_account to: {selected}")
        self.current_account = selected
        print(f"[DEBUG] Cleared rate card cache")
        # Clear rate card cache when account changes
        self.selected_rate_card = None
        self.cached_rate_card = None
        
        print(f"[DEBUG] Calling update_account_display()")
        self.update_account_display()
        
        print(f"[DEBUG] Calling update_status()")
        self.update_status(f"Active account: {self.current_account}")
        
        print(f"[DEBUG] Calling refresh_ui()")
        self.refresh_ui()
        
        print(f"[DEBUG] Calling refresh_workflow_dropdown()")
        self.refresh_workflow_dropdown()
        
        print(f"[DEBUG] Calling refresh_rate_card_dropdown()")
        self.refresh_rate_card_dropdown()
        
        print(f"[DEBUG] Account selection complete")
    
    def _create_account_from_ui(self):
        """Create a new account from startup screen"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Create New Account")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (200 // 2)
        dialog.geometry(f'400x200+{x}+{y}')
        
        ctk.CTkLabel(dialog, text="Enter Account Name:", font=("Arial", 12, "bold")).pack(pady=(20, 10))
        name_entry = ctk.CTkEntry(dialog, width=300, font=("Arial", 12), placeholder_text="e.g., Client A")
        name_entry.pack(pady=10)
        name_entry.focus()
        
        def create():
            account_name = name_entry.get().strip()
            if not account_name:
                messagebox.showwarning("Invalid Name", "Account name cannot be empty")
                return
            
            try:
                if self.account_workflow_manager.create_account(account_name):
                    dialog.destroy()
                    self._refresh_account_list_ui()
                    self.selected_account_var.set(account_name)

                else:
                    messagebox.showerror("Error", "Account already exists or creation failed")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create account: {str(e)}")
        
        ctk.CTkButton(dialog, text="Create", command=create, width=120, height=32, font=("Arial", 11, "bold")).pack(pady=10)
    
    def _rename_account_from_ui(self):
        """Rename an account from startup screen"""
        old_name = self.selected_account_var.get()
        if not old_name:
            messagebox.showwarning("No Selection", "Please select an account to rename")
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Rename Account")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (200 // 2)
        dialog.geometry(f'400x200+{x}+{y}')
        
        ctk.CTkLabel(dialog, text=f"Rename '{old_name}' to:", font=("Arial", 12, "bold")).pack(pady=(20, 10))
        name_entry = ctk.CTkEntry(dialog, width=300, font=("Arial", 12))
        name_entry.insert(0, old_name)
        name_entry.pack(pady=10)
        name_entry.focus()
        name_entry.select_range(0, len(old_name))
        
        def rename():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showwarning("Invalid Name", "Account name cannot be empty")
                return
            
            try:
                if self.account_workflow_manager.rename_account(old_name, new_name):
                    if self.current_account == old_name:
                        self.current_account = new_name
                    dialog.destroy()
                    self._refresh_account_list_ui()
                    self.selected_account_var.set(new_name)
                    self.update_account_display()
                    messagebox.showinfo("Success", f"Account renamed to '{new_name}'!")
                else:
                    messagebox.showerror("Error", "Account already exists or rename failed")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to rename account: {str(e)}")
        
        ctk.CTkButton(dialog, text="Rename", command=rename, width=120, height=32, font=("Arial", 11, "bold")).pack(pady=10)
    
    def _delete_account_from_ui(self):
        """Delete an account from startup screen"""
        account_name = self.selected_account_var.get()
        if not account_name:
            messagebox.showwarning("No Selection", "Please select an account to delete")
            return
        
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{account_name}'?\n\nThis will delete all workflows and configurations for this account.\n\nThis action cannot be undone."
        )
        
        if not confirm:
            return
        
        try:
            if self.account_workflow_manager.delete_account(account_name):
                if self.current_account == account_name:
                    self.current_account = None
                    self.refresh_ui()
                
                self._refresh_account_list_ui()
                self.selected_account_var.set("")
            else:
                messagebox.showerror("Error", "Failed to delete account")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete account: {str(e)}")
    
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
            self.switch_account_btn.configure(state="normal")  # Enable switch button
            # Show tabs
            if hasattr(self, 'account_prompt') and hasattr(self, 'main_tabs'):
                self.account_prompt.pack_forget()
                self.main_tabs.pack(fill="both", expand=True)  # Pack tabs only when account selected
            # Reload PA Template Mapper with the newly selected account
            self.refresh_pa_integration_tab()
            # Refresh Manage Workflows tab to show workflows for this account
            if hasattr(self, '_manage_workflows_refresh'):
                self._manage_workflows_refresh()
        else:
            self.account_info_label.configure(text="None Selected")
            self.switch_account_btn.configure(state="disabled")  # Disable switch button
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
        """Open service mapping management dialog (singleton – raises existing window if open)."""
        if not self.current_account:
            messagebox.showwarning("Warning", "Please select an account first")
            return
        account_name = str(self.current_account)

        # Singleton guard: bring existing window to front instead of opening another
        if hasattr(self, "_service_mapper_window") and self._service_mapper_window is not None:
            try:
                if self._service_mapper_window.winfo_exists():
                    self._service_mapper_window.lift()
                    self._service_mapper_window.focus_force()
                    return
            except Exception:
                pass
            self._service_mapper_window = None

        dialog = ctk.CTkToplevel(self.root)
        self._service_mapper_window = dialog

        def _on_mapper_close():
            self._service_mapper_window = None
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", _on_mapper_close)
        dialog.title(f"Service Mapper - {account_name}")
        dialog.geometry("700x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Title
        title_label = ctk.CTkLabel(
            dialog,
            text=f"Manage Service Mappings for {account_name}",
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

        # Load account-level conflicts once for this dialog session
        account_conflict_report = self.service_mapper.detect_account_mapping_conflicts(account_name)
        account_conflicts = account_conflict_report.get("conflicts", {})
        
        def on_rate_card_select(rc_name: str):
            """Update mappings display when rate card is selected, including conflict details."""
            # Clear current mappings display
            for widget in scroll_frame.winfo_children():
                widget.destroy()
            
            if not rc_name:
                return

            clean_rc_name = rc_name.replace("[Master] ", "").strip()

            # Show conflicts related to this selected rate card
            related_conflicts = []
            for alias_norm, conflict_data in account_conflicts.items():
                sources = conflict_data.get("sources", [])
                if any(str(src.get("rate_card", "")).strip() == clean_rc_name for src in sources):
                    related_conflicts.append((alias_norm, conflict_data))

            if related_conflicts:
                conflict_banner = ctk.CTkFrame(scroll_frame, fg_color="#5a2a2a", corner_radius=6)
                conflict_banner.pack(fill="x", pady=(0, 10), padx=2)

                ctk.CTkLabel(
                    conflict_banner,
                    text=f"⚠ {len(related_conflicts)} alias conflict(s) involve this rate card",
                    font=("Arial", 11, "bold"),
                    text_color="#ffd6d6",
                    anchor="w"
                ).pack(fill="x", padx=10, pady=(8, 4))

                ctk.CTkLabel(
                    conflict_banner,
                    text="Same alias is mapped to different canonical services across saved mappings.",
                    font=("Arial", 10),
                    text_color="#ffd6d6",
                    anchor="w",
                    wraplength=620,
                    justify="left"
                ).pack(fill="x", padx=10, pady=(0, 8))

                for alias_norm, conflict_data in sorted(related_conflicts, key=lambda x: x[0]):
                    alias_variants = ", ".join(conflict_data.get("alias_variants", []))
                    canonical_targets = " | ".join(conflict_data.get("canonical_services", []))
                    cards = sorted({
                        str(src.get("rate_card", ""))
                        for src in conflict_data.get("sources", [])
                        if src.get("rate_card")
                    })

                    item = ctk.CTkFrame(scroll_frame, fg_color="#4a2323", corner_radius=5)
                    item.pack(fill="x", pady=4, padx=4)

                    ctk.CTkLabel(
                        item,
                        text=f"Alias: {alias_variants or alias_norm}",
                        font=("Arial", 10, "bold"),
                        text_color="#ffd6d6",
                        anchor="w"
                    ).pack(fill="x", padx=10, pady=(7, 2))

                    ctk.CTkLabel(
                        item,
                        text=f"Canonical targets: {canonical_targets}",
                        font=("Arial", 10),
                        text_color="#ffd6d6",
                        anchor="w",
                        wraplength=620,
                        justify="left"
                    ).pack(fill="x", padx=10, pady=2)

                    ctk.CTkLabel(
                        item,
                        text=f"Seen in rate cards: {', '.join(cards)}",
                        font=("Arial", 9),
                        text_color="#ffb3b3",
                        anchor="w",
                        wraplength=620,
                        justify="left"
                    ).pack(fill="x", padx=10, pady=(2, 7))
            
            # Load mappings for this rate card
            mappings = self.service_mapper.load_mapping(account_name, clean_rc_name)
            
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
            command=_on_mapper_close,
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
            if spec is None or spec.loader is None:
                messagebox.showerror(
                    "Automation Error",
                    f"Failed to load KickOff module spec from:\n{kickoff_path}"
                )
                return
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
    
    def pull_glp_data_from_entry(self):
        """Pull GLP data using the job ID from the entry field"""
        job_id = self.glp_entry.get().strip()
        
        if not job_id:
            messagebox.showwarning("Missing Input", "Please enter a Job ID in the GLP entry field")
            return
        
        try:
            self.update_status("Fetching data from GLP API...")
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
            self.update_status(f"✅ GLP data pulled for Job ID: {job_id}")
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
            messagebox.showerror("Error", f"Failed to pull GLP data:\n{str(e)}")
            self.update_status("❌ Failed to pull GLP data")


    

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
        
        # Switch Account button
        self.switch_account_btn = ctk.CTkButton(
            account_row,
            text="🔄 Switch Account",
            command=self._switch_account,
            width=140,
            height=28,
            font=("Arial", 10),
            fg_color="#8e44ad",
            hover_color="#7d3f88",
            state="disabled"  # Enabled only when account is selected
        )
        self.switch_account_btn.pack(side="left", padx=(0, 10))
        
        # Center section - GLP API Pull
        center_section = ctk.CTkFrame(banner_frame, fg_color="transparent")
        center_section.pack(side="left", fill="y", padx=15, pady=10)
        
        
        glp_row = ctk.CTkFrame(center_section, fg_color="transparent")
        glp_row.pack(fill="x", pady=(5, 0))
        
        self.glp_entry = ctk.CTkEntry(
            glp_row,
            placeholder_text="Enter GLP JOB ID...",
            width=200,
            height=28,
            font=("Arial", 10)
        )
        self.glp_entry.pack(side="left", padx=(0, 8))
        self.glp_entry.bind("<Return>", lambda e: self.pull_glp_data_from_entry())

        ctk.CTkButton(
            glp_row,
            text="Pull GLP Data",
            command=self.pull_glp_data_from_entry,
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
        
        # Account selection prompt - now with full management UI (shows when no account selected)
        self.account_prompt = ctk.CTkFrame(self.tabs_container, fg_color="#34495e", corner_radius=15)
        self.account_prompt.pack(fill="both", expand=True, padx=20, pady=50)
        
        prompt_content = ctk.CTkFrame(self.account_prompt, fg_color="transparent")
        prompt_content.pack(fill="both", expand=True, padx=40, pady=30)
        
        # Title section
        title_frame = ctk.CTkFrame(prompt_content, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 30))
        
        ctk.CTkLabel(
            title_frame,
            text="🏢 Manage Accounts",
            font=("Arial", 28, "bold"),
            text_color="white"
        ).pack(side="left")
        
        ctk.CTkLabel(
            title_frame,
            text="Select, create, or manage your accounts",
            font=("Arial", 12),
            text_color="#95a5a6"
        ).pack(side="left", padx=(20, 0))
        
        # Content: Two columns - left for list, right for buttons
        content_row = ctk.CTkFrame(prompt_content, fg_color="transparent")
        content_row.pack(fill="both", expand=True)
        content_row.grid_columnconfigure(0, weight=2)  # Account list gets 2x space
        content_row.grid_columnconfigure(1, weight=1)  # Buttons get 1x space
        
        # LEFT: Account list
        list_section = ctk.CTkFrame(content_row, fg_color="transparent")
        list_section.grid(row=0, column=0, sticky="nsew", padx=(0, 30))
        
        ctk.CTkLabel(
            list_section,
            text="Available Accounts",
            font=("Arial", 14, "bold"),
            text_color="white"
        ).pack(anchor="w", pady=(0, 15))
        
        # Scrollable account list
        self.account_list_frame = ctk.CTkScrollableFrame(
            list_section,
            fg_color="#2c3e50",
            corner_radius=8,
            height=300
        )
        self.account_list_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        self.selected_account_var = ctk.StringVar(value=self.current_account or "")
        self._refresh_account_list_ui()
        
        # RIGHT: Action buttons
        button_section = ctk.CTkFrame(content_row, fg_color="transparent")
        button_section.grid(row=0, column=1, sticky="n", padx=(30, 0))
        
        ctk.CTkLabel(
            button_section,
            text="Actions",
            font=("Arial", 14, "bold"),
            text_color="white"
        ).pack(anchor="w", pady=(0, 15))
        
        # Select Account button
        ctk.CTkButton(
            button_section,
            text="✅ Select",
            command=self._select_account_from_ui,
            width=140,
            height=36,
            font=("Arial", 11, "bold"),
            fg_color="#27ae60",
            hover_color="#229954"
        ).pack(fill="x", pady=5)
        
        # Create New button
        ctk.CTkButton(
            button_section,
            text="➕ Create New",
            command=self._create_account_from_ui,
            width=140,
            height=36,
            font=("Arial", 11, "bold"),
            fg_color="#3498db",
            hover_color="#2980b9"
        ).pack(fill="x", pady=5)
        
        # Rename button
        ctk.CTkButton(
            button_section,
            text="✏️  Rename",
            command=self._rename_account_from_ui,
            width=140,
            height=36,
            font=("Arial", 11),
            fg_color="#f39c12",
            hover_color="#e67e22"
        ).pack(fill="x", pady=5)
        
        # Delete button
        ctk.CTkButton(
            button_section,
            text="🗑️  Delete",
            command=self._delete_account_from_ui,
            width=140,
            height=36,
            font=("Arial", 11),
            fg_color="#e74c3c",
            hover_color="#c0392b"
        ).pack(fill="x", pady=5)
        
        # Tabbed interface (created but NOT packed initially - fixes startup lag)
        self.main_tabs = ctk.CTkTabview(self.tabs_container)
        # DO NOT PACK HERE - let tabs build offscreen, pack only when account selected
        
        # Create tabs - Data View first, then QuoteMe, PA Integration, Rate Cards, and Configuration
        # These build in memory without rendering since main_tabs is not packed
        self.setup_data_view_tab()
        self.setup_quoteme_parser_tab()
        self.setup_pa_integration_tab()
        self.setup_rate_cards_tab()
        self.setup_configuration_tab()
    
    def setup_data_view_tab(self):
        """Setup Job Data tab - split layout with data preview (25%) and workflow services (75%)"""
        data_tab = self.main_tabs.add("Job Data")
        
        # Main container with grid layout - now resizable
        main_container = ctk.CTkFrame(data_tab, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left pane starts minimised; user can expand via the separator drag
        main_container.grid_columnconfigure(0, weight=0, minsize=8)   # Collapsed by default
        main_container.grid_columnconfigure(2, weight=1, minsize=300)  # Right pane takes all space
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
            total_width = main_container.winfo_width()
            pointer_x = event.x_root
            # Use winfo_rootx() for correct screen-to-widget coordinate mapping
            left_width = pointer_x - main_container.winfo_rootx()
            
            # Clamp to sensible limits
            if left_width < 8:
                left_width = 8
            right_width = total_width - left_width - separator.winfo_width()
            if right_width < 300:
                return  # Don't shrink right pane below minimum
            # Drive sizes directly via minsize so there is no weight-ratio jump
            main_container.grid_columnconfigure(0, weight=0, minsize=left_width)
            main_container.grid_columnconfigure(2, weight=0, minsize=right_width)
        
        separator.bind("<B1-Motion>", on_separator_drag)
        separator.configure(cursor="sb_h_double_arrow")
        
        # ─── RIGHT PANE: Workflow Services (75%) ────────────────────────────────────
        right_pane = ctk.CTkFrame(main_container, fg_color="gray20", corner_radius=10)
        right_pane.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        right_pane.grid_columnconfigure(0, weight=1)
        right_pane.grid_rowconfigure(4, weight=1)  # Services table gets remaining space
        
        # Right pane header
        right_header = ctk.CTkFrame(right_pane, fg_color="transparent")
        right_header.grid(row=0, column=0, sticky="ew", padx=15, pady=(5, 3))
        
        header_left = ctk.CTkFrame(right_header, fg_color="transparent")
        header_left.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            header_left,
            text="⚙️ Job Charges",
            font=("Arial", 14, "bold")
        ).pack(anchor="w")
        
        # Workflow selector section
        wf_frame = ctk.CTkFrame(right_pane, fg_color="transparent")
        wf_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=10)

        # Entity selector (global across account/workflow)
        entity_values = self._get_available_entities()
        default_entity = "TPUS" if "TPUS" in entity_values else (entity_values[0] if entity_values else "")
        self.selected_entity_var.set(default_entity)

        self.entity_dropdown = ctk.CTkComboBox(
            wf_frame,
            values=entity_values,
            variable=self.selected_entity_var,
            command=self._on_job_entity_changed,
            state="readonly",
            font=("Arial", 10),
            height=32,
            width=130
        )
        self.entity_dropdown.pack(side="left", padx=(0, 10))
        if default_entity:
            self.entity_dropdown.set(default_entity)
        
        self.workflow_dropdown = ctk.CTkComboBox(
            wf_frame,
            values=[],
            command=self.on_workflow_selected,
            state="readonly",
            font=("Arial", 11),
            height=32
        )
        self.workflow_dropdown.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.workflow_dropdown.set("Choose Workflow...")
        
        # Source Type Selector (on same row as workflow dropdown)
        self.source_type_dropdown = ctk.CTkComboBox(
            wf_frame,
            values=["Live Source", "Dead Source"],
            variable=self.source_type_var,
            command=self._on_source_type_changed,
            state="readonly",
            font=("Arial", 10),
            height=32,
            width=150
        )
        self.source_type_dropdown.pack(side="left", padx=(0, 0))

        # Keep entities list fresh in case Manage Entities changed WF_Matrix in-session
        self._refresh_entity_dropdown()
        
        # Rate card selector section
        rc_frame = ctk.CTkFrame(right_pane, fg_color="transparent")
        rc_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=10)
        
        # Top row: Rate card dropdown and Browse button
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
        self.rate_card_dropdown.set("Select Rate Card...")
        
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
        
        # Currency section (Native Currency + Target Currency + Conversion Rate)
        currency_frame = ctk.CTkFrame(rc_frame, fg_color="transparent")
        currency_frame.pack(fill="x", pady=(5, 0))
        
        # Native Currency (read-only label - from rate card)
        native_currency_frame = ctk.CTkFrame(currency_frame, fg_color="transparent")
        native_currency_frame.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            native_currency_frame,
            text="Native Currency:",
            font=("Arial", 10)
        ).pack(anchor="w")
        
        self.native_currency_label = ctk.CTkLabel(
            native_currency_frame,
            text="USD",
            font=("Arial", 10, "bold"),
            text_color="#3498db"
        )
        self.native_currency_label.pack(fill="x", pady=(3, 0))
        
        # Target Currency (editable dropdown - for conversion)
        target_currency_frame = ctk.CTkFrame(currency_frame, fg_color="transparent")
        target_currency_frame.pack(side="left", padx=(10, 0))
        
        ctk.CTkLabel(
            target_currency_frame,
            text="Target Currency:",
            font=("Arial", 10)
        ).pack(anchor="w")
        
        self.target_currency_dropdown = ctk.CTkComboBox(
            target_currency_frame,
            values=["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR", "MXN", "BRL"],
            state="readonly",
            font=("Arial", 10),
            height=28,
            width=80,
            command=self._on_target_currency_changed
        )
        self.target_currency_dropdown.set("USD")
        self.target_currency_dropdown.pack(fill="x", pady=(3, 0))
        
        # Conversion rate input
        rate_label_frame = ctk.CTkFrame(currency_frame, fg_color="transparent")
        rate_label_frame.pack(side="left", padx=(10, 0))
        
        ctk.CTkLabel(
            rate_label_frame,
            text="Conversion Rate:",
            font=("Arial", 10)
        ).pack(anchor="w")
        
        self.conversion_rate_entry = ctk.CTkEntry(
            rate_label_frame,
            placeholder_text="1.0",
            font=("Arial", 10),
            width=80,
            height=28
        )
        self.conversion_rate_entry.delete(0, "end")
        self.conversion_rate_entry.insert(0, "1.0")
        self.conversion_rate_entry.pack(fill="x", pady=(3, 0))
        
        # Save conversion rate button
        ctk.CTkButton(
            currency_frame,
            text="💾 Save",
            command=self._save_currency_and_recalculate,
            width=70,
            height=28,
            font=("Arial", 9, "bold"),
            fg_color="#3498db",
            hover_color="#2980b9"
        ).pack(side="left", padx=(10, 0), pady=(16, 0))
        
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
        # Services table label with Service Config button (moved to row 3 since Source Type is now with Workflow)
        table_label_frame = ctk.CTkFrame(right_pane, fg_color="transparent")
        table_label_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=(15, 5))
        
        ctk.CTkLabel(
            table_label_frame,
            text="Services by Language Pair:",
            font=("Arial", 11, "bold")
        ).pack(side="left", expand=True, anchor="w")
        
        # Manual WC button
        ctk.CTkButton(
            table_label_frame,
            text="📝 Manual WC",
            command=self._show_manual_wc_dialog,
            width=100,
            height=28,
            font=("Arial", 9, "bold"),
            fg_color="#e67e22",
            hover_color="#d35400"
        ).pack(side="right", padx=(5, 0))
        
        # Service Config button
        ctk.CTkButton(
            table_label_frame,
            text="⚙️ Service Config",
            command=self._open_service_config_dialog,
            width=140,
            height=28,
            font=("Arial", 9, "bold"),
            fg_color="#8e44ad",
            hover_color="#7d3ba0"
        ).pack(side="right", padx=(5, 0))
        
        # Rates Config button (for Min Fee thresholds)
        ctk.CTkButton(
            table_label_frame,
            text="💰 Rates Config",
            command=self.open_min_fee_editor,
            width=140,
            height=28,
            font=("Arial", 9, "bold"),
            fg_color="#16a085",
            hover_color="#138870"
        ).pack(side="right", padx=(5, 0))
        
        # Create scrollable table frame
        self.services_table_frame = ctk.CTkScrollableFrame(
            right_pane,
            fg_color="gray25",
            corner_radius=5
        )
        self.services_table_frame.grid(row=4, column=0, sticky="nsew", padx=15, pady=(0, 15))
        
        # Enable mousewheel scrolling on the services table
        def _stf_scroll(event):
            self.services_table_frame._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self._services_table_scroll_handler = _stf_scroll
        self.services_table_frame.bind("<MouseWheel>", _stf_scroll)
        self.services_table_frame._parent_canvas.bind("<MouseWheel>", _stf_scroll)
        
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
        
        # Rush rate entry frame (below services table)
        rush_frame = ctk.CTkFrame(right_pane, fg_color="transparent")
        rush_frame.grid(row=5, column=0, sticky="ew", padx=15, pady=(5, 5))
        
        ctk.CTkLabel(
            rush_frame,
            text="Rush Rate (%):",
            font=("Arial", 9)
        ).pack(side="left", padx=(0, 5))
        
        self.rush_rate_entry = ctk.CTkEntry(
            rush_frame,
            width=80,
            height=28,
            font=("Arial", 9),
            placeholder_text="e.g., 15"
        )
        self.rush_rate_entry.pack(side="left", padx=(0, 10))
        self.rush_rate_entry.bind("<FocusOut>", self._on_rush_rate_changed)
        self.rush_rate_entry.bind("<Return>", self._on_rush_rate_changed)
        
        ctk.CTkLabel(
            rush_frame,
            text="(Session-only, automatically adds Rush Premium fee)",
            font=("Arial", 8),
            text_color="gray"
        ).pack(side="left")
        
        # Cache for calculated quantities (from QuoteMe data)
        # Used to restore original values when recalculating min fees
        # Structure: {service_name: {lp: calculated_quantity_value}}
        self.calculated_quantities_cache = {}
        
        # Rush Premium tracking (session-only, not persisted)
        self.rush_rate_value = None  # Float representing percentage (e.g., 15.0 for 15%)
        
        # Manual WC data storage (can be merged with QuoteMe data)
        self.manual_wc_data = {}  # Structure: {lp_name: {field_name: value}}
        
        # Export Charges button section
        export_frame = ctk.CTkFrame(right_pane, fg_color="transparent")
        export_frame.grid(row=6, column=0, sticky="ew", padx=15, pady=(10, 15))
        
        ctk.CTkButton(
            export_frame,
            text="📊 Export Charges to CSV",
            command=self.export_charges_to_csv,
            height=35,
            font=("Arial", 11, "bold"),
            fg_color="#9b59b6",
            hover_color="#8e44ad"
        ).pack(fill="x")
    
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
            EntityManagerGUI(frame=entities_tab, on_entity_change=self._refresh_entity_dropdown)
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
            entity_names = sorted(PA_SERVICES.keys())
            if "TPUS" in entity_names:
                entity_names.remove("TPUS")
                entity_names.insert(0, "TPUS")
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
            """Load and display canonical service mappings for selected entity"""
            # Clear previous mapping UI
            for widget in mapping_container.winfo_children():
                widget.destroy()
            entity = entity_var.get()
            if not entity:
                return
            
            try:
                import sys
                sys.path.insert(0, str(Path(__file__).parent.parent / "Core"))
                from service_mapper import ServiceMapper
                
                mapper = ServiceMapper()
                canonical_services = mapper.canonical_services
                aliases = mapper.load_entity_service_aliases(entity)
                
                if not canonical_services:
                    ctk.CTkLabel(
                        mapping_container,
                        text="⚠️ No canonical services found",
                        font=("Arial", 12),
                        text_color="#e74c3c"
                    ).pack(expand=True, pady=30)
                    return
                
                # Header with info and add button
                header_frame = ctk.CTkFrame(mapping_container, fg_color="transparent")
                header_frame.pack(fill="x", padx=15, pady=(15, 10))
                
                title_label = ctk.CTkLabel(
                    header_frame,
                    text=f"Canonical Services - Map {entity} Equivalents",
                    font=("Arial", 13, "bold")
                )
                title_label.pack(side="left", anchor="w")
                
                info_label = ctk.CTkLabel(
                    header_frame,
                    text=f"{len(aliases)} / {len(canonical_services)} mapped",
                    font=("Arial", 11),
                    text_color="#95a5a6"
                )
                info_label.pack(side="left", padx=(20, 0), anchor="w")
                
                # Button to add new service
                def add_new_service():
                    dialog = ctk.CTkToplevel(self.root)
                    dialog.title("Add New Canonical Service")
                    dialog.geometry("450x250")
                    dialog.transient(self.root)
                    dialog.grab_set()
                    
                    # Center dialog
                    dialog.update_idletasks()
                    x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
                    y = (dialog.winfo_screenheight() // 2) - (250 // 2)
                    dialog.geometry(f'450x250+{x}+{y}')
                    
                    ctk.CTkLabel(
                        dialog,
                        text="Create New Canonical Service",
                        font=("Arial", 13, "bold")
                    ).pack(pady=(15, 5), padx=15)
                    
                    # Canonical service name
                    ctk.CTkLabel(
                        dialog,
                        text="Canonical Service Name:",
                        font=("Arial", 11)
                    ).pack(anchor="w", padx=15, pady=(10, 0))
                    
                    canonical_entry = ctk.CTkEntry(dialog, font=("Arial", 11), width=400)
                    canonical_entry.pack(padx=15, pady=(0, 10))
                    canonical_entry.focus()
                    
                    # Entity-specific alias
                    ctk.CTkLabel(
                        dialog,
                        text=f"{entity} Equivalent Name (Optional):",
                        font=("Arial", 11)
                    ).pack(anchor="w", padx=15, pady=(5, 0))
                    
                    alias_entry = ctk.CTkEntry(dialog, font=("Arial", 11), width=400)
                    alias_entry.pack(padx=15, pady=(0, 15))
                    
                    # Buttons
                    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
                    btn_frame.pack(fill="x", padx=15, pady=10)
                    
                    def save_new_service():
                        canonical_name = canonical_entry.get().strip()
                        alias_name = alias_entry.get().strip()
                        
                        if not canonical_name:
                            messagebox.showwarning("Required", "Please enter a canonical service name")
                            return
                        
                        # Add to canonical services
                        if mapper.add_canonical_service(canonical_name):
                            # If alias provided, set it
                            if alias_name:
                                mapper.set_entity_service_alias(entity, canonical_name, alias_name)
                            
                            messagebox.showinfo("Success", f"Added: {canonical_name}")
                            dialog.destroy()
                            # Reload the mapping UI
                            load_entity_mapping()
                        else:
                            messagebox.showerror("Error", f"Service '{canonical_name}' already exists")
                    
                    ctk.CTkButton(
                        btn_frame,
                        text="Add Service",
                        command=save_new_service,
                        fg_color="#27ae60",
                        hover_color="#229954"
                    ).pack(side="left", padx=(0, 5))
                    
                    ctk.CTkButton(
                        btn_frame,
                        text="Cancel",
                        command=dialog.destroy,
                        fg_color="#95a5a6",
                        hover_color="#7f8c8d"
                    ).pack(side="left")
                
                ctk.CTkButton(
                    header_frame,
                    text="+ Add New Service",
                    command=add_new_service,
                    width=180,
                    fg_color="#27ae60",
                    hover_color="#229954"
                ).pack(side="right", padx=5)
                
                # Scrollable services list with alias mappings
                scroll_frame = ctk.CTkScrollableFrame(mapping_container, fg_color="transparent")
                scroll_frame.pack(fill="both", expand=True, padx=15, pady=10)
                
                # Table header
                header_row = ctk.CTkFrame(scroll_frame, fg_color="#34495e", height=35)
                header_row.pack(fill="x", pady=(0, 5))
                header_row.pack_propagate(False)
                
                ctk.CTkLabel(
                    header_row,
                    text="Canonical Service",
                    font=("Arial", 11, "bold"),
                    width=300
                ).pack(side="left", padx=10, pady=8)
                
                ctk.CTkLabel(
                    header_row,
                    text="↔",
                    font=("Arial", 12, "bold"),
                    width=30
                ).pack(side="left")
                
                ctk.CTkLabel(
                    header_row,
                    text=f"{entity} Name",
                    font=("Arial", 11, "bold"),
                    width=300
                ).pack(side="left", padx=10, pady=8)
                
                # Services list
                for canonical_name in canonical_services:
                    row_frame = ctk.CTkFrame(scroll_frame, fg_color="#2c3e50", corner_radius=4)
                    row_frame.pack(fill="x", pady=3, padx=5)
                    
                    # Canonical service (read-only label)
                    ctk.CTkLabel(
                        row_frame,
                        text=canonical_name,
                        font=("Arial", 10),
                        width=300,
                        anchor="w",
                        text_color="#3498db"
                    ).pack(side="left", padx=10, pady=8)
                    
                    ctk.CTkLabel(
                        row_frame,
                        text="→",
                        font=("Arial", 11, "bold"),
                        width=30
                    ).pack(side="left")
                    
                    # Entity alias (editable entry)
                    alias_var = ctk.StringVar(value=aliases.get(canonical_name, ""))
                    alias_entry = ctk.CTkEntry(
                        row_frame,
                        textvariable=alias_var,
                        font=("Arial", 10),
                        width=300,
                        placeholder_text="(optional: entity-specific name)"
                    )
                    alias_entry.pack(side="left", padx=10, pady=5)
                    
                    # Save button for this alias
                    def save_alias(canonical=canonical_name, var=alias_var):
                        alias_val = var.get().strip()
                        if alias_val:
                            mapper.set_entity_service_alias(entity, canonical, alias_val)
                            info_label.configure(text=f"{len(mapper.load_entity_service_aliases(entity))} / {len(canonical_services)} mapped")
                            print(f"[DEBUG] Saved alias for {canonical}: {alias_val}")
                        else:
                            # Clear alias if empty
                            current_aliases = mapper.load_entity_service_aliases(entity)
                            if canonical in current_aliases:
                                del current_aliases[canonical]
                                mapper.save_entity_service_aliases(entity, current_aliases)
                                info_label.configure(text=f"{len(current_aliases)} / {len(canonical_services)} mapped")
                                print(f"[DEBUG] Cleared alias for {canonical}")
                    
                    ctk.CTkButton(
                        row_frame,
                        text="Save",
                        command=save_alias,
                        width=60,
                        font=("Arial", 9),
                        fg_color="#3498db",
                        hover_color="#2980b9"
                    ).pack(side="left", padx=5, pady=5)
                
                print(f"[DEBUG] Loaded {len(canonical_services)} canonical services, {len(aliases)} mapped for {entity}")
                
            except Exception as e:
                print(f"Error loading canonical service mapping: {e}")
                import traceback
                traceback.print_exc()
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

        # ── 1.3 Fee Services Configuration ────────────────────────────────────
        fee_services_tab = config_subtabs.add("Fee Services")
        
        # Account selector for Fee Service defaults
        fee_header_frame = ctk.CTkFrame(fee_services_tab, fg_color="#1f538d", height=60)
        fee_header_frame.pack(fill="x", padx=0, pady=(0, 5))
        fee_header_frame.pack_propagate(False)
        
        fee_header_inner = ctk.CTkFrame(fee_header_frame, fg_color="transparent")
        fee_header_inner.pack(expand=True)
        
        ctk.CTkLabel(
            fee_header_inner,
            text="Configure Fee Service Defaults:",
            font=("Arial", 12, "bold"),
            text_color="white"
        ).pack(side="left", padx=(10, 10), pady=15)
        
        # Load accounts
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / "Core"))
            from account_workflow_manager import AccountWorkflowManager
            
            wf_manager = AccountWorkflowManager()
            account_list = wf_manager.get_accounts()
        except Exception:
            account_list = []
        
        fee_account_var = ctk.StringVar(value=account_list[0] if account_list else "")
        fee_account_dropdown = ctk.CTkComboBox(
            fee_header_inner,
            values=account_list,
            variable=fee_account_var,
            width=200,
            font=("Arial", 12)
        )
        fee_account_dropdown.pack(side="left", padx=(0, 10), pady=15)
        
        # Container for fee service configuration
        fee_config_container = ctk.CTkFrame(fee_services_tab, fg_color="transparent")
        fee_config_container.pack(fill="both", expand=True)
        
        def load_fee_services_config(*_):
            """Load and display Fee Service default configuration"""
            for widget in fee_config_container.winfo_children():
                widget.destroy()
            
            account = fee_account_var.get()
            if not account:
                ctk.CTkLabel(
                    fee_config_container,
                    text="No account selected",
                    font=("Arial", 11)
                ).pack(expand=True, pady=20)
                return
            
            try:
                from service_mapper import ServiceMapper
                
                mapper = ServiceMapper()
                canonical_services = [s for s in mapper.canonical_services if "Fee" in s]
                
                if not canonical_services:
                    ctk.CTkLabel(
                        fee_config_container,
                        text="No Fee services found in canonical services",
                        font=("Arial", 11)
                    ).pack(expand=True, pady=20)
                    return
                
                # Load existing fee defaults for this account
                fee_defaults_path = Path(__file__).parent.parent / "Core" / "accounts" / account / "fee_service_defaults.json"
                fee_defaults = {}
                if fee_defaults_path.exists():
                    with open(fee_defaults_path, 'r', encoding='utf-8') as f:
                        fee_defaults = json.load(f).get("defaults", {})
                
                # Info label
                info_frame = ctk.CTkFrame(fee_config_container, fg_color="transparent")
                info_frame.pack(fill="x", padx=15, pady=(15, 10))
                
                ctk.CTkLabel(
                    info_frame,
                    text=f"Default Quantities for {account} - {len(canonical_services)} Fee Services",
                    font=("Arial", 12, "bold")
                ).pack(anchor="w")
                
                # Scrollable list of Fee services
                scroll_frame = ctk.CTkScrollableFrame(fee_config_container, fg_color="transparent")
                scroll_frame.pack(fill="both", expand=True, padx=15, pady=10)
                
                # Table header
                header_row = ctk.CTkFrame(scroll_frame, fg_color="#34495e", height=35)
                header_row.pack(fill="x", pady=(0, 5))
                header_row.pack_propagate(False)
                
                ctk.CTkLabel(
                    header_row,
                    text="Fee Service Name",
                    font=("Arial", 11, "bold"),
                    width=400
                ).pack(side="left", padx=10, pady=8)
                
                ctk.CTkLabel(
                    header_row,
                    text="Default Quantity",
                    font=("Arial", 11, "bold"),
                    width=150
                ).pack(side="left", padx=10, pady=8)
                
                # Fee services list
                for service_name in canonical_services:
                    row_frame = ctk.CTkFrame(scroll_frame, fg_color="#2c3e50", corner_radius=4)
                    row_frame.pack(fill="x", pady=3, padx=5)
                    
                    ctk.CTkLabel(
                        row_frame,
                        text=service_name,
                        font=("Arial", 10),
                        width=400,
                        anchor="w",
                        text_color="#2ecc71"
                    ).pack(side="left", padx=10, pady=8)
                    
                    # Default quantity entry
                    qty_var = ctk.StringVar(value=str(fee_defaults.get(service_name, "")))
                    qty_entry = ctk.CTkEntry(
                        row_frame,
                        textvariable=qty_var,
                        font=("Arial", 10),
                        width=150,
                        placeholder_text="(optional)"
                    )
                    qty_entry.pack(side="left", padx=5, pady=5)
                    
                    # Save button
                    def save_fee_default(service=service_name, var=qty_var):
                        default_qty = var.get().strip()
                        
                        # Load current defaults
                        if fee_defaults_path.exists():
                            with open(fee_defaults_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                        else:
                            data = {"description": f"Fee Service default quantities for {account}", "defaults": {}}
                        
                        # Update or remove
                        if default_qty:
                            try:
                                float(default_qty)  # Validate it's a number
                                data["defaults"][service] = default_qty
                                print(f"[DEBUG] Set default quantity for {service}: {default_qty}")
                            except ValueError:
                                messagebox.showerror("Invalid", "Default quantity must be a number")
                                return
                        else:
                            if service in data["defaults"]:
                                del data["defaults"][service]
                                print(f"[DEBUG] Cleared default quantity for {service}")
                        
                        # Save
                        fee_defaults_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(fee_defaults_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2, ensure_ascii=False)
                        
                        messagebox.showinfo("Saved", f"Default quantity saved for {service}")
                    
                    ctk.CTkButton(
                        row_frame,
                        text="Save",
                        command=save_fee_default,
                        width=70,
                        font=("Arial", 9),
                        fg_color="#27ae60",
                        hover_color="#229954"
                    ).pack(side="left", padx=5, pady=5)
                
            except Exception as e:
                print(f"Error loading fee services config: {e}")
                import traceback
                traceback.print_exc()
                ctk.CTkLabel(
                    fee_config_container,
                    text=f"⚠️ Error: {str(e)}",
                    font=("Arial", 11),
                    text_color="#e74c3c"
                ).pack(expand=True, pady=20)
        
        fee_account_dropdown.configure(command=load_fee_services_config)
        
        if account_list:
            load_fee_services_config()

    def setup_quoteme_parser_tab(self):
        """Setup QuoteMe Email Parser tab - embedded directly in the viewing pane"""
        parser_tab = self.main_tabs.add("QuoteMe Parser")
        
        # ── Manage Workflows Tab ─────────────────────────────────────────────────
        workflows_tab = self.main_tabs.add("Manage Workflows")
        self._setup_manage_workflows_tab(workflows_tab)

        def on_parser_apply(lp_code: str, lp_data):
            """Callback when parser applies individual LP data"""
            print(f"\n[DEBUG] on_parser_apply called")
            print(f"[DEBUG]   lp_code: {lp_code}")
            print(f"[DEBUG]   lp_data type: {type(lp_data)}")
            
            # Initialize quoteme_data as a list if not already set
            if self.quoteme_data is None:
                self.quoteme_data = []
                print(f"[DEBUG]   Initialized quoteme_data as empty list")
            
            # Add this LP data to the list (avoid duplicates by checking lp_code)
            existing_lp_codes = [lp.lp_code for lp in self.quoteme_data if hasattr(lp, 'lp_code')]
            print(f"[DEBUG]   Existing LP codes: {existing_lp_codes}")
            
            if lp_code not in existing_lp_codes:
                self.quoteme_data.append(lp_data)
                print(f"[DEBUG]   Added lp_data to quoteme_data (total: {len(self.quoteme_data)})")
            else:
                print(f"[DEBUG]   LP code already exists - skipping")
            
            # Extract and add to language_pairs if not already present
            lp_name = self._extract_lp_name(lp_code)
            print(f"[DEBUG]   Extracted LP name: {lp_name}")
            
            if lp_name not in self.language_pairs:
                self.language_pairs.append(lp_name)
                print(f"[DEBUG]   Added to language_pairs (total: {len(self.language_pairs)})")
            else:
                print(f"[DEBUG]   LP name already in language_pairs - skipping")
            
            # Update status
            self.update_status(f"✅ Applied: {lp_code}")
            
            # If a workflow is selected, refresh quantities in services table
            print(f"[DEBUG]   selected_workflow: {self.selected_workflow}")
            if self.selected_workflow:
                services = self.account_workflow_manager.get_workflow_services(
                    self.current_account,
                    self.selected_workflow
                )
                print(f"[DEBUG]   Got services: {services}")
                if services:
                    print(f"[DEBUG]   Calling populate_services_table")
                    self.populate_services_table(services)
            else:
                print(f"[DEBUG]   No workflow selected - not refreshing table")

        def on_parser_complete(parse_result):
            """Callback when parsing completes - update Job Data tab"""
            print(f"\n[DEBUG] on_parser_complete called")
            print(f"[DEBUG]   parse_result: {parse_result}")
            if parse_result:
                print(f"[DEBUG]   parse_result.success: {parse_result.success if hasattr(parse_result, 'success') else 'N/A'}")
                print(f"[DEBUG]   parse_result.language_pairs: {len(parse_result.language_pairs) if hasattr(parse_result, 'language_pairs') else 'N/A'}")
            
            if parse_result and hasattr(parse_result, 'success') and parse_result.success and hasattr(parse_result, 'language_pairs') and parse_result.language_pairs:
                try:
                    print(f"[DEBUG]   Calling set_language_pairs_from_quoteme with {len(parse_result.language_pairs)} LP(s)")
                    self.set_language_pairs_from_quoteme(parse_result.language_pairs)
                    self.update_status(f"✅ Job Data updated with {len(parse_result.language_pairs)} language pair(s)")
                except Exception as e:
                    print(f"[DEBUG] ERROR: {e}")
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

    def _on_source_type_changed(self, choice: str):
        """Callback when source type dropdown changes - refresh services table"""
        if self.selected_workflow:
            services = self.account_workflow_manager.get_workflow_services(
                self.current_account,
                self.selected_workflow
            )
            self.populate_services_table(services)
    
    def _setup_manage_workflows_tab(self, tab_frame):
        """Setup the Manage Workflows tab with embedded UI (no dialog)"""
        # Content frame
        content_frame = ctk.CTkFrame(tab_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Workflows list label and button frame
        list_header = ctk.CTkFrame(content_frame, fg_color="transparent")
        list_header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            list_header,
            text="Workflows:",
            font=("Arial", 11, "bold")
        ).pack(anchor="w", side="left")
        
        # Scrollable workflows list
        workflows_scroll = ctk.CTkScrollableFrame(
            content_frame,
            fg_color="gray25",
            corner_radius=8
        )
        workflows_scroll.pack(fill="both", expand=True)
        
        # Bind mouse wheel
        def on_mousewheel(event):
            workflows_scroll._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        workflows_scroll.bind("<MouseWheel>", on_mousewheel)
        
        def refresh_workflows_list():
            """Refresh the workflows list display"""
            # Clear existing widgets
            for widget in workflows_scroll.winfo_children():
                widget.destroy()
            
            if not self.current_account:
                ctk.CTkLabel(
                    workflows_scroll,
                    text="Select an account first",
                    text_color="orange"
                ).pack(pady=20)
                return
            
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
                    
                    services = self.account_workflow_manager.get_workflow_services(
                        self.current_account,
                        workflow_name
                    )
                    
                    # Extract service names (handle both string and dict formats)
                    service_names = []
                    for svc in (services or []):
                        if isinstance(svc, dict):
                            service_names.append(svc.get("name", svc))
                        else:
                            service_names.append(svc)
                    
                    ctk.CTkLabel(
                        wf_info_frame,
                        text=f"📋 {workflow_name}",
                        font=("Arial", 11, "bold")
                    ).pack(anchor="w")
                    
                    ctk.CTkLabel(
                        wf_info_frame,
                        text=f"Services: {', '.join(service_names) if service_names else 'None'}",
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
                        command=lambda wf=workflow_name: self._edit_workflow_dialog(None, wf),
                        width=80,
                        height=26,
                        font=("Arial", 9),
                        fg_color="#3498db"
                    ).pack(side="left", padx=(0, 5))
                    
                    ctk.CTkButton(
                        btn_frame,
                        text="🗑️ Delete",
                        command=lambda wf=workflow_name: self._delete_workflow_from_tab(wf, refresh_workflows_list),
                        width=80,
                        height=26,
                        font=("Arial", 9),
                        fg_color="#e74c3c"
                    ).pack(side="left")
        
        # Save the refresh function so it can be called from update_account_display()
        self._manage_workflows_refresh = refresh_workflows_list
        
        # Add New button now that refresh_workflows_list is defined
        ctk.CTkButton(
            list_header,
            text="➕ Add New",
            command=lambda: self._add_workflow_embedded(content_frame, refresh_workflows_list),
            width=100,
            height=28,
            font=("Arial", 9, "bold"),
            fg_color="green"
        ).pack(anchor="e", side="right")
        
        # Initial population
        refresh_workflows_list()
    
    def _add_workflow_embedded(self, parent_frame, refresh_callback):
        """Dialog to add new workflow - works with embedded tab"""
        add_dialog = ctk.CTkToplevel(self.root)
        add_dialog.title("Add Workflow")
        add_dialog.geometry("600x500")
        add_dialog.transient(self.root)
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
        
        from Core.service_search_engine import ServiceSearchEngine
        
        search_var.trace_add("write", on_search_change)
        
        def on_service_selected(service_name, cb_var):
            """Handle service checkbox"""
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
            var = BooleanVar(value=False)
            
            def make_callback(svc, v):
                return lambda: on_service_selected(svc, v)
            
            cb_frame = ctk.CTkFrame(services_scroll, fg_color="transparent")
            cb_frame.pack(anchor="w", padx=10, pady=2, fill="x")
            service_frames[service] = cb_frame
            
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
        attribute_vars = {}  # Track Used_when attributes
        
        def update_selected_list():
            """Refresh the selected services list"""
            for widget in selected_widgets:
                widget.destroy()
            selected_widgets.clear()
            
            for idx, service in enumerate(selected_services_list):
                item_frame = ctk.CTkFrame(selected_scroll, fg_color="gray20", corner_radius=4, height=40)
                item_frame.pack(fill="x", padx=5, pady=3)
                item_frame.pack_propagate(False)
                selected_widgets.append(item_frame)
                
                content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
                content_frame.pack(fill="both", expand=True, padx=2, pady=2)
                
                service_label = ctk.CTkLabel(
                    content_frame,
                    text=f"{idx + 1}. {service}",
                    font=("Arial", 10),
                    justify="left"
                )
                service_label.pack(side="left", fill="x", expand=True, pady=5)
                
                # Remove button
                def make_remove_cmd(service_name):
                    def remove_service():
                        selected_services_list.remove(service_name)
                        service_widgets[service_name][1].set(False)
                        update_selected_list()
                    return remove_service
                
                ctk.CTkButton(
                    content_frame,
                    text="✗",
                    command=make_remove_cmd(service),
                    width=24,
                    height=24,
                    font=("Arial", 10),
                    fg_color="#e74c3c"
                ).pack(side="right", padx=5)
                
                # Initialize attribute_vars if needed
                if service not in attribute_vars:
                    attribute_vars[service] = {
                        ">For": BooleanVar(value=False),
                        ">Eng": BooleanVar(value=False),
                        "Live": BooleanVar(value=False)
                    }
        
        # Initial population
        update_selected_list()
        
        # Buttons
        btn_frame = ctk.CTkFrame(add_dialog, fg_color="transparent")
        btn_frame.pack(pady=15, padx=15)
        
        def save_workflow():
            workflow_name = name_entry.get().strip()
            if not workflow_name:
                messagebox.showerror("Error", "Workflow name cannot be empty!")
                return
            
            if not selected_services_list:
                messagebox.showerror("Error", "Select at least one service!")
                return
            
            if self.account_workflow_manager.create_workflow(self.current_account, workflow_name, selected_services_list):
                # Update service attributes
                for service in selected_services_list:
                    used_when = []
                    if service in attribute_vars:
                        if attribute_vars[service][">For"].get():
                            used_when.append(">For")
                        if attribute_vars[service][">Eng"].get():
                            used_when.append(">Eng")
                        if attribute_vars[service]["Live"].get():
                            used_when.append("Live")
                    
                    if hasattr(self.account_workflow_manager, 'update_service_attribute'):
                        self.account_workflow_manager.update_service_attribute(
                            self.current_account,
                            workflow_name,
                            service,
                            used_when
                        )
                
                add_dialog.destroy()
                refresh_callback()  # Refresh Manage Workflows tab
                self.refresh_workflow_dropdown()  # CRITICAL: Also refresh Job Data dropdown
            else:
                messagebox.showerror("Error", f"Workflow '{workflow_name}' already exists!")
        
        ctk.CTkButton(btn_frame, text="Create", command=save_workflow, width=100, fg_color="#2b7dbc").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=add_dialog.destroy, width=100).pack(side="left", padx=5)
    
    def _delete_workflow_from_tab(self, workflow_name, refresh_callback):
        """Delete workflow and refresh tab display"""
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete workflow '{workflow_name}'?\n\nThis cannot be undone."
        )
        
        if confirm:
            if self.account_workflow_manager.delete_workflow(self.current_account, workflow_name):
                messagebox.showinfo("Success", f"Workflow '{workflow_name}' deleted")
                refresh_callback()
            else:
                messagebox.showerror("Error", "Failed to delete workflow")
    
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
    
    def get_rate_from_card(self, rate_card: dict, service: str, target_language: Optional[str] = None) -> str:
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
        print(f"[DEBUG] refresh_workflow_dropdown called - current_account: {self.current_account}")
        try:
            workflows = self.get_available_workflows()
            print(f"[DEBUG] Got workflows: {workflows}")
            self.workflow_dropdown.configure(values=workflows)
            print(f"[DEBUG] Configured dropdown values")
            if workflows:
                self.workflow_dropdown.set(workflows[0])
                print(f"[DEBUG] Set first workflow: {workflows[0]}")
                self.on_workflow_selected(workflows[0])
            else:
                self.workflow_dropdown.set("")
                print(f"[DEBUG] No workflows, showing empty label")
                if hasattr(self, 'services_empty_label'):
                    self.services_empty_label.pack(expand=True, pady=20)
        except Exception as e:
            print(f"[ERROR] refresh_workflow_dropdown failed: {e}")
            import traceback
            traceback.print_exc()
    
    def refresh_rate_card_dropdown(self):
        """Refresh rate card dropdown - allows user to choose"""
        print(f"[DEBUG] refresh_rate_card_dropdown called - current_account: {self.current_account}")
        try:
            rate_cards = self.get_available_rate_cards()
            print(f"[DEBUG] Got rate cards: {rate_cards}")
            self.rate_card_dropdown.configure(values=rate_cards)
            print(f"[DEBUG] Configured rate card dropdown values")
            # Don't auto-select; let user choose manually or use Browse button
            self.rate_card_dropdown.set("")
            self.selected_rate_card = None
            self.rate_card_info.configure(text="ℹ️ No rate card loaded. Select from dropdown or browse for a file.")
        except Exception as e:
            print(f"[ERROR] refresh_rate_card_dropdown failed: {e}")
            import traceback
            traceback.print_exc()
    
    def open_current_account_workflow_editor(self):
        """Deprecated - workflow editing now in Manage Workflows tab"""
        # Direct user to the Manage Workflows tab instead
        messagebox.showinfo("Workflow Editor Moved", "Workflow editing has been moved to the 'Manage Workflows' tab. Please use that tab to manage workflows.")
        # Optionally, select the Manage Workflows tab
        # self.main_tabs.set("Manage Workflows")  # If tab names support this
        return
    
    def open_current_account_workflow_editor_old(self):
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
                
                # Extract service names (handle both string and dict formats)
                service_names = []
                for svc in (services or []):
                    if isinstance(svc, dict):
                        service_names.append(svc.get("name", svc))
                    else:
                        service_names.append(svc)
                
                ctk.CTkLabel(
                    wf_info_frame,
                    text=f"📋 {workflow_name}",
                    font=("Arial", 11, "bold")
                ).pack(anchor="w")
                
                ctk.CTkLabel(
                    wf_info_frame,
                    text=f"Services: {', '.join(service_names) if service_names else 'None'}",
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
        
        search_var.trace_add("write", on_search_change)
        
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
            var = BooleanVar(value=False)
            
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
        edit_dialog.geometry("700x600")
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
        current_services_raw = self.account_workflow_manager.get_workflow_services(
            self.current_account,
            workflow_name
        )
        
        # Extract service names (handle both string and dict formats)
        current_services = []
        for svc in (current_services_raw or []):
            if isinstance(svc, dict):
                current_services.append(svc.get("name", svc))
            else:
                current_services.append(svc)
        
        # Get canonical services
        canonical_services = self.service_mapper.canonical_services
        selected_services_list = list(current_services)  # Maintain current order
        service_widgets = {}
        service_frames = {}  # Track frames for visibility toggling
        attribute_vars = {}  # Track Used_when attributes for each service
        
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
        
        search_var.trace_add("write", on_search_change)
        
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
            var = BooleanVar(value=service in current_services)
            
            def make_callback(svc, v):
                return lambda: on_service_selected(svc, v)
            
            # Get current attributes for this service
            current_attrs = []
            if hasattr(self.account_workflow_manager, 'get_service_attributes'):
                try:
                    current_attrs = self.account_workflow_manager.get_service_attributes(
                        self.current_account,
                        workflow_name,
                        service
                    )
                except:
                    current_attrs = []
            
            cb_frame = ctk.CTkFrame(services_scroll, fg_color="transparent")
            cb_frame.pack(anchor="w", padx=10, pady=5, fill="x")
            service_frames[service] = cb_frame  # Store frame for search filtering
            
            # Service checkbox
            cb = ctk.CTkCheckBox(
                cb_frame,
                text=service,
                variable=var,
                command=make_callback(service, var),
                font=("Arial", 9, "bold")
            )
            cb.pack(anchor="w", side="left", pady=(0, 3))
            service_widgets[service] = (cb, var)
            
            # Attribute checkboxes (only shown if service is selected)
            attr_frame = ctk.CTkFrame(cb_frame, fg_color="transparent")
            attr_frame.pack(anchor="w", fill="x", padx=(20, 0), pady=(2, 3))
            
            attribute_vars[service] = {}
            
            # >For checkbox
            for_var = BooleanVar(value=(">For" in current_attrs))
            ctk.CTkCheckBox(
                attr_frame,
                text=">For (Foreign)",
                variable=for_var,
                font=("Arial", 8),
                text_color="#aaa"
            ).pack(side="left", padx=(0, 8))
            attribute_vars[service][">For"] = for_var
            
            # >Eng checkbox
            eng_var = BooleanVar(value=(">Eng" in current_attrs))
            ctk.CTkCheckBox(
                attr_frame,
                text=">Eng (English)",
                variable=eng_var,
                font=("Arial", 8),
                text_color="#aaa"
            ).pack(side="left", padx=(0, 8))
            attribute_vars[service][">Eng"] = eng_var
            
            # Live checkbox
            live_var = BooleanVar(value=("Live" in current_attrs))
            ctk.CTkCheckBox(
                attr_frame,
                text="Live source",
                variable=live_var,
                font=("Arial", 8),
                text_color="#aaa"
            ).pack(side="left", padx=0)
            attribute_vars[service]["Live"] = live_var
        
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
                        # Bind B1-Motion to root window for tracking while button is held
                        edit_dialog.bind("<B1-Motion>", on_motion)
                    
                    def on_motion(event):
                        if not drag_data["dragging"] or drag_data["source_idx"] is None:
                            return
                        
                        # Get the scrollable frame's scroll offset to adjust coordinates
                        scroll_offset = selected_scroll._parent_canvas.yview()[0] * (
                            selected_scroll._parent_canvas.bbox("all")[3] if selected_scroll._parent_canvas.bbox("all") else 0
                        )
                        
                        # Find which service we're hovering over using absolute window coordinates
                        target_y = selected_scroll.winfo_rooty() + (event.y - edit_dialog.winfo_rooty())
                        
                        for check_idx, check_widget in enumerate(selected_widgets):
                            widget_root_y = check_widget.winfo_rooty()
                            widget_height = check_widget.winfo_height()
                            # Check if we're hovering over this widget
                            if widget_root_y <= event.y_root <= widget_root_y + widget_height:
                                # Highlight this widget as the drop target
                                if check_idx != drag_data["source_idx"]:
                                    check_widget.configure(fg_color="#2ecc71")
                                else:
                                    check_widget.configure(fg_color="#3498db")
                            else:
                                # Reset color for non-target widgets
                                if check_widget != drag_data["source_widget"]:
                                    check_widget.configure(fg_color="gray20")
                    
                    def on_release(event):
                        if not drag_data["dragging"] or drag_data["source_idx"] is None:
                            return
                        
                        drag_data["dragging"] = False
                        edit_dialog.unbind("<B1-Motion>")
                        
                        # Find target index by checking which widget we released over
                        target_idx = drag_data["source_idx"]  # Default to current position
                        for check_idx, check_widget in enumerate(selected_widgets):
                            widget_root_y = check_widget.winfo_rooty()
                            widget_height = check_widget.winfo_height()
                            if widget_root_y <= event.y_root <= widget_root_y + widget_height:
                                target_idx = check_idx
                                break
                        
                        # Perform reorder if different positions
                        if target_idx != drag_data["source_idx"]:
                            src = drag_data["source_idx"]
                            dst = target_idx
                            # Move item from src to dst
                            item = selected_services_list.pop(src)
                            selected_services_list.insert(dst, item)
                        
                        # Reset drag state
                        drag_data["source_idx"] = None
                        drag_data["source_widget"] = None
                        
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
                # Update service attributes
                for service in selected_services_list:
                    if service in attribute_vars:
                        used_when = []
                        if attribute_vars[service][">For"].get():
                            used_when.append(">For")
                        if attribute_vars[service][">Eng"].get():
                            used_when.append(">Eng")
                        if attribute_vars[service]["Live"].get():
                            used_when.append("Live")
                        
                        if hasattr(self.account_workflow_manager, 'update_service_attribute'):
                            self.account_workflow_manager.update_service_attribute(
                                self.current_account,
                                workflow_name,
                                service,
                                used_when
                            )
                
                edit_dialog.destroy()
                messagebox.showinfo("Success", f"Workflow '{workflow_name}' updated successfully")
                # Refresh parent dialog if it exists (from embedded tab)
                if parent_dialog is not None:
                    parent_dialog.destroy()
                # Refresh the Manage Workflows tab
                if hasattr(self, '_manage_workflows_refresh'):
                    self._manage_workflows_refresh()
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
                # Refresh the Manage Workflows tab if available
                if hasattr(self, '_manage_workflows_refresh'):
                    self._manage_workflows_refresh()
                self.refresh_workflow_dropdown()
            else:
                messagebox.showerror("Error", "Failed to delete workflow")
    
    def _open_service_config_dialog(self):
        """Open the Map QuoteMe Values dialog for service configuration"""
        if not self.current_account:
            messagebox.showwarning("No Account", "Please select an account first")
            return
        
        if not self.selected_workflow:
            messagebox.showwarning("No Workflow", "Please select a workflow first")
            return
        
        if not self.quoteme_data and not self.manual_wc_data:
            messagebox.showwarning(
                "No Word Count Data",
                "Please parse a QuoteMe email or add Manual WC data first to configure services"
            )
            return
        
        
        # Get services for current workflow
        services = self.account_workflow_manager.get_workflow_services(
            self.current_account,
            self.selected_workflow
        )
        
        if not services:
            messagebox.showwarning("No Services", "The selected workflow has no services")
            return
        
        # Extract service names (handle both string and dict formats)
        service_names = []
        for s in services:
            if isinstance(s, dict):
                service_names.append(s.get("name", s))
            else:
                service_names.append(s)
        
        # Show the mapping dialog
        self._show_quoteme_mapping_dialog(service_names, self.selected_workflow)
    
    def on_workflow_selected(self, workflow_name: str):
        """Handle workflow selection - populate services table and check for QuoteMe mapping"""
        print(f"\n[DEBUG] on_workflow_selected called: workflow='{workflow_name}'")

        # Pull latest entities in case Manage Entities changed WF_Matrix in-session.
        self._refresh_entity_dropdown()
        
        if not workflow_name or not self.current_account:
            print(f"[DEBUG] Returning early - workflow_name: {workflow_name}, current_account: {self.current_account}")
            return
        
        self.selected_workflow = workflow_name
        services = self.account_workflow_manager.get_workflow_services(
            self.current_account,
            workflow_name
        )
        print(f"[DEBUG] Services for workflow: {services}")
        
        # Check if we have QuoteMe data and need to map values to services
        if self.quoteme_data and services:
            print(f"[DEBUG] QuoteMe data present ({len(self.quoteme_data)} LPs), checking mapping...")
            existing_mapping = self.quoteme_value_mapper.load_mapping(
                self.current_account
            )
            print(f"[DEBUG] Loaded mapping keys: {list(existing_mapping.keys())}")
            
            # Check if user has opted to skip prompts for this workflow
            skip_prompts = existing_mapping.get("_workflow_skip_prompts", {})
            should_skip_for_this_wf = skip_prompts.get(workflow_name, False)
            print(f"[DEBUG] Skip prompts for this workflow: {should_skip_for_this_wf}")
            
            # Extract service names (handle both string and dict formats)
            service_names = []
            for s in services:
                if isinstance(s, dict):
                    service_names.append(s.get("name", s))
                else:
                    service_names.append(s)
            
            print(f"[DEBUG] Service names: {service_names}")
            
            # Show dialog if:
            # 1. User hasn't opted to skip this workflow AND
            # 2. (New services exist that aren't mapped OR no mapping exists at all)
            if not should_skip_for_this_wf:
                # Filter out metadata keys when checking for service mappings
                service_mapping = {k: v for k, v in existing_mapping.items() if not k.startswith("_")}
                unmapped_services = [s for s in service_names if s not in service_mapping]
                print(f"[DEBUG] Unmapped services: {unmapped_services}, existing mapping count: {len(service_mapping)}")
                if unmapped_services or not service_mapping:
                    # New services need mapping
                    print(f"[DEBUG] Showing QuoteMe mapping dialog...")
                    self._show_quoteme_mapping_dialog(service_names, workflow_name)
        else:
            print(f"[DEBUG] Skipping mapping check - quoteme_data: {bool(self.quoteme_data)}, services: {bool(services)}")
        
        print(f"[DEBUG] Calling populate_services_table...")
        self.populate_services_table(services)
    
    def _show_manual_wc_dialog(self):
        """Show dialog for manually entering word count data for specific language pairs"""
        if not self.current_account or not self.selected_rate_card:
            messagebox.showwarning("Missing Info", "Please select a rate card first")
            return

        # Build language list from currently selected/imported rate card
        language_choices = []
        rate_card = self.cached_rate_card if self.cached_rate_card else self.load_rate_card(self.selected_rate_card)
        if isinstance(rate_card, dict) and "languages" in rate_card:
            language_choices = ["English (US)", "English (GB)"] + sorted([str(k).strip() for k in rate_card.get("languages", {}).keys() if str(k).strip()])
        
        # Fallback: derive source/target suggestions from existing LPs
        if not language_choices:
            derived = set()
            for lp_name in self.language_pairs:
                if ">" in lp_name:
                    src, tgt = lp_name.split(">", 1)
                    if src.strip():
                        derived.add(src.strip())
                    if tgt.strip():
                        derived.add(tgt.strip())
            language_choices = ["English (US)", "English (GB)"] +sorted(derived)
        
        # Create modal dialog
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Manual Word Count Entry")
        dialog.geometry("700x800")
        dialog.resizable(True, True)
        dialog.grab_set()
        dialog.transient(self.root)
        self._manual_wc_dialog = dialog
        
        # Make dialog centered and keep it on top
        dialog.after(100, lambda: dialog.lift())
        
        # Main frame with scrollable content
        main_frame = ctk.CTkScrollableFrame(dialog, fg_color="gray25")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Data structure to hold LP entries
        lp_entries = []
        
        def create_lp_section(frame, lp_data=None):
            """Create a section for one language pair"""
            lp_section_frame = ctk.CTkFrame(frame, fg_color="gray30", corner_radius=5)
            lp_section_frame.pack(fill="x", padx=5, pady=5)

            # Source/Target language selectors
            lp_header_frame = ctk.CTkFrame(lp_section_frame, fg_color="transparent")
            lp_header_frame.pack(fill="x", padx=10, pady=(10, 5))

            ctk.CTkLabel(
                lp_header_frame,
                text="Source:",
                font=("Arial", 9, "bold")
            ).pack(side="left", padx=(0, 4))

            source_var = ctk.StringVar(value=lp_data.get("source", "") if lp_data else "")
            source_combo = ctk.CTkComboBox(
                lp_header_frame,
                values=language_choices,
                variable=source_var,
                width=200,
                font=("Arial", 9),
                state="normal"
            )
            source_combo.pack(side="left", padx=(0, 10))

            ctk.CTkLabel(
                lp_header_frame,
                text="Target:",
                font=("Arial", 9, "bold")
            ).pack(side="left", padx=(0, 4))

            target_var = ctk.StringVar(value=lp_data.get("target", "") if lp_data else "")
            target_combo = ctk.CTkComboBox(
                lp_header_frame,
                values=language_choices,
                variable=target_var,
                width=200,
                font=("Arial", 9),
                state="normal"
            )
            target_combo.pack(side="left", padx=(0, 5))

            # Type-ahead filtering for source/target dropdowns
            def bind_typeahead(combo_widget):
                def on_type(_event=None):
                    typed = combo_widget.get().strip().lower()
                    if not language_choices:
                        return
                    if typed:
                        filtered = [lang for lang in language_choices if typed in lang.lower()]
                        combo_widget.configure(values=filtered if filtered else language_choices)
                    else:
                        combo_widget.configure(values=language_choices)
                combo_widget.bind("<KeyRelease>", on_type)

            bind_typeahead(source_combo)
            bind_typeahead(target_combo)

            # WC Fields grid
            wc_frame = ctk.CTkFrame(lp_section_frame, fg_color="transparent")
            wc_frame.pack(fill="x", padx=10, pady=(5, 10))
            
            wc_labels = ["Context:", "100%:", "Repetitions:", "Fuzzy Matches:", "New Words:", "Total Words:"]
            wc_fields = ["context", "fuzzy_100", "repetitions", "fuzzy_matches", "new_words", "total_words"]
            wc_widgets = {}

            for i, (label, field) in enumerate(zip(wc_labels, wc_fields)):
                row = i // 2
                col = i % 2

                # Label
                ctk.CTkLabel(
                    wc_frame,
                    text=label,
                    font=("Arial", 9),
                    width=80,
                    anchor="e"
                ).grid(row=row, column=col*2, padx=5, pady=3, sticky="e")

                # Entry
                entry = ctk.CTkEntry(
                    wc_frame,
                    width=60,
                    height=25,
                    font=("Arial", 9)
                )
                entry.grid(row=row, column=col*2+1, padx=5, pady=3, sticky="w")

                # Populate if editing existing
                if lp_data and field in lp_data:
                    entry.insert(0, str(lp_data[field]))

                # Total words is auto-calculated
                if field == "total_words":
                    entry.configure(state="disabled")

                wc_widgets[field] = entry

            # Keep total words auto-synced: sum of the five base buckets
            def update_total_words(_event=None):
                total = 0
                for base_field in ["context", "fuzzy_100", "repetitions", "fuzzy_matches", "new_words"]:
                    raw_value = wc_widgets[base_field].get().strip()
                    if raw_value:
                        try:
                            total += int(raw_value)
                        except ValueError:
                            # Ignore partial non-numeric typing; strict validation happens on save
                            pass

                total_widget = wc_widgets["total_words"]
                total_widget.configure(state="normal")
                total_widget.delete(0, "end")
                total_widget.insert(0, str(total))
                total_widget.configure(state="disabled")

            for base_field in ["context", "fuzzy_100", "repetitions", "fuzzy_matches", "new_words"]:
                wc_widgets[base_field].bind("<KeyRelease>", update_total_words)

            # Initialize computed total for new sections
            update_total_words()
            
            lp_entries.append({
                "frame": lp_section_frame,
                "source_var": source_var,
                "target_var": target_var,
                "wc_widgets": wc_widgets
            })
        
        # Create initial LP section
        create_lp_section(main_frame)
        
        # Button frame
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        def add_lp_section():
            """Add another LP section"""
            create_lp_section(main_frame)
            dialog.after(100, lambda: main_frame._parent_canvas.yview_moveto(1.0))  # Scroll to bottom
        
        ctk.CTkButton(
            button_frame,
            text="+ Add Another LP",
            command=add_lp_section,
            width=150,
            height=28,
            font=("Arial", 9),
            fg_color="#3498db",
            hover_color="#2980b9"
        ).pack(side="left", padx=5)
        
        def on_ok():
            """Save manual WC data and refresh services"""
            try:
                # Validate and collect data
                saved_count = 0
                new_lps = []

                for entry_data in lp_entries:
                    source_lang = entry_data["source_var"].get().strip()
                    target_lang = entry_data["target_var"].get().strip()

                    if not source_lang or not target_lang:
                        messagebox.showerror("Missing Language", "Please select both Source and Target languages")
                        return

                    if source_lang == target_lang:
                        messagebox.showerror("Invalid Language Pair", "Source and Target cannot be the same")
                        return

                    if language_choices:
                        if source_lang not in language_choices or target_lang not in language_choices:
                            messagebox.showerror(
                                "Invalid Language",
                                "Please select Source and Target from the rate card language list"
                            )
                            return

                    lp_name = f"{source_lang} > {target_lang}"

                    wc_data = {}

                    # Validate numeric fields (total_words is auto-calculated and disabled)
                    for field in ["context", "fuzzy_100", "repetitions", "fuzzy_matches", "new_words"]:
                        widget = entry_data["wc_widgets"][field]
                        value_str = widget.get().strip()
                        if value_str:
                            try:
                                wc_data[field] = int(value_str)
                            except ValueError:
                                messagebox.showerror("Invalid Input", f"'{field}' must be a whole number")
                                return

                    # Always store auto-calculated total_words
                    wc_data["total_words"] = (
                        wc_data.get("context", 0)
                        + wc_data.get("fuzzy_100", 0)
                        + wc_data.get("repetitions", 0)
                        + wc_data.get("fuzzy_matches", 0)
                        + wc_data.get("new_words", 0)
                    )

                    if wc_data["total_words"] <= 0:
                        messagebox.showerror("No Data", "Please enter at least one word count value greater than zero")
                        return

                    self.manual_wc_data[lp_name] = wc_data
                    saved_count += 1

                    # Add to language_pairs if not already there
                    if lp_name not in self.language_pairs:
                        self.language_pairs.append(lp_name)
                        new_lps.append(lp_name)

                    print(f"[DEBUG] Stored manual WC for {lp_name}: {wc_data}")

                if saved_count == 0:
                    messagebox.showwarning("No Data", "Please enter at least one word count value")
                    return

                dialog.grab_release()
                dialog.destroy()
                self._manual_wc_dialog = None

                # Refresh services table with new data if workflow selected
                if self.selected_workflow:
                    services = self.account_workflow_manager.get_workflow_services(
                        self.current_account,
                        self.selected_workflow
                    )
                    self.populate_services_table(services)
                    self.update_quantities_from_quoteme(self.selected_workflow)
                    if new_lps:
                        messagebox.showinfo(
                            "Success",
                            f"Manual WC data applied ({saved_count} LP(s) saved).\nAdded LP column(s): {', '.join(new_lps)}"
                        )
                    else:
                        messagebox.showinfo("Success", f"Manual WC data applied ({saved_count} LP(s) saved)")
                else:
                    messagebox.showinfo(
                        "Success",
                        f"Manual WC data saved ({saved_count} LP(s) saved)\n\nNow select a workflow to view services with this data"
                    )
            except Exception as e:
                messagebox.showerror("Error", f"Error saving WC data: {e}")
        
        def on_cancel():
            """Close dialog without saving"""
            dialog.grab_release()
            dialog.destroy()
            self._manual_wc_dialog = None
        
        ctk.CTkButton(
            button_frame,
            text="OK",
            command=on_ok,
            width=150,
            height=28,
            font=("Arial", 9, "bold"),
            fg_color="#27ae60",
            hover_color="#229954"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=on_cancel,
            width=150,
            height=28,
            font=("Arial", 9),
            fg_color="#95a5a6",
            hover_color="#7f8c8d"
        ).pack(side="left", padx=5)
    
    def _on_rush_rate_changed(self, event=None):
        """Handle rush rate value change.

        Snapshot current user-entered quantities for all non-Rush services so they
        are restored exactly after the table rebuild, then run only the Rush Premium
        recalculation on top of them.
        """
        try:
            rush_value_str = self.rush_rate_entry.get().strip()

            if rush_value_str:
                self.rush_rate_value = float(rush_value_str)
                print(f"[DEBUG] Rush rate set to: {self.rush_rate_value}%")
            else:
                self.rush_rate_value = None
                print(f"[DEBUG] Rush rate cleared")

            if not self.selected_workflow:
                return

            # --- Snapshot current table values before rebuild ---
            saved_quantities: dict = {}   # {service_name: {lp: qty_str}}
            saved_rates: dict = {}        # {service_name: {lp: rate_str}}
            for svc, lp_map in self.workflow_service_widgets.items():
                saved_quantities[svc] = {}
                saved_rates[svc] = {}
                for lp, widgets in lp_map.items():
                    try:
                        saved_quantities[svc][lp] = widgets["quantity"].get()
                        saved_rates[svc][lp] = widgets["rate"].get()
                    except Exception:
                        pass

            services = self.account_workflow_manager.get_workflow_services(
                self.current_account,
                self.selected_workflow
            )
            # Rebuild the table (adds/removes Rush Premium row)
            self.populate_services_table(services)

            # --- Restore saved values for every service except Rush Premium ---
            for svc, lp_map in self.workflow_service_widgets.items():
                if svc == "Rush Premium":
                    continue
                for lp, widgets in lp_map.items():
                    saved_qty = saved_quantities.get(svc, {}).get(lp)
                    saved_rate = saved_rates.get(svc, {}).get(lp)
                    if saved_qty is not None:
                        try:
                            widgets["quantity"].delete(0, "end")
                            widgets["quantity"].insert(0, saved_qty)
                        except Exception:
                            pass
                    if saved_rate is not None:
                        try:
                            widgets["rate"].delete(0, "end")
                            widgets["rate"].insert(0, saved_rate)
                        except Exception:
                            pass

            # Now recalculate only Rush Premium on top of restored values
            self._recalculate_rush_premium_from_current_table()

        except ValueError:
            pass

    def _schedule_rush_recalculation(self, event=None):
        """Debounce Rush Premium recalculation when table values change."""
        if not self.selected_workflow:
            return
        if self.rush_rate_value is None or self.rush_rate_value <= 0:
            return
        if "Rush Premium" not in self.workflow_service_widgets:
            return

        if hasattr(self, "_rush_recalc_after_id") and self._rush_recalc_after_id:
            try:
                self.root.after_cancel(self._rush_recalc_after_id)
            except Exception:
                pass

        self._rush_recalc_after_id = self.root.after(150, self._recalculate_rush_premium_from_current_table)

    def _recalculate_rush_premium_from_current_table(self):
        """Recalculate Rush Premium from current table values without resetting other services."""
        self._rush_recalc_after_id = None

        if not self.selected_workflow:
            return
        if self.rush_rate_value is None or self.rush_rate_value <= 0:
            return
        if "Rush Premium" not in self.workflow_service_widgets:
            return

        rush_qty = self.rush_rate_value / 100.0

        for lp in self.language_pairs:
            total_cost = 0.0
            for service, lp_map in self.workflow_service_widgets.items():
                if service == "Rush Premium":
                    continue
                if lp not in lp_map:
                    continue
                try:
                    qty_str = lp_map[lp]["quantity"].get().strip()
                    rate_str = lp_map[lp]["rate"].get().strip()
                    if qty_str and rate_str:
                        total_cost += float(qty_str) * float(rate_str)
                except (ValueError, KeyError):
                    pass

            try:
                widgets = self.workflow_service_widgets["Rush Premium"][lp]
                widgets["quantity"].delete(0, "end")
                widgets["quantity"].insert(0, str(rush_qty))
                widgets["rate"].delete(0, "end")
                widgets["rate"].insert(0, str(total_cost))
                print(f"[DEBUG]   ✓ Live Rush Premium recalc for {lp}: Qty={rush_qty}, Rate={total_cost}")
            except KeyError:
                pass

    def _recalculate_fee_rates_from_table(self):
        """Recalculate Fee service rates (SUMPRODUCT of all services above them) from current table values.

        Called when user edits an Hourly quantity so that downstream Fee services stay correct.
        """
        if not self.workflow_service_widgets:
            return

        service_order = list(self.workflow_service_widgets.keys())
        lps = list(next(iter(self.workflow_service_widgets.values())).keys())

        for svc_idx, svc in enumerate(service_order):
            svc_lp_data = self.workflow_service_widgets.get(svc, {})
            # Detect Fee services by stored metadata or by quoteme_value_mapper
            first_lp_data = next(iter(svc_lp_data.values()), {}) if svc_lp_data else {}
            svc_type = first_lp_data.get("service_type", "Word") if isinstance(first_lp_data, dict) else "Word"
            if svc_type != "Fee":
                continue

            for lp in lps:
                if lp not in svc_lp_data:
                    continue
                sumproduct = 0.0
                for prev_idx in range(svc_idx):
                    prev_svc = service_order[prev_idx]
                    prev_lp_data = self.workflow_service_widgets.get(prev_svc, {})
                    if lp not in prev_lp_data:
                        continue
                    try:
                        qty = float(prev_lp_data[lp]["quantity"].get().strip() or "0")
                        rate = float(prev_lp_data[lp]["rate"].get().strip() or "0")
                        sumproduct += qty * rate
                    except (ValueError, KeyError):
                        pass

                try:
                    svc_lp_data[lp]["rate"].delete(0, "end")
                    svc_lp_data[lp]["rate"].insert(0, str(sumproduct))
                except Exception:
                    pass

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
        
        # Build available rate-card services for "Rate Source Service" dropdown
        available_rate_services = []
        card_for_services = self.cached_rate_card if self.cached_rate_card else (
            self.load_rate_card(self.selected_rate_card) if self.selected_rate_card else {}
        )
        if isinstance(card_for_services, dict):
            for lang_data in card_for_services.get("languages", {}).values():
                if isinstance(lang_data, dict) and "rates" in lang_data and isinstance(lang_data["rates"], dict):
                    for svc_name in lang_data["rates"].keys():
                        if svc_name not in available_rate_services:
                            available_rate_services.append(svc_name)
        available_rate_services = sorted(available_rate_services)

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
                    self._show_service_config_dialog(
                        dialog, 
                        svc_name, 
                        service_configs,
                        available_rate_services
                    )
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
            existing_service_cfg = self.quoteme_value_mapper.get_service_config_from_mapping(existing_mapping, service)
            if existing_service_cfg:
                existing_fields = existing_service_cfg.get("fields", [])
            
            for field in self.quoteme_value_mapper.available_fields:
                var = BooleanVar(value=(field in existing_fields))
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
            if existing_service_cfg:
                service_configs[service] = existing_service_cfg.copy()
                if not service_configs[service].get("rate_source_service"):
                    service_configs[service]["rate_source_service"] = service
            else:
                service_configs[service] = {
                    "fields": [],
                    "service_type": "Word",
                    "divider": 1.0,
                    "increment": 1.0,
                    "minimum": 0,
                    "rate_source_service": service
                }
            
            service_configs[service]["field_vars"] = field_vars
        
        # Skip prompt checkbox
        skip_prompt_var = BooleanVar(value=False)
        skip_prompt_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        skip_prompt_frame.pack(fill="x", padx=15, pady=(5, 10))
        
        ctk.CTkCheckBox(
            skip_prompt_frame,
            text="Do not show this prompt again for this workflow",
            variable=skip_prompt_var,
            font=("Arial", 9),
            onvalue=True,
            offvalue=False
        ).pack(anchor="w")
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=15, padx=15)
        
        def save_mapping():
            # Build mapping dict from checkbox states
            mapping_updates = {}
            for service, config in service_configs.items():
                field_vars = config.pop("field_vars", {})
                selected_fields = [field for field, var in field_vars.items() if var.get()]
                
                if selected_fields or config.get("service_type") != "Word":
                    # Save config even if no fields selected (might be pre-filled with hourly/fee settings)
                    config["fields"] = selected_fields
                    mapping_updates[service] = config
            
            if not mapping_updates:
                messagebox.showwarning(
                    "No Fields Selected",
                    "Please select at least one field for at least one service"
                )
                return

            # Merge updates into existing account-level mapping so other workflow mappings are preserved
            existing = self.quoteme_value_mapper.load_mapping(self.current_account)
            merged_mapping = {
                k: v for k, v in existing.items()
                if not str(k).startswith("_")
            }
            merged_mapping.update(mapping_updates)
            
            # Add skip-prompt metadata if checked
            if skip_prompt_var.get():
                skip_prompts = existing.get("_workflow_skip_prompts", {})
                skip_prompts[workflow_name] = True
                merged_mapping["_workflow_skip_prompts"] = skip_prompts
            else:
                # Preserve existing skip-prompts even if not checked this time
                if "_workflow_skip_prompts" in existing:
                    merged_mapping["_workflow_skip_prompts"] = existing["_workflow_skip_prompts"]
            
            # Save the account-level mapping
            self.quoteme_value_mapper.save_mapping(
                self.current_account,
                merged_mapping
            )

            # Persist Fee service default quantities from Service Config minimum values.
            # These defaults are applied to all LPs for each Fee service in the services table.
            try:
                fee_defaults_path = Path(__file__).parent.parent / "Core" / "accounts" / self.current_account / "fee_service_defaults.json"
                existing_defaults = {}
                if fee_defaults_path.exists():
                    with open(fee_defaults_path, 'r', encoding='utf-8') as f:
                        existing_defaults = json.load(f).get("defaults", {})

                for svc_name, svc_cfg in merged_mapping.items():
                    if str(svc_name).startswith("_"):
                        continue
                    if not isinstance(svc_cfg, dict):
                        continue
                    if svc_cfg.get("service_type") != "Fee":
                        continue

                    min_qty = svc_cfg.get("minimum")
                    if min_qty is None:
                        continue
                    try:
                        min_qty_float = float(min_qty)
                        if min_qty_float < 0:
                            min_qty_float = 0.0
                        existing_defaults[svc_name] = min_qty_float
                    except (TypeError, ValueError):
                        continue

                fee_defaults_data = {
                    "description": f"Fee Service default quantities for {self.current_account}",
                    "defaults": existing_defaults
                }
                fee_defaults_path.parent.mkdir(parents=True, exist_ok=True)
                with open(fee_defaults_path, 'w', encoding='utf-8') as f:
                    json.dump(fee_defaults_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[DEBUG] Warning: Failed to persist fee defaults from Service Config: {e}")
            
            dialog.destroy()
            
            # Refresh the services table to display quantities with new mapping
            if self.selected_workflow:
                services = self.account_workflow_manager.get_workflow_services(
                    self.current_account,
                    self.selected_workflow
                )
                self.populate_services_table(services)
        
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
    
    def _show_service_config_dialog(
        self,
        parent_dialog,
        service_name: str,
        service_configs: dict,
        available_rate_services: Optional[list] = None
    ):
        """
        Show configuration dialog for service type settings (Word, Hourly, or Fee).
        Allows setting divider, increment, minimum values, and rate source service.
        """
        config_dialog = ctk.CTkToplevel(parent_dialog)
        config_dialog.title(f"Configure: {service_name}")
        config_dialog.geometry("550x650")
        config_dialog.transient(parent_dialog)
        config_dialog.grab_set()
        
        # Center dialog
        config_dialog.update_idletasks()
        x = (config_dialog.winfo_screenwidth() // 2) - (550 // 2)
        y = (config_dialog.winfo_screenheight() // 2) - (650 // 2)
        config_dialog.geometry(f'550x650+{x}+{y}')
        
        current_config = service_configs.get(service_name, {})
        current_service_type = current_config.get("service_type", "Word")
        current_rate_source = current_config.get("rate_source_service", service_name)

        if available_rate_services is None:
            available_rate_services = []
        
        # Header
        ctk.CTkLabel(
            config_dialog,
            text=f"Service Configuration: {service_name}",
            font=("Arial", 12, "bold")
        ).pack(pady=(15, 20), padx=15)
        
        # Service Type dropdown
        type_frame = ctk.CTkFrame(config_dialog, fg_color="transparent")
        type_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(
            type_frame,
            text="Service Type:",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")
        
        service_type_var = ctk.StringVar(value=current_service_type)
        service_type_dropdown = ctk.CTkComboBox(
            type_frame,
            values=["Word", "Hourly", "Fee"],
            variable=service_type_var,
            state="readonly",
            font=("Arial", 10),
            height=32
        )
        service_type_dropdown.pack(fill="x", pady=(5, 0))

        # Rate source service dropdown
        rate_source_frame = ctk.CTkFrame(config_dialog, fg_color="transparent")
        rate_source_frame.pack(fill="x", padx=30, pady=10)

        ctk.CTkLabel(
            rate_source_frame,
            text="Rate Source Service (from loaded rate card):",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")

        rate_source_values = [service_name]
        for svc_name in available_rate_services:
            if svc_name not in rate_source_values:
                rate_source_values.append(svc_name)

        rate_source_var = ctk.StringVar(
            value=current_rate_source if current_rate_source in rate_source_values else service_name
        )

        rate_source_dropdown = ctk.CTkComboBox(
            rate_source_frame,
            values=rate_source_values,
            variable=rate_source_var,
            state="readonly",
            font=("Arial", 10),
            height=32
        )
        rate_source_dropdown.pack(fill="x", pady=(5, 0))
        
        # Info labels for each service type
        info_frame = ctk.CTkFrame(config_dialog, fg_color="#2b2b2b", corner_radius=6)
        info_frame.pack(fill="x", padx=30, pady=10)
        
        word_info = ctk.CTkLabel(
            info_frame,
            text="Word: Standard word count (sum of selected fields)",
            font=("Arial", 9),
            text_color="#b0c4de",
            justify="left",
            wraplength=450
        )
        word_info.pack(padx=10, pady=10, anchor="w")
        
        hourly_info = ctk.CTkLabel(
            info_frame,
            text="Hourly: Calculate as MAX(CEILING(total_words/divider, increment), minimum)",
            font=("Arial", 9),
            text_color="#b0c4de",
            justify="left",
            wraplength=450
        )
        hourly_info.pack(padx=10, pady=10, anchor="w")
        
        fee_info = ctk.CTkLabel(
            info_frame,
            text="Fee: Rate = SUMPRODUCT(Qty*Rate) of all Word/Hourly/Fee services above (enter qty manually)",
            font=("Arial", 9),
            text_color="#b0c4de",
            justify="left",
            wraplength=450
        )
        fee_info.pack(padx=10, pady=10, anchor="w")
        
        # Separator
        separator = ctk.CTkFrame(config_dialog, height=1, fg_color="gray40")
        separator.pack(fill="x", padx=30, pady=10)
        
        # Hourly settings frame (scrollable if needed)
        settings_frame = ctk.CTkFrame(config_dialog, fg_color="transparent")
        settings_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        # Divider field
        divider_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        divider_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            divider_frame,
            text="Divider (e.g., 1000 for hourly rate):",
            font=("Arial", 10)
        ).pack(anchor="w")
        
        divider_entry = ctk.CTkEntry(
            divider_frame,
            placeholder_text="1.0",
            font=("Arial", 10),
            height=32
        )
        divider_entry.pack(fill="x", pady=(5, 0))
        divider_entry.insert(0, str(current_config.get("divider", 1.0)))
        
        # Increment field
        increment_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        increment_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            increment_frame,
            text="Increment (rounding unit, e.g., 0.5):",
            font=("Arial", 10)
        ).pack(anchor="w")
        
        increment_entry = ctk.CTkEntry(
            increment_frame,
            placeholder_text="1.0",
            font=("Arial", 10),
            height=32
        )
        increment_entry.pack(fill="x", pady=(5, 0))
        increment_entry.insert(0, str(current_config.get("increment", 1.0)))
        
        # Minimum field
        minimum_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        minimum_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            minimum_frame,
            text="Minimum Value (e.g., 0.5):",
            font=("Arial", 10)
        ).pack(anchor="w")
        
        minimum_entry = ctk.CTkEntry(
            minimum_frame,
            placeholder_text="0.0",
            font=("Arial", 10),
            height=32
        )
        minimum_entry.pack(fill="x", pady=(5, 0))
        minimum_entry.insert(0, str(current_config.get("minimum", 0.0)))
        
        # Help text
        help_label = ctk.CTkLabel(
            config_dialog,
            text="Example: 640 words ÷ 1000 = 0.64 → CEILING to 0.5 = 1.0 → MAX with min 0.5 = 1.0",
            font=("Arial", 8),
            text_color="gray",
            wraplength=450
        )
        help_label.pack(padx=30, pady=(5, 10))
        
        # Buttons
        btn_frame = ctk.CTkFrame(config_dialog, fg_color="transparent")
        btn_frame.pack(pady=15)
        
        def save_config():
            try:
                divider = float(divider_entry.get() or 1.0)
                increment = float(increment_entry.get() or 1.0)
                minimum = float(minimum_entry.get() or 0.0)
                
                if divider <= 0:
                    messagebox.showerror("Invalid", "Divider must be greater than 0")
                    return
                if increment <= 0:
                    messagebox.showerror("Invalid", "Increment must be greater than 0")
                    return
                
                service_configs[service_name]["service_type"] = service_type_var.get()
                service_configs[service_name]["rate_source_service"] = rate_source_var.get().strip() or service_name
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
            height=32,
            fg_color="#2b7dbc",
            font=("Arial", 10, "bold")
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Close",
            command=config_dialog.destroy,
            width=120,
            height=32,
            fg_color="gray",
            font=("Arial", 10)
        ).pack(side="left", padx=5)
    
    
    def set_language_pairs_from_quoteme(self, quoteme_data):
        """
        Set language pairs from parsed QuoteMe data
        
        Args:
            quoteme_data: List of LanguagePairData objects from QuoteMe parser
        """
        print(f"\n[DEBUG] set_language_pairs_from_quoteme called")
        print(f"[DEBUG] quoteme_data type: {type(quoteme_data)}, length: {len(quoteme_data) if quoteme_data else 'None'}")
        
        self.quoteme_data = quoteme_data
        self.language_pairs = []
        
        if quoteme_data:
            for idx, lp_data in enumerate(quoteme_data):
                if lp_data.lp_code:
                    # Extract only the language pair name ("Source > Target") without parsed data
                    lp_name = self._extract_lp_name(lp_data.lp_code)
                    self.language_pairs.append(lp_name)
                    print(f"[DEBUG] LP {idx}: {lp_name}")
        
        print(f"[DEBUG] Total language pairs loaded: {len(self.language_pairs)}")
        
        # Refresh the services table to show the new language pairs
        if self.selected_workflow and self.current_account:
            print(f"[DEBUG] Refreshing services table for workflow: {self.selected_workflow}")
            services = self.account_workflow_manager.get_workflow_services(
                self.current_account,
                self.selected_workflow
            )
            if services:
                self.populate_services_table(services)
        else:
            print(f"[DEBUG] Cannot refresh services - selected_workflow: {self.selected_workflow}, current_account: {self.current_account}")
    
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
        """Handle rate card selection - update rates in table and load currency settings"""
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
            
            # Load and display native currency from rate card
            native_currency = rate_card.get("native_currency", "USD")
            self.native_currency_label.configure(text=native_currency)
            print(f"[DEBUG] Native Currency set to: {native_currency}")
            
            # Load target currency and conversion rate for this rate card
            self._load_currency_conversion(rate_card_name)
            
            # Check and prompt for min fee thresholds if not set
            clean_rc_name = rate_card_name.replace("[Master] ", "")
            self._check_and_show_min_fee_dialog(clean_rc_name)
        else:
            display_name = rate_card_name.replace("[Master] ", "")
            self.rate_card_info.configure(text=f"⚠️ Failed to load rate card: {display_name}")
            # Reset currency to default
            self.native_currency_label.configure(text="USD")
            self.target_currency_dropdown.set("USD")
            self.conversion_rate_entry.delete(0, "end")
            self.conversion_rate_entry.insert(0, "1.0")
    
    def _get_currency_conversion_path(self) -> Path:
        """Get the path for storing currency conversion rates for an account"""
        if not self.current_account:
            return None
        
        conversion_dir = Path(__file__).parent.parent / "Core" / "accounts" / self.current_account
        conversion_dir.mkdir(parents=True, exist_ok=True)
        return conversion_dir / "currency_conversions.json"
    
    def _load_currency_conversion(self, rate_card_name: str):
        """Load saved currency and conversion rate for a specific rate card"""
        conv_path = self._get_currency_conversion_path()
        if not conv_path or not conv_path.exists():
            # Default to USD and 1.0
            self.target_currency_dropdown.set("USD")
            self.conversion_rate_entry.delete(0, "end")
            self.conversion_rate_entry.insert(0, "1.0")
            return
        
        try:
            with open(conv_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Get clean rate card name (remove [Master] prefix)
            clean_name = rate_card_name.replace("[Master] ", "")
            conversions = data.get("conversions", {})
            
            if clean_name in conversions:
                conv_data = conversions[clean_name]
                target_currency = conv_data.get("target_currency", "USD")
                rate = conv_data.get("rate", 1.0)
                
                self.target_currency_dropdown.set(target_currency)
                self.conversion_rate_entry.delete(0, "end")
                self.conversion_rate_entry.insert(0, str(rate))
                print(f"[DEBUG] Loaded conversion: {target_currency} @ {rate}")
            else:
                # New rate card - use defaults
                self.target_currency_dropdown.set("USD")
                self.conversion_rate_entry.delete(0, "end")
                self.conversion_rate_entry.insert(0, "1.0")
                print(f"[DEBUG] No saved conversion for {clean_name}, using defaults")
        except Exception as e:
            print(f"Error loading currency conversion: {e}")
            self.target_currency_dropdown.set("USD")
            self.conversion_rate_entry.delete(0, "end")
            self.conversion_rate_entry.insert(0, "1.0")
    
    def _save_currency_and_recalculate(self):
        """Save the current target currency and conversion rate for the selected rate card, then recalculate rates"""
        if not self.selected_rate_card or not self.current_account:
            messagebox.showwarning("Error", "Please select a rate card first")
            return
        
        try:
            target_currency = self.target_currency_dropdown.get()
            rate_str = self.conversion_rate_entry.get()
            rate = float(rate_str)
            
            if rate <= 0:
                messagebox.showerror("Invalid", "Conversion rate must be greater than 0")
                return
            
            conv_path = self._get_currency_conversion_path()
            
            # Load existing data or create new
            if conv_path.exists():
                with open(conv_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"description": f"Currency conversions for account {self.current_account}", "conversions": {}}
            
            # Get clean rate card name
            clean_name = self.selected_rate_card.replace("[Master] ", "")
            
            # Update or create entry
            if "conversions" not in data:
                data["conversions"] = {}
            
            data["conversions"][clean_name] = {
                "target_currency": target_currency,
                "rate": rate
            }
            
            # Save to file
            with open(conv_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"[DEBUG] Saved conversion: {clean_name} - {target_currency} @ {rate}")
            
            # Recalculate rates in the table
            self._recalculate_rates(rate)
            
            messagebox.showinfo("Success", f"Saved & Applied: {clean_name} - {target_currency} @ {rate}")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid conversion rate (number)")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save currency conversion: {e}")
    
    def _on_target_currency_changed(self, new_currency: str):
        """Handle when target currency is changed - trigger recalculation"""
        print(f"[DEBUG] Target Currency changed to: {new_currency}")
        
        try:
            rate_str = self.conversion_rate_entry.get()
            if rate_str:
                rate = float(rate_str)
                if rate > 0:
                    self._recalculate_rates(rate)
                    print(f"[DEBUG] Rates recalculated with {new_currency} @ {rate}")
        except ValueError:
            print(f"[DEBUG] Could not parse conversion rate: {rate_str}")
    
    def _check_and_show_min_fee_dialog(self, rate_card_name: str):
        """Check if min fee thresholds exist, if not show dialog to add them"""
        if not self.current_account:
            return
        
        # Check if min_fees already exist
        if self.service_mapper.min_fee_exists(self.current_account, rate_card_name):
            print(f"[DEBUG] Min fee thresholds already exist for {rate_card_name}")
            return
        
        # Show dialog to add min_fees
        self._show_min_fee_configuration_dialog(rate_card_name)
    
    def _show_min_fee_configuration_dialog(self, rate_card_name: str):
        """Show dialog for user to configure min fee thresholds"""
        if not self.current_account:
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Min Fee Thresholds - {rate_card_name}")
        dialog.geometry("500x300")
        dialog.resizable(False, False)
        
        # Header
        header = ctk.CTkFrame(dialog, fg_color="#1f538d", height=60)
        header.pack(fill="x", padx=0, pady=(0, 10))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text=f"Configure Min Fee Thresholds for {rate_card_name}",
            font=("Arial", 13, "bold"),
            text_color="white"
        ).pack(pady=15)
        
        # Instructions
        ctk.CTkLabel(
            dialog,
            text="Define minimum fee thresholds for Front Translation (FT) and Back Translation (BT).\nLeave blank to skip.",
            font=("Arial", 10),
            text_color="#bdc3c7"
        ).pack(padx=15, pady=(10, 15))
        
        # FT_Min frame
        ft_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        ft_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            ft_frame,
            text="FT_Min (Front Translation Minimum):",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")
        
        ft_min_var = ctk.StringVar()
        ft_min_entry = ctk.CTkEntry(
            ft_frame,
            textvariable=ft_min_var,
            placeholder_text="e.g., 90.00",
            font=("Arial", 11),
            width=300
        )
        ft_min_entry.pack(anchor="w", pady=5)
        
        # BT_Min frame
        bt_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        bt_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            bt_frame,
            text="BT_Min (Back Translation Minimum):",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")
        
        bt_min_var = ctk.StringVar()
        bt_min_entry = ctk.CTkEntry(
            bt_frame,
            textvariable=bt_min_var,
            placeholder_text="e.g., 90.00",
            font=("Arial", 11),
            width=300
        )
        bt_min_entry.pack(anchor="w", pady=5)
        
        # Button frame
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=20)
        
        def save_min_fees():
            """Save min fee thresholds"""
            thresholds = {}
            
            ft_val = ft_min_var.get().strip()
            if ft_val:
                try:
                    thresholds["FT_Min"] = float(ft_val)
                except ValueError:
                    messagebox.showerror("Invalid", "FT_Min must be a number")
                    return
            
            bt_val = bt_min_var.get().strip()
            if bt_val:
                try:
                    thresholds["BT_Min"] = float(bt_val)
                except ValueError:
                    messagebox.showerror("Invalid", "BT_Min must be a number")
                    return
            
            # Save
            self.service_mapper.save_min_fee_thresholds(
                self.current_account,
                rate_card_name,
                thresholds
            )
            print(f"[DEBUG] Saved initial min fee thresholds for {rate_card_name}: {thresholds}")
            
            # IMPORTANT: If services table already has quantities, recalculate with new thresholds
            if self.workflow_service_widgets:
                print(f"[DEBUG] Recalculating min fees with new thresholds...")
                service_order = list(self.workflow_service_widgets.keys())
                self._apply_min_fee_adjustments(service_order, rate_card_name)
                print(f"[DEBUG] Min fees applied to {len(service_order)} services")
            
            messagebox.showinfo("Success", f"Min fee thresholds saved for {rate_card_name}")
            dialog.destroy()
        
        def skip():
            """Skip setting min fees for now"""
            dialog.destroy()
        
        ctk.CTkButton(
            button_frame,
            text="Save",
            command=save_min_fees,
            width=150,
            font=("Arial", 11, "bold"),
            fg_color="#27ae60",
            hover_color="#229954"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Skip",
            command=skip,
            width=150,
            font=("Arial", 11),
            fg_color="#95a5a6",
            hover_color="#7f8c8d"
        ).pack(side="left", padx=5)
    
    def open_min_fee_editor(self):
        """Open dialog to edit min fee thresholds for current rate card"""
        if not self.selected_rate_card or not self.current_account:
            messagebox.showwarning("Error", "Please select a rate card first")
            return
        
        rate_card_name = self.selected_rate_card.replace("[Master] ", "")
        self._show_min_fee_editor_dialog(rate_card_name)
    
    def _show_min_fee_editor_dialog(self, rate_card_name: str):
        """Show dialog to edit existing min fee thresholds"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"Edit Min Fee Thresholds - {rate_card_name}")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        
        # Store reference to prevent garbage collection
        self._min_fee_dialog = dialog
        
        # Make it modal
        dialog.grab_set()
        dialog.transient(self.root)
        
        # Header
        header = ctk.CTkFrame(dialog, fg_color="#1f538d", height=60)
        header.pack(fill="x", padx=0, pady=(0, 10))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text=f"Edit Min Fee Thresholds - {rate_card_name}",
            font=("Arial", 13, "bold"),
            text_color="white"
        ).pack(pady=15)
        
        # Load current thresholds
        current_thresholds = self.service_mapper.load_min_fee_thresholds(
            self.current_account,
            rate_card_name
        )
        
        # FT_Min frame
        ft_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        ft_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            ft_frame,
            text="FT_Min (Front Translation Minimum):",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")
        
        ft_min_var = ctk.StringVar(value=str(current_thresholds.get("FT_Min", "")))
        ft_min_entry = ctk.CTkEntry(
            ft_frame,
            textvariable=ft_min_var,
            placeholder_text="e.g., 90.00",
            font=("Arial", 11),
            width=300
        )
        ft_min_entry.pack(anchor="w", pady=5)
        
        # BT_Min frame
        bt_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        bt_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            bt_frame,
            text="BT_Min (Back Translation Minimum):",
            font=("Arial", 11, "bold")
        ).pack(anchor="w")
        
        bt_min_var = ctk.StringVar(value=str(current_thresholds.get("BT_Min", "")))
        bt_min_entry = ctk.CTkEntry(
            bt_frame,
            textvariable=bt_min_var,
            placeholder_text="e.g., 90.00",
            font=("Arial", 11),
            width=300
        )
        bt_min_entry.pack(anchor="w", pady=5)
        
        # Button frame
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=20)
        
        def save_changes():
            """Save updated min fee thresholds"""
            thresholds = {}
            
            ft_val = ft_min_var.get().strip()
            if ft_val:
                try:
                    thresholds["FT_Min"] = float(ft_val)
                except ValueError:
                    messagebox.showerror("Invalid", "FT_Min must be a number")
                    return
            
            bt_val = bt_min_var.get().strip()
            if bt_val:
                try:
                    thresholds["BT_Min"] = float(bt_val)
                except ValueError:
                    messagebox.showerror("Invalid", "BT_Min must be a number")
                    return
            
            # Save
            self.service_mapper.save_min_fee_thresholds(
                self.current_account,
                rate_card_name,
                thresholds
            )
            print(f"[DEBUG] Saved min fee thresholds for {rate_card_name}: {thresholds}")
            
            # IMPORTANT: Recalculate and apply min fees to services table with new thresholds
            if self.workflow_service_widgets:
                print(f"[DEBUG] Recalculating min fees with new thresholds...")
                service_order = list(self.workflow_service_widgets.keys())
                self._apply_min_fee_adjustments(service_order, rate_card_name)
                print(f"[DEBUG] Min fees reapplied to {len(service_order)} services")
            
            messagebox.showinfo("Success", f"Min fee thresholds updated for {rate_card_name}")
            dialog.grab_release()
            dialog.destroy()
            self._min_fee_dialog = None
        
        ctk.CTkButton(
            button_frame,
            text="Save Changes",
            command=save_changes,
            width=150,
            font=("Arial", 11, "bold"),
            fg_color="#27ae60",
            hover_color="#229954"
        ).pack(side="left", padx=5)
        
        def on_cancel():
            dialog.grab_release()
            dialog.destroy()
            self._min_fee_dialog = None
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=on_cancel,
            width=150,
            font=("Arial", 11),
            fg_color="#95a5a6",
            hover_color="#7f8c8d"
        ).pack(side="left", padx=5)
    
    def _recalculate_rates(self, conversion_rate: float):
        """Recalculate all service rates using the conversion rate (Word & Hourly only, not Fee)"""
        print(f"[DEBUG] _recalculate_rates called with rate: {conversion_rate}")
        
        if not hasattr(self, 'workflow_service_widgets') or not self.workflow_service_widgets:
            print(f"[DEBUG] No workflow services to recalculate")
            return
        
        # Get the original (unconverted) rates from the selected rate card
        if not self.selected_rate_card:
            print(f"[DEBUG] No rate card selected")
            return
        
        original_rate_card = self.load_rate_card(self.selected_rate_card)
        if not original_rate_card:
            print(f"[DEBUG] Could not load original rate card")
            return
        
        # For each service in the workflow, apply conversion to Word/Hourly services (NOT Fee)
        for service_name, widgets in self.workflow_service_widgets.items():
            print(f"[DEBUG] Processing service: {service_name}")
            
            # Get service type to check if it's Fee
            service_config = self.quoteme_value_mapper.get_service_config(
                self.current_account,
                service_name
            ) if hasattr(self, 'quoteme_value_mapper') else {}
            
            service_type = service_config.get("service_type", "Word")
            print(f"[DEBUG]   Service type: {service_type}")
            
            # Skip Fee services - they auto-calculate from other services
            if service_type == "Fee":
                print(f"[DEBUG]   Skipping Fee service (auto-calculated)")
                continue
            
            # Get the original rate from the rate card
            if self.selected_workflow and self.language_pairs:
                lp = self.language_pairs[0] if self.language_pairs else ""
                if lp:
                    # Extract target language from LP
                    parts = lp.split(">")
                    if len(parts) == 2:
                        target_lang = parts[1].strip()
                    else:
                        target_lang = lp
                    
                    # Get original rate from rate card
                    original_rate_str = self.get_rate_from_card(original_rate_card, service_name, target_lang)
                    if original_rate_str:
                        try:
                            original_rate = float(original_rate_str)
                            # Apply conversion
                            converted_rate = original_rate * conversion_rate
                            
                            # Update the rate widget (display only, not saved to rate card)
                            widgets["rate"].delete(0, "end")
                            widgets["rate"].insert(0, str(round(converted_rate, 4)))
                            print(f"[DEBUG]   Rate converted: {original_rate} * {conversion_rate} = {converted_rate}")
                        except ValueError:
                            print(f"[DEBUG]   Could not parse original rate: {original_rate_str}")
        
        print(f"[DEBUG] Rate recalculation complete")
    
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
                    if load_excel_rate_card is None:
                        messagebox.showerror(
                            "Missing Dependency",
                            "Excel rate card loader is not available in this environment."
                        )
                        return
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
                    
                    # Ensure native currency is set
                    if "native_currency" not in rate_card:
                        # Prompt user for native currency
                        dialog = ctk.CTkToplevel(self.root)
                        dialog.title("Set Native Currency")
                        dialog.geometry("350x150")
                        dialog.transient(self.root)
                        dialog.grab_set()
                        
                        # Center dialog
                        dialog.update_idletasks()
                        x = (dialog.winfo_screenwidth() // 2) - (350 // 2)
                        y = (dialog.winfo_screenheight() // 2) - (150 // 2)
                        dialog.geometry(f'350x150+{x}+{y}')
                        
                        ctk.CTkLabel(
                            dialog,
                            text="New rate card loaded!\nWhat is the native currency?",
                            font=("Arial", 12)
                        ).pack(pady=15)
                        
                        currency_var = ctk.StringVar(value="USD")
                        currency_dropdown = ctk.CTkComboBox(
                            dialog,
                            values=["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR", "MXN", "BRL"],
                            variable=currency_var,
                            state="readonly",
                            font=("Arial", 11),
                            width=150
                        )
                        currency_dropdown.pack(pady=10)
                        
                        def save_currency():
                            rate_card["native_currency"] = currency_var.get()
                            print(f"[DEBUG] Set native_currency to: {rate_card['native_currency']}")
                            dialog.destroy()
                        
                        ctk.CTkButton(
                            dialog,
                            text="OK",
                            command=save_currency,
                            width=150
                        ).pack(pady=10)
                        
                        dialog.wait_window()
                    else:
                        print(f"[DEBUG] Rate card already has native_currency: {rate_card['native_currency']}")
                
                # Update selection and load
                self.selected_rate_card = rate_card_name
                self.rate_card_dropdown.set(rate_card_name)
                
                # Initialize target currency conversion as USD/1.0 if not already set
                # (The on_rate_card_selected will call _load_currency_conversion)
                self.target_currency_dropdown.set("USD")
                self.conversion_rate_entry.delete(0, "end")
                self.conversion_rate_entry.insert(0, "1.0")
                
                # Update rates in table
                if rate_card:
                    self.rate_card_info.configure(text=f"✓ Using rate card: {rate_card_name}")
                    self.update_rates_in_table(rate_card)
                    
                    # Update native currency label
                    native_currency = rate_card.get("native_currency", "USD")
                    self.native_currency_label.configure(text=native_currency)
                    
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
        mapping, unmapped, conflict_report = self.service_mapper.normalize_services(
            rate_card_services,
            account_name=self.current_account,
            rate_card_name=rate_card_name
        )

        # Flag alias conflicts so the user knows some mappings are ambiguous
        if conflict_report.get("has_conflicts"):
            self.service_mapping_conflicts = conflict_report
            conflict_count = len(conflict_report.get("conflicts", {}))
            self.rate_card_info.configure(
                text=f"⚠️ {conflict_count} service alias conflict(s) detected for {rate_card_name}"
            )
            messagebox.showwarning(
                "Service Mapping Conflicts",
                f"{conflict_count} alias conflict(s) were detected for {rate_card_name}.\n\n"
                "Some saved mappings use the same alias for different canonical services.\n"
                "The card will still load, but these mappings should be reviewed."
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
        dialog.geometry("900x600")
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
            frame.pack(fill="x", pady=8, padx=20)
            
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
            dropdown.pack(side="right", fill="x", expand=True, padx=(80, 0))
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

    
    def populate_services_table(self, services: Optional[list]):
        """
        Populate the services table with workflow services and language pair columns.
        Uses pure grid layout for perfect alignment of LP headers with Qty/Rate columns.
        """
        # Clear existing widgets
        for widget in self.services_table_frame.winfo_children():
            widget.destroy()
        
        self.workflow_service_widgets = {}
        
        # Add Rush Premium service if rush rate is set (session-only, not persisted)
        services_to_display = list(services or [])  # Make a copy to avoid modifying the original
        if self.rush_rate_value is not None and self.rush_rate_value > 0:
            # Check if Rush Premium is not already in the list
            if "Rush Premium" not in [s if isinstance(s, str) else s.get("name") for s in services_to_display]:
                services_to_display.append("Rush Premium")
                print(f"[DEBUG] Added Rush Premium service (session-only)")
        
        # Load fee service defaults for this account
        fee_defaults = {}
        if self.current_account:
            fee_defaults_path = Path(__file__).parent.parent / "Core" / "accounts" / self.current_account / "fee_service_defaults.json"
            if fee_defaults_path.exists():
                try:
                    with open(fee_defaults_path, 'r', encoding='utf-8') as f:
                        fee_defaults = json.load(f).get("defaults", {})
                        print(f"[DEBUG] Loaded fee service defaults for {self.current_account}: {fee_defaults}")
                except Exception as e:
                    print(f"[DEBUG] Error loading fee defaults: {e}")
        
        if not services:
            msg_text = "Select a workflow to view services"
            
            self.services_empty_label = ctk.CTkLabel(
                self.services_table_frame,
                text=msg_text,
                font=("Arial", 10),
                text_color="gray"
            )
            self.services_empty_label.pack(expand=True, pady=20)
            return

        # Keep services visible even before LP parsing by showing a placeholder LP column.
        display_language_pairs = self.language_pairs if self.language_pairs else ["No LP (parse QuoteMe or add Manual WC)"]
        
        # Create a main table frame using grid layout
        table_frame = ctk.CTkFrame(self.services_table_frame, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Configure columns: Service column (column 0) + LP columns (2 per LP)
        table_frame.grid_columnconfigure(0, minsize=150, weight=0)  # Service column - fixed
        for lp_idx in range(len(display_language_pairs)):
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
        for lp_idx, lp in enumerate(display_language_pairs):
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
                font=("Arial", 11, "bold"),
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
        
        # Create service rows with filtering based on source type and LP direction
        print(f"\n[TABLE DISPLAY] Populating services table for workflow '{self.selected_workflow}'")
        print(f"  Source Type: {self.source_type_var.get()}")

        # If current filter combination would hide everything, show all services as a safe fallback.
        has_any_visible_service = False
        for service in services_to_display:
            if isinstance(service, dict):
                service_name = service.get("name", str(service))
            else:
                service_name = service
            for lp in display_language_pairs:
                lp_direction = self._detect_translation_direction(lp)
                if self._should_include_service(service_name, self.source_type_var.get(), lp_direction):
                    has_any_visible_service = True
                    break
            if has_any_visible_service:
                break

        bypass_filters = not has_any_visible_service
        if bypass_filters:
            print("  [TABLE DISPLAY] No services matched filters; showing all workflow services.")
        
        row_idx = 1
        for service in services_to_display:
            # Extract service name and attributes (handle both string and dict formats)
            if isinstance(service, dict):
                service_name = service.get("name", str(service))
                used_when = service.get("used_when", [])
            else:
                service_name = service
                used_when = []
            
            # Check if this service has any rows that would be visible across all LPs
            service_has_visible_rows = False
            for lp in display_language_pairs:
                lp_direction = self._detect_translation_direction(lp)
                selected_source_type = self.source_type_var.get()
                
                if self._should_include_service(service_name, selected_source_type, lp_direction):
                    service_has_visible_rows = True
                    break
            
            # Skip services that wouldn't be visible in any LP
            if not bypass_filters and not service_has_visible_rows and used_when:  # Only skip if it has attributes (defined filters)
                print(f"  [SKIP] Service '{service_name}': Not applicable for any LP with current settings")
                continue
            
            print(f"  [SHOW] Service '{service_name}' with attributes {used_when}")
            
            row_bg = "gray22" if row_idx % 2 == 1 else "gray20"
            
            # Build display text with attributes on separate lines
            display_service_name = self._get_display_service_name(service_name)
            display_text = display_service_name
            if used_when:
                attr_text = ", ".join(used_when)
                display_text = f"{display_service_name}\n({attr_text})"
            
            # Service name cell
            service_label = ctk.CTkLabel(
                table_frame,
                text=display_text,
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
            for lp_idx, lp in enumerate(display_language_pairs):
                col_qty = 1 + lp_idx * 2
                col_rate = 2 + lp_idx * 2
                
                # Get service type to check if it's a Fee service
                service_type = "Word"  # Default
                
                # Special handling for Rush Premium (session-only service)
                if service_name == "Rush Premium":
                    service_type = "Fee"  # Rush Premium is always a Fee service
                elif self.current_account:
                    try:
                        service_cfg = self.quoteme_value_mapper.get_service_config(self.current_account, service_name)
                        if service_cfg:
                            service_type = service_cfg.get("service_type", "Word")
                    except:
                        pass
                
                # Determine styling — Fee AND Hourly both get highlighted, user-editable quantity
                is_fee_service = service_type == "Fee"
                is_hourly_service = service_type == "Hourly"
                needs_highlight = is_fee_service or is_hourly_service

                # Theme-aware colors for highlighted (Fee/Hourly) services
                current_mode = ctk.get_appearance_mode()
                if is_fee_service:
                    # Fee: bright green (dark) / dark red (light)
                    if current_mode == "Light":
                        qty_border_color = "#CC0000"
                        qty_fg_color = "#FFE6E6"
                    else:
                        qty_border_color = "#00ff00"
                        qty_fg_color = "#1a3a1a"
                elif is_hourly_service:
                    # Hourly: orange (dark) / dark orange (light) – distinct from Fee
                    if current_mode == "Light":
                        qty_border_color = "#b35900"
                        qty_fg_color = "#fff3e0"
                    else:
                        qty_border_color = "#ff8c00"
                        qty_fg_color = "#2a1a00"
                else:
                    qty_border_color = "#505050"
                    qty_fg_color = "#3a3a3a"

                # Quantity entry
                quantity_entry = ctk.CTkEntry(
                    table_frame,
                    width=40,
                    height=28,
                    font=("Arial", 8),
                    placeholder_text="0",
                    fg_color=qty_fg_color,
                    border_color=qty_border_color,
                    border_width=2 if needs_highlight else 1
                )
                quantity_entry.grid(row=row_idx, column=col_qty, sticky="ew", padx=1, pady=1)

                # Recalculate Rush Premium whenever values in the services table are edited
                quantity_entry.bind("<KeyRelease>", self._schedule_rush_recalculation, add="+")
                quantity_entry.bind("<FocusOut>", self._schedule_rush_recalculation, add="+")
                quantity_entry.bind("<Return>", self._schedule_rush_recalculation, add="+")

                # Apply Fee service default quantity if available.
                # Priority: Service Config minimum (for Fee type) -> fee_service_defaults.json
                default_fee_qty = None
                if is_fee_service and service_name != "Rush Premium":
                    try:
                        cfg = self.quoteme_value_mapper.get_service_config(self.current_account, service_name)
                        if cfg and cfg.get("service_type") == "Fee":
                            default_fee_qty = cfg.get("minimum")
                    except Exception:
                        default_fee_qty = None

                    if default_fee_qty is None and service_name in fee_defaults:
                        default_fee_qty = fee_defaults[service_name]

                    if default_fee_qty is not None and str(default_fee_qty) != "":
                        quantity_entry.insert(0, str(default_fee_qty))
                        print(f"[DEBUG] Applied default quantity to {service_name}: {default_fee_qty}")

                # Store LP for binding closure with service type metadata
                service_data[lp] = {
                    "quantity": quantity_entry,
                    "rate": None,  # Placeholder, will be set later
                    "service_type": service_type,  # Store service type (Word/Hourly/Fee)
                    "original_quantity": None  # Will store original quantity before min fee adjustments
                }

                # Bind cross-LP quantity sync for Fee AND Hourly services.
                # User types in any LP column → value mirrors to all other LP columns.
                # For Hourly, also recalculate downstream Fee service rates.
                if needs_highlight:
                    def create_sync_qty_handler(svc_name, current_lp, qty_widget, is_hourly):
                        def on_qty_change(event):
                            new_qty = qty_widget.get().strip()
                            if not new_qty:
                                return
                            if svc_name in self.workflow_service_widgets:
                                for other_lp, other_widgets in self.workflow_service_widgets[svc_name].items():
                                    other_widgets["quantity"].delete(0, "end")
                                    other_widgets["quantity"].insert(0, new_qty)
                            # Always reschedule Rush Premium and, for Hourly, also recalc Fee rates
                            self._schedule_rush_recalculation()
                            if is_hourly:
                                self._recalculate_fee_rates_from_table()
                        return on_qty_change

                    handler = create_sync_qty_handler(service_name, lp, quantity_entry, is_hourly_service)
                    quantity_entry.bind("<FocusOut>", handler, add="+")
                    quantity_entry.bind("<Return>", handler, add="+")
                
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
                rate_entry.bind("<KeyRelease>", self._schedule_rush_recalculation, add="+")
                rate_entry.bind("<FocusOut>", self._schedule_rush_recalculation, add="+")
                rate_entry.bind("<Return>", self._schedule_rush_recalculation, add="+")
                
                # Update the rate entry and store original quantity
                service_data[lp]["rate"] = rate_entry
                # Store original quantity (will be used to restore when recalculating min fees)
                try:
                    original_qty = quantity_entry.get()
                    if original_qty and original_qty != "0":
                        service_data[lp]["original_quantity"] = original_qty
                except:
                    pass
            
            # Store using service name (not dict) as key for consistent access
            self.workflow_service_widgets[service_name] = service_data
            
            # Increment row for next service
            row_idx += 1
        
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
        
        # Try to populate quantities from QuoteMe mapping or Manual WC data
        if self.selected_workflow and (self.quoteme_data or self.manual_wc_data):
            self.update_quantities_from_quoteme(self.selected_workflow)
        
        # Re-bind mousewheel to all child widgets so scrolling works anywhere in the table
        self._rebind_services_mousewheel(self.services_table_frame)
    
    def _rebind_services_mousewheel(self, widget):
        """Recursively bind mousewheel scrolling to widget and all its children."""
        if not hasattr(self, '_services_table_scroll_handler'):
            return
        try:
            widget.bind("<MouseWheel>", self._services_table_scroll_handler, add="+")
        except Exception:
            pass
        for child in widget.winfo_children():
            self._rebind_services_mousewheel(child)

    def update_rates_in_table(self, rate_card: dict):
        """Update rate values in the services table from a rate card"""
        if not self.workflow_service_widgets:
            return

        # Load service configs once so we can honor rate_source_service overrides
        account_mapping = {}
        if self.current_account:
            account_mapping = self.quoteme_value_mapper.load_mapping(self.current_account)
        
        # Debug: Print rate card structure
        print("\n=== DEBUG: Rate Card Structure ===")
        if "languages" in rate_card:
            print(f"Languages in rate card: {list(rate_card['languages'].keys())}")
            # Show first language's structure
            for lang_name, lang_data in list(rate_card['languages'].items())[:1]:
                if isinstance(lang_data, dict) and "rates" in lang_data:
                    print(f"Services in {lang_name}: {list(lang_data['rates'].keys())}")
        
        for service, service_data in self.workflow_service_widgets.items():
            service_config = None
            if account_mapping:
                service_config = self.quoteme_value_mapper.get_service_config_from_mapping(account_mapping, service)

            rate_source_service = service_config.get("rate_source_service", service) if service_config else service
            if not rate_source_service:
                rate_source_service = service

            for lp, widgets in service_data.items():
                # Extract target language from language pair (e.g., "Polish" from "English > Polish")
                if ">" in lp:
                    _, target_lang = lp.split(">", 1)
                    target_lang = target_lang.strip()
                else:
                    target_lang = lp
                
                # Get rate based on target language
                rate = self.get_rate_from_card(rate_card, rate_source_service, target_lang)
                print(f"DEBUG: WorkflowService='{service}', RateSource='{rate_source_service}', LP='{lp}', Target='{target_lang}' -> Rate='{rate}'")
                
                if rate:
                    widgets["rate"].delete(0, "end")
                    widgets["rate"].insert(0, rate)
    
    def update_quantities_from_quoteme(self, workflow_name: str):
        """
        Populate service quantities from QuoteMe data or manual WC data based on saved account-level mapping.
        Each LP gets its own word count data from the corresponding quoteme_data entry or manual_wc_data.
        Handles Word, Hourly, and Fee service types with cumulative calculations for Fee services.
        """
        print(f"\n[DEBUG] update_quantities_from_quoteme called for workflow: {workflow_name}")
        print(f"[DEBUG] quoteme_data: {bool(self.quoteme_data)}, language_pairs: {self.language_pairs}, manual_wc_data: {bool(self.manual_wc_data)}")
        
        # Clear cache - new data is being processed
        self.calculated_quantities_cache = {}
        print(f"[DEBUG] Cleared calculated quantities cache")
        
        # Proceed if we have either QuoteMe data OR manual WC data
        has_quoteme_data = bool(self.quoteme_data)
        has_manual_wc_data = bool(self.manual_wc_data)
        
        if not workflow_name or (not self.language_pairs and not has_manual_wc_data):
            print(f"[DEBUG] Returning early - workflow_name: {workflow_name}, language_pairs: {bool(self.language_pairs)}, manual_wc_data: {bool(self.manual_wc_data)}")
            return
        
        if not has_quoteme_data and not has_manual_wc_data:
            print(f"[DEBUG] No QuoteMe or manual WC data available")
            return
        
        # Load the account-level mapping (shared across all workflows)
        mapping = self.quoteme_value_mapper.load_mapping(
            self.current_account
        )
        print(f"[DEBUG] Loaded account mapping from '{self.current_account}': {list(mapping.keys())}")
        
        if not mapping:
            print(f"[DEBUG] No mapping found for account '{self.current_account}' - aborting")
            return  # No mapping defined for this account
        
        # Create a mapping of LP name to its corresponding word count data
        # Supports both QuoteMe data and manual WC data
        lp_data_map = {}
        
        # Add QuoteMe data if available
        if self.quoteme_data:
            for idx, quoteme_lp_data in enumerate(self.quoteme_data):
                if quoteme_lp_data and idx < len(self.language_pairs):
                    lp_name = self.language_pairs[idx]
                    lp_data_map[lp_name] = quoteme_lp_data
                    print(f"[DEBUG] LP {idx}: '{lp_name}' -> quoteme_data")
        
        # Add manual WC data (either standalone or as override for QuoteMe)
        if self.manual_wc_data:
            import types
            for lp_name, wc_dict in self.manual_wc_data.items():
                # Create a simple object with the WC fields
                synthetic_wc = types.SimpleNamespace(
                    context=wc_dict.get("context", 0),
                    fuzzy_100=wc_dict.get("fuzzy_100", 0),
                    repetitions=wc_dict.get("repetitions", 0),
                    fuzzy_matches=wc_dict.get("fuzzy_matches", 0),
                    new_words=wc_dict.get("new_words", 0),
                    total_words=wc_dict.get("total_words", 0)
                )
                # Bind compatibility method to this specific object to avoid late-binding issues
                synthetic_wc.get_effective_wc = (lambda obj: (lambda use_cumulative=False: obj))(synthetic_wc)
                lp_data_map[lp_name] = synthetic_wc
                print(f"[DEBUG] LP: '{lp_name}' -> manual_wc_data: {wc_dict}")
        
        # Build ordered list of services (from workflow_service_widgets which preserves order)
        service_order = list(self.workflow_service_widgets.keys())
        print(f"[DEBUG] Service order from widgets: {service_order}")
        
        # Apply quantities to services based on account-level mapping
        for service_idx, service in enumerate(service_order):
            # Skip Rush Premium - it's handled separately as session-only service
            if service == "Rush Premium":
                print(f"[DEBUG] Skipping Rush Premium (session-only, calculated separately)")
                continue

            service_config = self.quoteme_value_mapper.get_service_config_from_mapping(mapping, service)
            if not service_config:
                print(f"[DEBUG] Service '{service}' NOT in mapping (even after canonical/normalized match) - skipping")
                continue

            print(f"[DEBUG] Processing service: {service}")
            service_type = service_config.get("service_type", "Word")
            print(f"[DEBUG]   Service type: {service_type}")
            print(f"[DEBUG]   Service config: {service_config}")
            
            service_data = self.workflow_service_widgets[service]
            
            for lp, widgets in service_data.items():
                print(f"[DEBUG]   Processing LP: {lp}")
                # Get the specific LP's word count data
                if lp not in lp_data_map:
                    print(f"[DEBUG]     LP '{lp}' not in lp_data_map - skipping")
                    continue
                
                lp_wc_data = lp_data_map[lp]
                
                # Get effective word count data (for QuoteMe objects with cumulative calculation)
                # For synthetic manual WC objects, just use them directly
                if hasattr(lp_wc_data, 'get_effective_wc'):
                    word_count_data = lp_wc_data.get_effective_wc(use_cumulative=True)
                else:
                    word_count_data = lp_wc_data
                
                print(f"[DEBUG]     Word count data: {word_count_data}")
                
                # Calculate quantity based on service type
                if service_type == "Fee":
                    # Fee service: SUMPRODUCT of (Quantity * Rate) for all services above it
                    # This includes Word, Hourly, AND other Fee services (cumulative)
                    # IMPORTANT: For Fee services, the SUMPRODUCT becomes the RATE, not the quantity
                    fee_value = 0.0
                    for prev_idx in range(service_idx):
                        prev_service = service_order[prev_idx]
                        if prev_service not in self.workflow_service_widgets:
                            continue
                        
                        try:
                            # Get Qty and Rate for previous service at this LP
                            prev_qty_str = self.workflow_service_widgets[prev_service][lp]["quantity"].get()
                            prev_rate_str = self.workflow_service_widgets[prev_service][lp]["rate"].get()
                            
                            if prev_qty_str and prev_rate_str:
                                prev_qty = float(prev_qty_str)
                                prev_rate = float(prev_rate_str)
                                fee_value += prev_qty * prev_rate
                        except (ValueError, KeyError):
                            pass
                    
                    # For Fee services, SUMPRODUCT becomes the RATE (quantity defaults to 1)
                    widgets["rate"].delete(0, "end")
                    widgets["rate"].insert(0, str(fee_value))
                    print(f"[DEBUG]     Fee service - Set rate to: {fee_value}")

                    # Set quantity from Fee default (Service Config minimum), fallback to 1
                    fee_qty_value = service_config.get("minimum", 1)
                    try:
                        fee_qty_value = float(fee_qty_value)
                    except (TypeError, ValueError):
                        fee_qty_value = 1.0

                    if fee_qty_value < 0:
                        fee_qty_value = 0.0

                    widgets["quantity"].delete(0, "end")
                    widgets["quantity"].insert(0, str(fee_qty_value))
                    print(f"[DEBUG]     Fee service - Set quantity to default: {fee_qty_value}")

                    # Cache the calculated quantity for this service/LP
                    if service not in self.calculated_quantities_cache:
                        self.calculated_quantities_cache[service] = {}
                    self.calculated_quantities_cache[service][lp] = str(fee_qty_value)
                    print(f"[DEBUG]     Cached quantity for {service}/{lp}: {fee_qty_value}")
                else:
                    # Word or Hourly: use normal calculation
                    quantity = self.quoteme_value_mapper.calculate_service_value(
                        word_count_data,
                        service_config
                    )
                    print(f"[DEBUG]     Calculated quantity: {quantity}")
                    
                    widgets["quantity"].delete(0, "end")
                    widgets["quantity"].insert(0, str(quantity))
                    
                    # Cache the calculated quantity for this service/LP
                    if service not in self.calculated_quantities_cache:
                        self.calculated_quantities_cache[service] = {}
                    self.calculated_quantities_cache[service][lp] = str(quantity)
                    print(f"[DEBUG]     Cached quantity for {service}/{lp}: {quantity}")
        
        # Calculate and apply Rush Premium service if rush_rate is set
        print(f"[DEBUG] Rush rate value: {self.rush_rate_value}, Rush Premium in widgets: {'Rush Premium' in self.workflow_service_widgets}")
        if self.rush_rate_value is not None and self.rush_rate_value > 0:
            print(f"[DEBUG] Calculating Rush Premium at {self.rush_rate_value}% of total cost")
            
            if "Rush Premium" not in self.workflow_service_widgets:
                print(f"[DEBUG] WARNING: Rush Premium not found in workflow_service_widgets!")
                print(f"[DEBUG] Available services: {list(self.workflow_service_widgets.keys())}")
            else:
                for lp in self.language_pairs:
                    # Calculate total cost of all services (excluding Rush Premium itself)
                    total_cost = 0.0
                    for service in service_order:
                        if service == "Rush Premium":
                            continue
                        if service not in self.workflow_service_widgets:
                            continue
                        try:
                            qty_str = self.workflow_service_widgets[service][lp]["quantity"].get()
                            rate_str = self.workflow_service_widgets[service][lp]["rate"].get()
                            if qty_str and rate_str:
                                total_cost += float(qty_str) * float(rate_str)
                                print(f"[DEBUG]     {service}: {qty_str} * {rate_str} = {float(qty_str) * float(rate_str)}, running total: {total_cost}")
                        except (ValueError, KeyError) as e:
                            print(f"[DEBUG]     Error calculating {service}: {e}")
                            pass
                    
                    # Rush Premium model:
                    #   Qty = rush percentage as decimal (e.g., 15 -> 0.15)
                    #   Rate = total cost of services above
                    rush_premium_qty = self.rush_rate_value / 100.0
                    rush_premium_rate = total_cost
                    
                    try:
                        widgets = self.workflow_service_widgets["Rush Premium"][lp]
                        widgets["quantity"].delete(0, "end")
                        widgets["quantity"].insert(0, str(rush_premium_qty))
                        widgets["rate"].delete(0, "end")
                        widgets["rate"].insert(0, str(rush_premium_rate))
                        print(f"[DEBUG]   ✓ Rush Premium for {lp}: Qty={rush_premium_qty}, Rate={rush_premium_rate}")
                    except KeyError as e:
                        print(f"[DEBUG]   ERROR: Failed to set Rush Premium for {lp}: {e}")

        
        # Apply min fee adjustments for each language pair
        clean_rc_name = self.selected_rate_card.replace("[Master] ", "") if self.selected_rate_card else ""
        if clean_rc_name:
            self._apply_min_fee_adjustments(service_order, clean_rc_name)

    def _apply_min_fee_adjustments(self, service_order: list, rate_card_name: str):
        """
        Apply min fee thresholds (FT_Min and BT_Min) to services.
        
        Process:
        1. Load FT_Min and BT_Min from stored config
        2. For each LP, calculate total cost of FT services
        3. If total < FT_Min: collapse FT services (MTFull Edit Proof gets qty=1, rate=FT_Min; others get qty=0)
        4. Same for BT services with BT_Min
        """
        if not self.current_account or not service_order:
            return
        
        # Load min fee thresholds
        ft_min = self.quoteme_value_mapper.get_min_fee_threshold_from_file(
            self.current_account,
            rate_card_name,
            "FT_Min"
        )
        bt_min = self.quoteme_value_mapper.get_min_fee_threshold_from_file(
            self.current_account,
            rate_card_name,
            "BT_Min"
        )
        
        if not ft_min and not bt_min:
            print(f"[DEBUG] No min fee thresholds configured for {rate_card_name}")
            return
        
        print(f"[DEBUG] Applying min fee adjustments - FT_Min: {ft_min}, BT_Min: {bt_min}")
        
        # Process each language pair
        first_service = self.workflow_service_widgets.get(service_order[0]) if service_order else None
        if not first_service:
            return
        
        # Debug: Log which services are identified as FT/BT with canonical mapping
        service_classifications = {}
        for service in service_order:
            canonical = self.quoteme_value_mapper._find_canonical_service_name(service)
            is_ft = self.quoteme_value_mapper.is_ft_service(service)
            is_bt = self.quoteme_value_mapper.is_bt_service(service)
            classification = "FT" if is_ft else ("BT" if is_bt else "Fee/Other")
            service_classifications[service] = {"canonical": canonical, "type": classification}
            print(f"[DEBUG] Service: '{service}' → Canonical: '{canonical}' → Type: {classification}")
        
        ft_services_list = [s for s, info in service_classifications.items() if info["type"] == "FT"]
        bt_services_list = [s for s, info in service_classifications.items() if info["type"] == "BT"]
        print(f"[DEBUG] Identified FT services: {ft_services_list}")
        print(f"[DEBUG] Identified BT services: {bt_services_list}")

        # Load account-level QuoteMe mapping once for FT_Min target service selection.
        # FT_Min should apply to the FT service that carries New Words in the current workflow.
        account_mapping = self.quoteme_value_mapper.load_mapping(self.current_account)
        
        for lp in first_service.keys():
            # FIRST: Restore quantities from cache (original calculated values from QuoteMe)
            print(f"[DEBUG] Restoring quantities from cache for LP '{lp}'...")
            for service in service_order:
                if service not in self.workflow_service_widgets:
                    continue
                
                # Check if we have cached quantity
                if service in self.calculated_quantities_cache and lp in self.calculated_quantities_cache[service]:
                    cached_qty = self.calculated_quantities_cache[service][lp]
                    service_lp_data = self.workflow_service_widgets[service].get(lp)
                    if service_lp_data:
                        service_lp_data["quantity"].delete(0, "end")
                        service_lp_data["quantity"].insert(0, cached_qty)
                        print(f"[DEBUG]   ✓ Restored {service} to cached quantity: {cached_qty}")
            
            # SECOND: Store original quantities in widget metadata (for reference during this session)
            print(f"[DEBUG] Storing original quantities for LP '{lp}'...")
            for service in service_order:
                if service not in self.workflow_service_widgets:
                    continue
                service_lp_data = self.workflow_service_widgets[service].get(lp)
                if service_lp_data:
                    current_qty = service_lp_data["quantity"].get()
                    if current_qty and current_qty != "0":
                        service_lp_data["original_quantity"] = current_qty
                        print(f"[DEBUG]   Stored original quantity for {service}: {current_qty}")
# Restore original quantities (for re-calculation when threshold changes)
            print(f"[DEBUG] Restoring original quantities for LP '{lp}'...")
            for service in service_order:
                if service not in self.workflow_service_widgets:
                    continue
                service_lp_data = self.workflow_service_widgets[service].get(lp)
                if service_lp_data and service_lp_data.get("original_quantity"):
                    original_qty = service_lp_data["original_quantity"]
                    service_lp_data["quantity"].delete(0, "end")
                    service_lp_data["quantity"].insert(0, original_qty)
                    print(f"[DEBUG]   Restored {service} to original quantity: {original_qty}")
            
            # Calculate FT services total cost (WORD SERVICES ONLY - EXCLUDE BT)
            ft_total_cost = 0.0
            ft_services = []
            
            for service in service_order:
                if service not in self.workflow_service_widgets:
                    continue
                
                # Explicitly exclude BT services (Back Translation)
                if self.quoteme_value_mapper.is_bt_service(service):
                    print(f"[DEBUG]   Skipping '{service}' - it's a BT service (only used for BT_min, not FT_min)")
                    continue
                
                if self.quoteme_value_mapper.is_ft_service(service):
                    service_widgets = self.workflow_service_widgets[service].get(lp)
                    service_type = service_widgets.get("service_type", "Word") if service_widgets else "Word"
                    
                    # Only include WORD services in FT calculation (exclude Hourly)
                    if service_type != "Word":
                        print(f"[DEBUG]   Skipping FT service '{service}' - not a Word service (type={service_type})")
                        continue
                    
                    ft_services.append(service)
                    try:
                        qty_str = self.workflow_service_widgets[service][lp]["quantity"].get()
                        rate_str = self.workflow_service_widgets[service][lp]["rate"].get()
                        if qty_str and rate_str:
                            cost = float(qty_str) * float(rate_str)
                            ft_total_cost += cost
                            print(f"[DEBUG]   FT service '{service}' in '{lp}': qty={qty_str}, rate={rate_str}, cost={cost}, total_so_far={ft_total_cost}")
                    except (ValueError, KeyError) as e:
                        print(f"[DEBUG]   Error calculating FT service '{service}': {e}")
                        pass
            
            # Apply FT_Min if threshold exceeded
            if ft_min and ft_total_cost < ft_min:
                print(f"[DEBUG] FT total cost ({ft_total_cost}) below FT_Min ({ft_min}) for LP '{lp}'")
                print(f"[DEBUG]   FT services found: {ft_services}")

                # Select FT service that takes New Words in this workflow.
                # This keeps FT_Min independent from any single canonical service label.
                ft_target_service = None
                for service in ft_services:
                    service_cfg = self.quoteme_value_mapper.get_service_config_from_mapping(account_mapping, service) if account_mapping else {}
                    mapped_fields = service_cfg.get("fields", []) if isinstance(service_cfg, dict) else []
                    if "New Words" in mapped_fields:
                        ft_target_service = service
                        print(f"[DEBUG]   ✓ Selected FT_Min target by New Words mapping: {ft_target_service}")
                        break

                # Fallback 1: preserve historical behavior when available
                if not ft_target_service:
                    for service in ft_services:
                        canonical = self.quoteme_value_mapper._find_canonical_service_name(service)
                        print(f"[DEBUG]   Checking FT fallback candidate '{service}' → canonical: '{canonical}'")
                        if canonical and "MT full" in canonical and "EditProof" in canonical:
                            ft_target_service = service
                            print(f"[DEBUG]   ✓ Selected FT_Min fallback target: {ft_target_service} (canonical MT full EditProof)")
                            break

                # Fallback 2: first FT word service in current workflow
                if not ft_target_service and ft_services:
                    ft_target_service = ft_services[0]
                    print(f"[DEBUG]   ✓ Selected FT_Min final fallback target: {ft_target_service} (first FT service)")

                if ft_target_service and ft_target_service in self.workflow_service_widgets:
                    # Set FT target service to Qty=1, Rate=FT_Min
                    widgets = self.workflow_service_widgets[ft_target_service][lp]
                    widgets["quantity"].delete(0, "end")
                    widgets["quantity"].insert(0, "1")
                    widgets["rate"].delete(0, "end")
                    widgets["rate"].insert(0, str(ft_min))
                    print(f"[DEBUG]   Applied FT_Min to {ft_target_service}: Qty=1, Rate={ft_min}")

                    # Set other FT services to Qty=0
                    for service in ft_services:
                        if service != ft_target_service:
                            try:
                                widgets = self.workflow_service_widgets[service][lp]
                                widgets["quantity"].delete(0, "end")
                                widgets["quantity"].insert(0, "0")
                                print(f"[DEBUG]   Set {service} to Qty=0")
                            except KeyError:
                                pass
            
            # Calculate BT services total cost (WORD SERVICES ONLY)
            bt_total_cost = 0.0
            bt_services = []
            
            for service in service_order:
                if service not in self.workflow_service_widgets:
                    continue
                
                if self.quoteme_value_mapper.is_bt_service(service):
                    service_widgets = self.workflow_service_widgets[service].get(lp)
                    service_type = service_widgets.get("service_type", "Word") if service_widgets else "Word"
                    
                    # Only include WORD services in BT calculation (exclude Hourly)
                    if service_type != "Word":
                        print(f"[DEBUG]   Skipping BT service '{service}' - not a Word service (type={service_type})")
                        continue
                    
                    bt_services.append(service)
                    try:
                        qty_str = self.workflow_service_widgets[service][lp]["quantity"].get()
                        rate_str = self.workflow_service_widgets[service][lp]["rate"].get()
                        if qty_str and rate_str:
                            bt_total_cost += float(qty_str) * float(rate_str)
                    except (ValueError, KeyError):
                        pass
            
            # Apply BT_Min if threshold exceeded
            if bt_min and bt_total_cost < bt_min:
                print(f"[DEBUG] BT total cost ({bt_total_cost}) below BT_Min ({bt_min}) for LP '{lp}'")
                
                # Find main BT service to apply min fee to using canonical matching
                bt_service = None
                for service in bt_services:
                    canonical = self.quoteme_value_mapper._find_canonical_service_name(service)
                    print(f"[DEBUG]   Checking BT service '{service}' → canonical: '{canonical}'")
                    if canonical and canonical == "Back Translation":
                        bt_service = service
                        print(f"[DEBUG]   ✓ Found Back Translation service: {bt_service} (canonical: {canonical})")
                        break
                
                if not bt_service:
                    print(f"[DEBUG]   WARNING: No 'Back Translation' service found in BT services: {bt_services}")
                    print(f"[DEBUG]   Available canonical mappings:")
                    for service in bt_services:
                        canonical = self.quoteme_value_mapper._find_canonical_service_name(service)
                        print(f"[DEBUG]      '{service}' → '{canonical}'")
                
                if bt_service and bt_service in self.workflow_service_widgets:
                    # Set Back Translation to Qty=1, Rate=BT_Min
                    widgets = self.workflow_service_widgets[bt_service][lp]
                    widgets["quantity"].delete(0, "end")
                    widgets["quantity"].insert(0, "1")
                    widgets["rate"].delete(0, "end")
                    widgets["rate"].insert(0, str(bt_min))
                    print(f"[DEBUG]   Applied BT_Min to {bt_service}: Qty=1, Rate={bt_min}")
        
        # THIRD: Recalculate Fee services after min fees applied (since their rates depend on previous services)
        print(f"[DEBUG] Recalculating Fee services after min fee adjustments...")
        for service in service_order:
            if service not in self.workflow_service_widgets:
                continue
            
            if self.quoteme_value_mapper.is_fee_service(service):
                print(f"[DEBUG]   Recalculating Fee service: {service}")
                
                for lp in first_service.keys():
                    # Calculate SUMPRODUCT of all services BEFORE this Fee service
                    fee_value = 0.0
                    service_idx = service_order.index(service)
                    
                    for prev_idx in range(service_idx):
                        prev_service = service_order[prev_idx]
                        if prev_service not in self.workflow_service_widgets:
                            continue
                        
                        try:
                            prev_qty_str = self.workflow_service_widgets[prev_service][lp]["quantity"].get()
                            prev_rate_str = self.workflow_service_widgets[prev_service][lp]["rate"].get()
                            
                            if prev_qty_str and prev_rate_str:
                                prev_qty = float(prev_qty_str)
                                prev_rate = float(prev_rate_str)
                                fee_value += prev_qty * prev_rate
                                print(f"[DEBUG]     Added {prev_service} ({prev_qty} * {prev_rate} = {prev_qty*prev_rate}) → Total: {fee_value}")
                        except (ValueError, KeyError) as e:
                            print(f"[DEBUG]     Error processing {prev_service}: {e}")
                            pass
                    
                    # Update Fee service rate
                    if service in self.workflow_service_widgets and lp in self.workflow_service_widgets[service]:
                        widgets = self.workflow_service_widgets[service][lp]
                        widgets["rate"].delete(0, "end")
                        widgets["rate"].insert(0, str(fee_value))
                        print(f"[DEBUG]   Updated {service} rate for LP '{lp}' to: {fee_value}")

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

    def export_charges_to_csv(self):
        """
        Export charges to CSV file based on current workflow services configuration.
        Format matches the CHARGES_TEMPLATE structure from ChargesIntegration.py
        
        Filters services based on:
        - User-selected Source Type (Live Source / Dead Source)
        - Service's Used_when attributes
        - Auto-detected direction based on target language (>Eng / >For)
        """
        # Validate prerequisites
        if not self.workflow_service_widgets:
            messagebox.showwarning(
                "No Services",
                "Please select a workflow and configure services first."
            )
            return
        
        if not self.language_pairs:
            messagebox.showwarning(
                "No Language Pairs",
                "Please parse QuoteMe data to populate language pairs first."
            )
            return
        
        try:
            # Get selected source type
            selected_source_type = self.source_type_var.get()
            selected_entity = self.selected_entity_var.get().strip() if hasattr(self, "selected_entity_var") else "TPUS"
            if not selected_entity:
                selected_entity = "TPUS"

            # Load entity mapping/metadata once for this export
            from entity_service_mapper import EntityServiceMapper
            entity_mapper = EntityServiceMapper()
            selected_entity_profile = self._get_entity_service_profile(selected_entity)
            tpus_profile = self._get_entity_service_profile("TPUS")
            
            print(f"\n[EXPORT DEBUG] Starting export with SourceType='{selected_source_type}', Entity='{selected_entity}'")
            print(f"  Workflows selected: {self.selected_workflow}")
            print(f"  Language pairs: {self.language_pairs}")
            
            # Prepare charges data - grouped by LP
            charges_list = []
            
            # Iterate through language pairs (outer loop) then services (inner loop)
            for lp_name in self.language_pairs:
                # Detect direction of translation for this LP
                lp_direction = self._detect_translation_direction(lp_name)
                
                print(f"\n  [EXPORT] LP='{lp_name}', Direction='{lp_direction}'")
                
                # Get all services for this LP
                services_for_lp = []
                
                for service_name, lp_data in self.workflow_service_widgets.items():
                    if lp_name not in lp_data:
                        continue
                    
                    # Check if this service should be included based on source type and direction
                    if not self._should_include_service(service_name, selected_source_type, lp_direction):
                        continue
                    
                    entries = lp_data[lp_name]
                    
                    # Extract quantity and rate from entries
                    qty_text = entries["quantity"].get().strip()
                    rate_text = entries["rate"].get().strip()
                    
                    # Skip if both are empty or zero
                    quantity = float(qty_text) if qty_text else 0
                    rate = float(rate_text) if rate_text else 0
                    
                    if quantity == 0 and rate == 0:
                        continue
                    
                    services_for_lp.append((service_name, quantity, rate))
                    print(f"    [INCLUDE] Service='{service_name}', Qty={quantity}, Rate={rate}")
                
                # If this LP has services to export, add them to charges list
                if services_for_lp:
                    print(f"  [SUMMARY] LP '{lp_name}' has {len(services_for_lp)} service(s) to export")
                else:
                    print(f"  [SUMMARY] LP '{lp_name}' has NO services to export")
                    
                if services_for_lp:
                    for row_idx, (service_name, quantity, rate) in enumerate(services_for_lp):
                        # Mark first row of this LP with "x"
                        mark_new = "x" if row_idx == 0 else ""

                        # Resolve entity-specific service label from canonical workflow service
                        export_service_name = self._resolve_service_for_entity(
                            service_name,
                            selected_entity,
                            entity_mapper
                        )

                        # Pull SG1/SG2/UofM from selected entity service row when possible.
                        # Fallback to TPUS canonical metadata for stability.
                        entity_meta = selected_entity_profile.get(export_service_name, {})
                        if not entity_meta:
                            entity_meta = selected_entity_profile.get(service_name, {})
                        tpus_meta = tpus_profile.get(service_name, {})

                        service_group_1 = entity_meta.get("group1", "") or tpus_meta.get("group1", "")
                        service_group_2 = entity_meta.get("group2", "") or tpus_meta.get("group2", "")

                        uom_value = entity_meta.get("uom", "") or tpus_meta.get("uom", "")
                        if not uom_value:
                            svc_widgets = self.workflow_service_widgets.get(service_name, {}).get(lp_name, {})
                            uom_value = svc_widgets.get("service_type", "Word") if isinstance(svc_widgets, dict) else "Word"
                        
                        # Parse source and target from LP name using " into " delimiter
                        if " into " in lp_name:
                            parts = lp_name.split(" into ", 1)
                            source_lang = parts[0].strip()
                            target_lang = parts[1].strip()
                        else:
                            # Fallback if format is different
                            lp_parts = lp_name.split('>')
                            source_lang = lp_parts[0].strip() if len(lp_parts) > 0 else ""
                            target_lang = lp_parts[1].strip() if len(lp_parts) > 1 else ""
                        
                        # Create charge row
                        charge_row = {
                            "Mark New Line Item": mark_new,
                            "Line Item Description": lp_name,
                            "Source": source_lang,
                            "Target": target_lang,
                            "Hide Unit Costs": 0,
                            "Hide Details": 0,
                            "Service Group 1": service_group_1,
                            "Service Group 2": service_group_2,
                            "Service Group 3": "",
                            "Service": export_service_name,
                            "UofM": uom_value,
                            "Quantity": quantity,
                            "Rate": rate,
                            "CommentsForInvoice": "",
                            "Technology Product": "GL PD"
                        }
                        charges_list.append(charge_row)
            
            if not charges_list:
                messagebox.showinfo(
                    "No Charges",
                    "No services with quantities or rates to export."
                )
                return
            
            # Create DataFrame
            charges_df = pd.DataFrame(charges_list)
            
            # Prepare filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"Charges_Export_{timestamp}.csv"
            
            # Ask user where to save
            filepath = filedialog.asksaveasfilename(
                title="Save Charges Export",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=default_filename
            )
            
            if not filepath:
                return
            
            # Export to CSV
            charges_df.to_csv(filepath, index=False)
            
            self.update_status(f"✅ Charges exported to {Path(filepath).name}")
            messagebox.showinfo(
                "Export Successful",
                f"Charges exported to:\n{filepath}\n\n"
                f"Total line items: {len(charges_list)}\n"
                f"Source Type: {selected_source_type}\n"
                f"Entity: {selected_entity}"
            )
            
        except ValueError as e:
            messagebox.showerror(
                "Invalid Value",
                f"Error processing quantity or rate values:\n{str(e)}"
            )
        except Exception as e:
            messagebox.showerror(
                "Export Failed",
                f"Failed to export charges:\n{str(e)}"
            )
    
    def _detect_translation_direction(self, lp_name: str) -> str:
        """
        Auto-detect translation direction based on target language.
        Returns ">Eng" if target is English, ">For" otherwise
        """
        if " into " not in lp_name:
            print(f"    [DIRECTION] LP '{lp_name}': No ' into ' delimiter -> >For (default)")
            return ">For"  # Default
        
        parts = lp_name.split(" into ", 1)
        if len(parts) < 2:
            print(f"    [DIRECTION] LP '{lp_name}': Invalid format -> >For (default)")
            return ">For"
        
        source_lang = parts[0].strip()
        target_lang = parts[1].strip()
        
        # Check if target is English (various forms)
        if "english" in target_lang.lower():
            print(f"    [DIRECTION] {source_lang} into {target_lang} -> >Eng (English target)")
            return ">Eng"
        else:
            print(f"    [DIRECTION] {source_lang} into {target_lang} -> >For (non-English target)")
            return ">For"
    
    def _should_include_service(self, service_name: str, selected_source_type: str, lp_direction: str) -> bool:
        """
        Determine if a service should be included in the export based on:
        - Selected source type (Live Source / Dead Source)
        - Service's Used_when attributes
        - LP direction (>Eng / >For)
        """
        # Get service attributes from workflow
        if not self.current_account or not self.selected_workflow:
            print(f"  [FILTER DEBUG] {service_name}: No account/workflow -> INCLUDE (legacy)")
            return True  # Include if no account/workflow selected (legacy behavior)
        
        try:
            used_when = self.account_workflow_manager.get_service_attributes(
                self.current_account,
                self.selected_workflow,
                service_name
            )
        except Exception as e:
            used_when = []  # Default: no filters
            print(f"  [FILTER DEBUG] {service_name}: Error getting attributes ({e}) -> INCLUDE")
        
        # If service has no Used_when attributes, include it
        if not used_when:
            print(f"  [FILTER DEBUG] {service_name}: No attributes defined -> INCLUDE (legacy)")
            return True
        
        # Debug: Show what we're filtering on
        print(f"  [FILTER DEBUG] Service='{service_name}', SourceType='{selected_source_type}', LPDirection='{lp_direction}', Attributes={used_when}")
        
        # Filter based on selected source type
        if selected_source_type == "Live Source":
            # Include if service is marked for "Live" source
            include = "Live" in used_when
            print(f"    -> Live Source: 'Live' in attributes? {include}")
            return include
        else:  # Dead Source
            # Include if service matches the LP direction
            include = lp_direction in used_when
            print(f"    -> Dead Source: '{lp_direction}' in attributes? {include}")
            return include


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
                source_data, self.current_account, row_index=0
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
            var = BooleanVar(value=col in self.visible_columns)
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
