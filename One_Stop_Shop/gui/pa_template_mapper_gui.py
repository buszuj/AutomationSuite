"""
PA Template Mapper GUI
Visual interface for configuring PA template mappings per account

Features:
- Complete template view with all fields
- Inline configuration with cog buttons
- Mapping type selection (direct, static, calculated, concatenate)
- Template preview
- Save/load per account
"""

import customtkinter as ctk
from tkinter import messagebox, Toplevel
import pandas as pd
from typing import Optional, Dict, List, Any
import sys
from pathlib import Path

# Add Core to path
core_path = Path(__file__).parent.parent.parent / "Core"
sys.path.insert(0, str(core_path))

from pa_template_manager import PATemplateManager


# Default PA Template Fields (from CEVA Integration_Template)
DEFAULT_TEMPLATE_FIELDS = [
    "GP Company",
    "Requested By Client #",
    "Billing Client #",
    "End Client/Sponsor",
    "Job Name",
    "Client Deadline",
    "Prod. Deadline hours before Client Deadline",
    "AM",
    "Client Dept",
    "Subject Matter",
    "Qualification",
    "primary tech product",
    "Client project purpose",
    "Location of source files",
    "Delivery Method",
    "Additional Delivery Info",
    "Project Instructions",
    "DTP Quote #",
    "DTP Platform",
    "DTP Software",
    "Billing Division",
    "Client PO",
    "Client Specific Project ID",
    "Case name",
    "Matter #",
    "Life Science Protocol",
    "Client Invoice description",
    "Main AE",
    "AE 2",
    "AE 3",
    "Main AE %",
    "AE 2 %",
    "AE 3 %",
    "Job referred by",
    "Revenue Credit Plan",
    "Primary Prod. Dept",
    "Primary PM",
    "Primary QM",
    "Primary Percent",
    "Additional 1 Prod. Dept.",
    "Additional 1 PM",
    "Additional 1 QM",
    "Additional 1 Percent",
    "Additional 1 Amount",
    "Additional 2 Prod. Dept.",
    "Additional 2 PM",
    "Additional 2 QM",
    "Additional 2 Percent",
    "Additional 2 Amount",
    "Estimated Internal Costs",
    "Estimated External Costs",
    "Estimated Revenue",
    "Rebate Percentage",
    "Rebate Amount",
    "Discount Percentage",
    "SourceFile1 File Type",
    "SourceFile1 Qty",
    "SourceFile1 SalesWordCount",
    "SourceFile1 ProdWordCount",
    "SourceFile1 SourceLanguage",
    "SourceFile1 TargetLanguages",
    "SourceFile2 File Type",
    "SourceFile2 Qty",
    "SourceFile2 SalesWordCount",
    "SourceFile2 ProdWordCount",
    "SourceFile2 SourceLanguage",
    "SourceFile2 TargetLanguages",
    "SourceFile3 File Type",
    "SourceFile3 Qty",
    "SourceFile3 SalesWordCount",
    "SourceFile3 ProdWordCount",
    "SourceFile3 SourceLanguage",
    "SourceFile3 TargetLanguages",
    "DeliverableFile1 File Type",
    "DeliverableFile1 Qty",
    "DeliverableFile1 WordCount",
    "DeliverableFile2 File Type",
    "DeliverableFile2 Qty",
    "DeliverableFile2 WordCount",
    "DeliverableFile3 File Type",
    "DeliverableFile3 Qty",
    "DeliverableFile3 WordCount",
    "LP1 Source",
    "LP1 Target",
    "LP1 Service Group",
    "LP1 Service",
    "LP1 Quantity",
    "LP1 Rate",
    "LP1 Unit of Measure",
]


class PATemplateMapperGUI:
    """Visual template mapper for PA import configuration"""
    
    def __init__(self, parent, account_name: str, dataframe: Optional[pd.DataFrame] = None):
        """
        Initialize PA Template Mapper
        
        Args:
            parent: Parent tkinter window
            account_name: Account to configure template for
            dataframe: Optional DataFrame to show available columns
        """
        self.parent = parent
        self.account_name = account_name
        self.dataframe = dataframe
        self.template_manager = PATemplateManager()
        
        # Current mappings configuration dict (key -> mapping config)
        self.mapping_config: Dict[str, Dict[str, Any]] = {}
        
        # Mapping widgets for reference
        self.mapping_widgets = {}
        
        # Create modal dialog
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(f"PA Template Mapper - {account_name}")
        self.dialog.geometry("1200x800")
        
        # Make modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center on screen
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (800 // 2)
        self.dialog.geometry(f"1200x800+{x}+{y}")
        
        # Load existing template if exists
        self.load_existing_template()
        
        self.setup_ui()
    
    def load_existing_template(self):
        """Load existing template for account if exists"""
        template = self.template_manager.get_template(self.account_name)
        if template:
            existing_mappings = template.get("mappings", [])
            self.template_name = template.get("template_name", "Integration Template")
            self.description = template.get("description", "")
            self.key_column = template.get("key_column_name", "Field Name")
            self.data_column = template.get("data_column_name", "Value")
            
            # Create mapping dict for easy lookup
            self.mapping_config = {}
            for mapping in existing_mappings:
                key = mapping.get("key", "")
                if key:
                    self.mapping_config[key] = mapping
        else:
            self.template_name = "Integration Template"
            self.description = ""
            self.key_column = "Field Name"
            self.data_column = "Value"
            self.mapping_config = {}
        
        # Initialize all default fields with empty config if not exist
        for field in DEFAULT_TEMPLATE_FIELDS:
            if field not in self.mapping_config:
                self.mapping_config[field] = {
                    "key": field,
                    "source_column": "",
                    "mapping_type": "direct",
                    "static_value": None,
                    "formula": None,
                    "format": None
                }
    
    def setup_ui(self):
        """Setup the template mapper UI"""
        # Header
        header_frame = ctk.CTkFrame(self.dialog, fg_color="#1f538d", corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        
        ctk.CTkLabel(
            header_frame,
            text=f"🗂️ PA Template Mapper - {self.account_name}",
            font=("Arial", 20, "bold"),
            text_color="white"
        ).pack(pady=15)
        
        ctk.CTkLabel(
            header_frame,
            text="Configure field mappings for PA import worksheets",
            font=("Arial", 12),
            text_color="#e0e0e0"
        ).pack(pady=(0, 15))
        
        # Main content area
        content_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Left panel - Template Settings
        left_panel = ctk.CTkFrame(content_frame, width=350, fg_color="#2b2b2b", corner_radius=8)
        left_panel.pack(side="left", fill="both", padx=(0, 10))
        left_panel.pack_propagate(False)
        
        self.setup_template_settings(left_panel)
        
        # Right panel - Mappings
        right_panel = ctk.CTkFrame(content_frame, fg_color="#2b2b2b", corner_radius=8)
        right_panel.pack(side="right", fill="both", expand=True)
        
        self.setup_mappings_panel(right_panel)
        
        # Bottom buttons
        button_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            command=self.cancel,
            width=150,
            height=40,
            font=("Arial", 13, "bold"),
            fg_color="#e74c3c",
            hover_color="#c0392b"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="👁️ Preview",
            command=self.preview_template,
            width=150,
            height=40,
            font=("Arial", 13, "bold"),
            fg_color="#3498db",
            hover_color="#2980b9"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="💾 Save Changes",
            command=self.save_template,
            width=200,
            height=40,
            font=("Arial", 13, "bold"),
            fg_color="#27ae60",
            hover_color="#229954"
        ).pack(side="right", padx=5)
    
    def setup_template_settings(self, parent):
        """Setup template settings panel"""
        ctk.CTkLabel(
            parent,
            text="📋 Template Settings",
            font=("Arial", 16, "bold"),
            text_color="#3498db"
        ).pack(pady=(15, 10), padx=15, anchor="w")
        
        # Template name
        ctk.CTkLabel(parent, text="Template Name:", font=("Arial", 11), anchor="w").pack(padx=15, pady=(10, 2), fill="x")
        self.name_entry = ctk.CTkEntry(parent, height=35, font=("Arial", 11))
        self.name_entry.insert(0, self.template_name)
        self.name_entry.pack(padx=15, pady=(0, 10), fill="x")
        
        # Description
        ctk.CTkLabel(parent, text="Description:", font=("Arial", 11), anchor="w").pack(padx=15, pady=(5, 2), fill="x")
        self.desc_entry = ctk.CTkTextbox(parent, height=80, font=("Arial", 11))
        self.desc_entry.insert("1.0", self.description)
        self.desc_entry.pack(padx=15, pady=(0, 10), fill="x")
        
        # Column names
        ctk.CTkLabel(parent, text="Key Column Name:", font=("Arial", 11), anchor="w").pack(padx=15, pady=(10, 2), fill="x")
        self.key_col_entry = ctk.CTkEntry(parent, height=35, font=("Arial", 11))
        self.key_col_entry.insert(0, self.key_column)
        self.key_col_entry.pack(padx=15, pady=(0, 10), fill="x")
        
        ctk.CTkLabel(parent, text="Data Column Name:", font=("Arial", 11), anchor="w").pack(padx=15, pady=(5, 2), fill="x")
        self.data_col_entry = ctk.CTkEntry(parent, height=35, font=("Arial", 11))
        self.data_col_entry.insert(0, self.data_column)
        self.data_col_entry.pack(padx=15, pady=(0, 10), fill="x")
        
        # Available columns info
        if self.dataframe is not None:
            ctk.CTkLabel(
                parent,
                text=f"📊 Available Columns: {len(self.dataframe.columns)}",
                font=("Arial", 11),
                text_color="#95a5a6"
            ).pack(padx=15, pady=(20, 5), anchor="w")
            
            # Show first few columns
            cols_preview = ", ".join(list(self.dataframe.columns[:5]))
            if len(self.dataframe.columns) > 5:
                cols_preview += "..."
            
            ctk.CTkLabel(
                parent,
                text=cols_preview,
                font=("Arial", 9),
                text_color="#7f8c8d",
                wraplength=300,
                justify="left"
            ).pack(padx=15, pady=(0, 10), anchor="w")
    
    def setup_mappings_panel(self, parent):
        """Setup mappings panel with all template fields"""
        # Header
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            header_frame,
            text="🔗 Template Field Mappings",
            font=("Arial", 16, "bold"),
            text_color="#3498db"
        ).pack(side="left")
        
        ctk.CTkLabel(
            header_frame,
            text=f"{len(DEFAULT_TEMPLATE_FIELDS)} fields",
            font=("Arial", 11),
            text_color="#95a5a6"
        ).pack(side="right")
        
        # Scrollable mappings area
        self.mappings_scroll = ctk.CTkScrollableFrame(parent, fg_color="#1e1e1e")
        self.mappings_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Render all fields
        self.refresh_mappings_display()
    
    def refresh_mappings_display(self):
        """Refresh the mappings display with all fields"""
        # Clear existing widgets
        for widget in self.mappings_scroll.winfo_children():
            widget.destroy()
        self.mapping_widgets.clear()
        
        # Create mapping row for each default field
        for idx, field_name in enumerate(DEFAULT_TEMPLATE_FIELDS):
            mapping = self.mapping_config.get(field_name, {
                "key": field_name,
                "source_column": "",
                "mapping_type": "direct",
                "static_value": None,
                "formula": None,
                "format": None
            })
            self.create_mapping_row(idx, field_name, mapping)
    
    def create_mapping_row(self, idx: int, field_name: str, mapping: Dict[str, Any]):
        """Create a single compact mapping row with inline config"""
        # Row container
        row_frame = ctk.CTkFrame(
            self.mappings_scroll,
            fg_color="#252525" if idx % 2 == 0 else "#2b2b2b",
            corner_radius=4
        )
        row_frame.pack(fill="x", pady=1, padx=5)
        
        # Content frame
        content_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=10, pady=6)
        
        # Field name (PA key) - fixed width
        key_label = ctk.CTkLabel(
            content_frame,
            text=field_name,
            font=("Arial", 10),
            text_color="#3498db",
            width=250,
            anchor="w"
        )
        key_label.pack(side="left", padx=(0, 10))
        
        # Value entry (source column or static value) - expandable
        value_entry = ctk.CTkEntry(
            content_frame,
            height=28,
            font=("Arial", 10),
            placeholder_text="Source column or static value..."
        )
        
        # Set current value based on mapping type
        current_value = ""
        if mapping.get("mapping_type") == "static" and mapping.get("static_value"):
            current_value = mapping.get("static_value", "")
        elif mapping.get("source_column"):
            current_value = mapping.get("source_column", "")
        
        if current_value:
            value_entry.insert(0, current_value)
        
        value_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Config button (cog icon)
        config_btn = ctk.CTkButton(
            content_frame,
            text="⚙️",
            command=lambda fn=field_name: self.show_field_config(fn),
            width=30,
            height=28,
            font=("Arial", 12),
            fg_color="#34495e",
            hover_color="#2c3e50"
        )
        config_btn.pack(side="right")
        
        # Store widget references
        self.mapping_widgets[field_name] = {
            "value_entry": value_entry,
            "mapping": mapping
        }
    
    def show_field_config(self, field_name: str):
        """Show configuration dialog for a specific field"""
        mapping = self.mapping_config.get(field_name, {})
        
        # Create config dialog
        config_dialog = ctk.CTkToplevel(self.dialog)
        config_dialog.title(f"Configure: {field_name}")
        config_dialog.geometry("600x500")
        config_dialog.transient(self.dialog)
        config_dialog.grab_set()
        
        # Center dialog
        config_dialog.update_idletasks()
        x = (config_dialog.winfo_screenwidth() // 2) - (300)
        y = (config_dialog.winfo_screenheight() // 2) - (250)
        config_dialog.geometry(f"600x500+{x}+{y}")
        
        # Header
        header = ctk.CTkFrame(config_dialog, fg_color="#34495e")
        header.pack(fill="x")
        
        ctk.CTkLabel(
            header,
            text=f"⚙️ Configure Field Mapping",
            font=("Arial", 16, "bold"),
            text_color="white"
        ).pack(pady=15)
        
        ctk.CTkLabel(
            header,
            text=field_name,
            font=("Arial", 12),
            text_color="#ecf0f1"
        ).pack(pady=(0, 15))
        
        # Content
        content = ctk.CTkFrame(config_dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Mapping Type
        ctk.CTkLabel(content, text="Mapping Type:", font=("Arial", 12, "bold"), anchor="w").pack(fill="x", pady=(10, 5))
        type_var = ctk.StringVar(value=mapping.get("mapping_type", "direct"))
        type_combo = ctk.CTkComboBox(
            content,
            values=["direct", "static", "calculated", "concatenate"],
            variable=type_var,
            height=35,
            font=("Arial", 11),
            state="readonly"
        )
        type_combo.pack(fill="x", pady=(0, 15))
        
        # Source Column
        ctk.CTkLabel(content, text="Source Column:", font=("Arial", 12, "bold"), anchor="w").pack(fill="x", pady=(10, 5))
        if self.dataframe is not None:
            source_var = ctk.StringVar(value=mapping.get("source_column", ""))
            source_combo = ctk.CTkComboBox(
                content,
                values=[""] + list(self.dataframe.columns),
                variable=source_var,
                height=35,
                font=("Arial", 11)
            )
            source_combo.pack(fill="x", pady=(0, 15))
        else:
            source_entry = ctk.CTkEntry(content, height=35, font=("Arial", 11))
            source_entry.insert(0, mapping.get("source_column", ""))
            source_entry.pack(fill="x", pady=(0, 15))
        
        # Static Value
        ctk.CTkLabel(content, text="Static Value:", font=("Arial", 12, "bold"), anchor="w").pack(fill="x", pady=(10, 5))
        static_entry = ctk.CTkEntry(content, height=35, font=("Arial", 11))
        static_entry.insert(0, mapping.get("static_value", "") or "")
        static_entry.pack(fill="x", pady=(0, 15))
        
        # Format
        ctk.CTkLabel(content, text="Format:", font=("Arial", 12, "bold"), anchor="w").pack(fill="x", pady=(10, 5))
        format_var = ctk.StringVar(value=mapping.get("format", "") or "")
        format_combo = ctk.CTkComboBox(
            content,
            values=["", "date", "number", "text"],
            variable=format_var,
            height=35,
            font=("Arial", 11),
            state="readonly"
        )
        format_combo.pack(fill="x", pady=(0, 15))
        
        # Buttons
        button_frame = ctk.CTkFrame(config_dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        def save_config():
            # Update mapping config
            self.mapping_config[field_name] = {
                "key": field_name,
                "mapping_type": type_var.get(),
                "source_column": source_var.get() if self.dataframe is not None else source_entry.get().strip(),
                "static_value": static_entry.get().strip() or None,
                "formula": None,
                "format": format_var.get() or None
            }
            
            # Update main display value entry
            widget_data = self.mapping_widgets.get(field_name, {})
            value_entry = widget_data.get("value_entry")
            if value_entry:
                value_entry.delete(0, "end")
                if type_var.get() == "static":
                    value_entry.insert(0, static_entry.get().strip())
                else:
                    source_val = source_var.get() if self.dataframe is not None else source_entry.get().strip()
                    value_entry.insert(0, source_val)
            
            config_dialog.destroy()
        
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=config_dialog.destroy,
            width=120,
            height=35,
            font=("Arial", 12),
            fg_color="#95a5a6",
            hover_color="#7f8c8d"
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Save",
            command=save_config,
            width=120,
            height=35,
            font=("Arial", 12, "bold"),
            fg_color="#27ae60",
            hover_color="#229954"
        ).pack(side="right", padx=5)
    
    def add_mapping_row(self):
        """Add a new empty mapping"""
        new_mapping = {
            "key": "",
            "source_column": "",
            "mapping_type": "direct",
            "static_value": None,
            "formula": None,
            "format": None
        }
        self.mappings.append(new_mapping)
        self.refresh_mappings_display()
    
    def delete_mapping(self, idx: int):
        """Delete a mapping"""
        if messagebox.askyesno("Confirm Delete", f"Delete mapping #{idx + 1}?"):
            del self.mappings[idx]
            self.refresh_mappings_display()
    
    def collect_mappings(self) -> List[Dict[str, Any]]:
        """Collect current mappings from all fields"""
        collected_mappings = []
        
        for field_name, widget_data in self.mapping_widgets.items():
            # Get the mapping config
            mapping = self.mapping_config.get(field_name, {})
            
            # Get the current value from entry
            value_entry = widget_data.get("value_entry")
            if value_entry:
                current_value = value_entry.get().strip()
                
                # Update source_column or static_value based on mapping type
                if mapping.get("mapping_type") == "static":
                    mapping["static_value"] = current_value or None
                else:
                    mapping["source_column"] = current_value
            
            # Only include if there's some configuration
            if mapping.get("source_column") or mapping.get("static_value"):
                collected_mappings.append(mapping)
        
        return collected_mappings
    
    def preview_template(self):
        """Preview how the template will look"""
        mappings = self.collect_mappings()
        
        if not mappings:
            messagebox.showwarning("No Mappings", "Please add at least one mapping to preview")
            return
        
        # Create preview window
        preview = ctk.CTkToplevel(self.dialog)
        preview.title("Template Preview")
        preview.geometry("700x600")
        preview.transient(self.dialog)
        
        # Header
        ctk.CTkLabel(
            preview,
            text="📄 Template Preview",
            font=("Arial", 18, "bold")
        ).pack(pady=15)
        
        # Scrollable preview area
        preview_scroll = ctk.CTkScrollableFrame(preview, fg_color="#1e1e1e")
        preview_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Show key column name and data column name
        key_col = self.key_col_entry.get().strip() or "Field Name"
        data_col = self.data_col_entry.get().strip() or "Value"
        
        # Header row
        header_frame = ctk.CTkFrame(preview_scroll, fg_color="#1f538d")
        header_frame.pack(fill="x", pady=(5, 10), padx=5)
        
        ctk.CTkLabel(
            header_frame,
            text=key_col,
            font=("Arial", 12, "bold"),
            text_color="white",
            width=250,
            anchor="w"
        ).pack(side="left", padx=15, pady=10)
        
        ctk.CTkLabel(
            header_frame,
            text=data_col,
            font=("Arial", 12, "bold"),
            text_color="white",
            anchor="w"
        ).pack(side="left", padx=15, pady=10, fill="x", expand=True)
        
        # Data rows
        for idx, mapping in enumerate(mappings):
            row_frame = ctk.CTkFrame(preview_scroll, fg_color="#252525" if idx % 2 == 0 else "#2b2b2b")
            row_frame.pack(fill="x", pady=2, padx=5)
            
            # Key
            ctk.CTkLabel(
                row_frame,
                text=mapping["key"],
                font=("Arial", 11),
                text_color="#3498db",
                width=250,
                anchor="w"
            ).pack(side="left", padx=15, pady=8)
            
            # Value (show mapping info)
            value_text = ""
            if mapping["mapping_type"] == "direct":
                value_text = f"← {mapping['source_column']}"
            elif mapping["mapping_type"] == "static":
                value_text = f"'{mapping['static_value']}'"
            elif mapping["mapping_type"] == "calculated":
                value_text = "[Calculated]"
            elif mapping["mapping_type"] == "concatenate":
                value_text = "[Concatenated]"
            
            if mapping.get("format"):
                value_text += f" ({mapping['format']})"
            
            ctk.CTkLabel(
                row_frame,
                text=value_text,
                font=("Arial", 10),
                text_color="#95a5a6",
                anchor="w"
            ).pack(side="left", padx=15, pady=8, fill="x", expand=True)
        
        # Close button
        ctk.CTkButton(
            preview,
            text="Close",
            command=preview.destroy,
            width=150,
            height=35,
            font=("Arial", 12, "bold")
        ).pack(pady=(0, 20))
    
    def save_template(self):
        """Save the template"""
        # Collect data
        template_name = self.name_entry.get().strip()
        description = self.desc_entry.get("1.0", "end-1c").strip()
        key_column = self.key_col_entry.get().strip() or "Field Name"
        data_column = self.data_col_entry.get().strip() or "Value"
        mappings = self.collect_mappings()
        
        if not template_name:
            messagebox.showwarning("Missing Name", "Please enter a template name")
            return
        
        if not mappings:
            messagebox.showwarning("No Mappings", "Please add at least one field mapping")
            return
        
        # Save via template manager
        success = self.template_manager.create_template(
            account_name=self.account_name,
            template_name=template_name,
            description=description,
            key_column_name=key_column,
            data_column_name=data_column,
            mappings=mappings
        )
        
        if success:
            messagebox.showinfo(
                "Template Saved",
                f"PA template '{template_name}' saved successfully for account '{self.account_name}'"
            )
            self.dialog.destroy()
        else:
            messagebox.showerror("Save Failed", "Failed to save template")
    
    def cancel(self):
        """Cancel and close"""
        if messagebox.askyesno("Confirm Cancel", "Discard changes and close?"):
            self.dialog.destroy()


def launch_template_mapper(parent, account_name: str, dataframe: Optional[pd.DataFrame] = None):
    """
    Launch the PA Template Mapper GUI
    
    Args:
        parent: Parent tkinter window
        account_name: Account to configure
        dataframe: Optional DataFrame with available columns
    """
    mapper = PATemplateMapperGUI(parent, account_name, dataframe)
    parent.wait_window(mapper.dialog)
