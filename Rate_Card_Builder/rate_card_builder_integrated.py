"""
Rate Card Builder - Integrated Tab Component
Embeddable module for One_Stop_Shop GUI
Provides rate card creation functionality as a tab component
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
from itemized_rate_card_window import ItemizedRateCardWindow
from load_rate_card_window import LoadRateCardWindow


class RateCardBuilderTab:
    """Embeddable Rate Card Builder component for One_Stop_Shop"""
    
    def __init__(self, parent_frame, root_window):
        """
        Initialize the Rate Card Builder Tab component.
        
        Args:
            parent_frame: Parent CTk frame to embed in
            root_window: Root window reference for creating popup windows
        """
        self.parent_frame = parent_frame
        self.root = root_window
        self.itemized_editor = None
        self.global_services_listbox = None
        self.global_service_entry = None
        self.global_service_status_label = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface with tabbed components."""
        # Main container
        main_container = ctk.CTkFrame(self.parent_frame, corner_radius=0)
        main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Header section
        header_frame = ctk.CTkFrame(main_container, corner_radius=0, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="📊 Rate Card Builder",
            font=ctk.CTkFont(size=24, weight="bold")
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
        try:
            from itemized_rate_card_editor import setup_itemized_editor
            
            # Setup the editor directly in this tab
            self.itemized_editor = setup_itemized_editor(self.tab_itemized, self.root)
        except Exception as e:
            error_label = ctk.CTkLabel(
                self.tab_itemized,
                text=f"⚠️ Failed to load Itemized Editor:\n{str(e)}",
                font=ctk.CTkFont(size=12),
                text_color="#e74c3c"
            )
            error_label.pack(expand=True, pady=50)
    
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
        
        # Buttons frame
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        # Open button
        open_button = ctk.CTkButton(
            button_frame,
            text="Open Rate Card",
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#27ae60",
            hover_color="#229954",
            command=self.on_open_rate_card
        )
        open_button.pack(side="left", padx=(0, 10), pady=10)

        # Load Master Rate Card button
        master_button = ctk.CTkButton(
            button_frame,
            text="📦 Load Master Rate Card",
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#8e44ad",  
            hover_color="#7d3c99",
            command=self.on_load_master_rate_card
        )
        master_button.pack(side="left", padx=(0, 10), pady=10)

        # Load from file button
        load_button = ctk.CTkButton(
            button_frame,
            text="Browse Files",
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#3498db",
            hover_color="#2980b9",
            command=self.on_browse_rate_cards
        )
        load_button.pack(side="left", padx=0, pady=10)
    
    def setup_settings_tab(self):
        """Setup the Settings tab."""
        content_frame = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            content_frame,
            text="Rate Card Builder Settings",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(anchor="w", pady=(0, 20))
        
        # Default services section
        services_label = ctk.CTkLabel(
            content_frame,
            text="Default Services:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        services_label.pack(anchor="w", pady=(0, 10))
        
        # Services info
        services_info = ctk.CTkLabel(
            content_frame,
            text="Standard translation services pre-configured:\n• Translation\n• TM - Fuzzy Match (Low, Medium, High)\n• TM - Exact Match",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            justify="left"
        )
        services_info.pack(anchor="w", pady=(0, 20))
        
        # Export format section
        format_label = ctk.CTkLabel(
            content_frame,
            text="Supported Formats:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        format_label.pack(anchor="w", pady=(0, 10))
        
        formats_info = ctk.CTkLabel(
            content_frame,
            text="Rate cards are saved in JSON format for easy integration with other systems.",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        formats_info.pack(anchor="w", pady=(0, 20))
    
    def on_create_tiered(self):
        """Open tiered rate card creation window."""
        try:
            TieredRateCardWindow(self.root)
            self.status_label.configure(text="✓ Tiered Rate Card Editor opened")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Tiered Rate Card Editor:\n{str(e)}")
            self.status_label.configure(text="✗ Error opening Tiered Rate Card Editor")
    
    def on_open_rate_card(self):
        """Open selected rate card."""
        try:
            LoadRateCardWindow(self.root)
            self.status_label.configure(text="✓ Load Rate Card window opened")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Load Rate Card:\n{str(e)}")
            self.status_label.configure(text="✗ Error opening Load Rate Card")
    
    def on_load_master_rate_card(self):
        """Open the master rate card picker directly."""
        try:
            win = LoadRateCardWindow(self.root)
            # Automatically trigger the master card picker after window opens
            win.window.after(200, win.on_load_master_rate_card)
            self.status_label.configure(text="✓ Master Rate Card loader opened")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Master Rate Card loader:\n{str(e)}")
            self.status_label.configure(text="✗ Error opening Master Rate Card loader")


    def on_browse_rate_cards(self):
        """Browse for rate card files."""
        file_path = filedialog.askopenfilename(
            title="Select Rate Card File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self.status_label.configure(
                        text=f"✓ Loaded: {Path(file_path).name}"
                    )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
                self.status_label.configure(text="✗ Error loading file")


def setup_rate_cards_tab(parent_frame, root_window) -> RateCardBuilderTab:
    """
    Factory function to create and return a RateCardBuilderTab instance.
    
    Args:
        parent_frame: Parent CTk frame to embed in
        root_window: Root window reference for popup windows
        
    Returns:
        RateCardBuilderTab instance
    """
    return RateCardBuilderTab(parent_frame, root_window)
