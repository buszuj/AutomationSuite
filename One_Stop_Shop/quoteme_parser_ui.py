"""
QuoteMe Email Parser UI Tab for One Stop Shop

Provides a UI tab for parsing QuoteMe emails, displaying extracted data,
and allowing users to edit and apply the parsed values to the main form.
"""

import customtkinter as ctk
from tkinter import messagebox, scrolledtext
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add Core to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Core.quoteme_email_parser import (
    QuoteeMEmailParser, ParseResult, LanguagePairData, 
    get_parse_cache, WordCountData
)


def create_labeled_frame(parent, text: str, **kwargs):
    """
    Create a labeled frame compatible with customtkinter
    Works around CTkLabelFrame not being available in all versions
    """
    # Filter out unsupported parameters for older customtkinter versions
    supported_kwargs = {}
    unsupported_params = {'fg_color', 'text_color', 'border_color', 'border_width'}
    
    for key, value in kwargs.items():
        if key not in unsupported_params:
            supported_kwargs[key] = value
    
    # Create outer frame
    frame = ctk.CTkFrame(parent, **supported_kwargs)
    
    # Add a title label at the top
    label = ctk.CTkLabel(frame, text=text, font=ctk.CTkFont(size=12, weight="bold"))
    label.pack(anchor="w", padx=5, pady=(5, 10))
    
    # Create an inner frame for content
    inner_frame = ctk.CTkFrame(frame)
    inner_frame.pack(fill="both", expand=True, padx=5, pady=5)
    
    return frame, inner_frame


class QuoteParserTab:
    """UI Tab for QuoteMe email parsing"""
    
    def __init__(self, parent_frame, on_apply_callback=None, on_parse_complete_callback=None):
        """
        Initialize the parser tab
        
        Args:
            parent_frame: Parent CTk frame
            on_apply_callback: Callback function when user applies parsed data
                             Should accept (lp_code: str, lp_data: LanguagePairData)
            on_parse_complete_callback: Callback function when parsing completes
                                       Should accept (parse_result: ParseResult)
        """
        self.parent = parent_frame
        self.on_apply_callback = on_apply_callback
        self.on_parse_complete_callback = on_parse_complete_callback
        self.parser = QuoteeMEmailParser()
        self.parse_cache = get_parse_cache()
        self.current_parse_result: Optional[ParseResult] = None
        self.selected_lp_index = 0
        self._lp_label_map: Dict[str, str] = {}   # display label → full lp_code
        self._entry_fields: Dict = {}

        # Create UI
        self._create_widgets()
    
    def _create_widgets(self):
        """Create all UI widgets"""
        # Main container - two rows: input (fixed) + results (expanding)
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # ── Step 1: Email Input (fixed height, buttons on the right) ─────────
        input_section = ctk.CTkFrame(main_frame, fg_color="#2b2b2b", corner_radius=8)
        input_section.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 3))

        ctk.CTkLabel(input_section, text="Step 1: Paste Email Body",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=8, pady=(6, 2))

        # Row: text area + action buttons side by side
        input_row = ctk.CTkFrame(input_section, fg_color="transparent")
        input_row.pack(fill="x", padx=5, pady=(0, 6))

        self.email_text = scrolledtext.ScrolledText(input_row, height=7, wrap="word",
                                                     bg="#1e1e1e", fg="white",
                                                     insertbackground="white",
                                                     font=("Arial", 11))
        self.email_text.pack(side="left", fill="both", expand=True, padx=(0, 6))

        # Buttons stacked vertically on the right
        btn_col = ctk.CTkFrame(input_row, fg_color="transparent")
        btn_col.pack(side="right", fill="y")

        ctk.CTkButton(btn_col, text="Parse Email", command=self._on_parse_click,
                      width=120, height=35, font=ctk.CTkFont(size=11, weight="bold"),
                      fg_color="#2ecc71", hover_color="#27ae60").pack(pady=(0, 6))

        ctk.CTkButton(btn_col, text="Clear", command=self._on_clear_click,
                      width=120, height=35,
                      fg_color="#e74c3c", hover_color="#c0392b").pack()

        # ── Step 2: Results (expands to fill remaining space) ─────────────────
        results_section = ctk.CTkFrame(main_frame, fg_color="#2b2b2b", corner_radius=8)
        results_section.grid(row=1, column=0, sticky="nsew", padx=5, pady=(3, 5))
        results_section.grid_rowconfigure(0, weight=0, minsize=48)  # LP picker strip – fixed 48 px
        results_section.grid_rowconfigure(1, weight=1)   # panels – expand
        results_section.grid_rowconfigure(2, weight=0)   # action buttons – fixed
        results_section.grid_columnconfigure(0, weight=1)  # Parsed Data – equal half
        results_section.grid_columnconfigure(1, weight=1)  # Review & Edit – equal half

        # ── Compact LP-picker strip (row 0, spans both columns) ───────────────
        # Fixed height – must NOT grow when LP data is loaded
        lp_strip = ctk.CTkFrame(results_section, fg_color="transparent", height=40)
        lp_strip.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(4, 4))
        lp_strip.pack_propagate(False)   # children cannot resize this frame

        ctk.CTkLabel(lp_strip, text="Step 2 – Language Pair:",
                     font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")

        self.lp_var = ctk.StringVar(value="—")
        self.lp_dropdown = ctk.CTkOptionMenu(
            lp_strip, variable=self.lp_var,
            values=["—"], command=self._on_lp_select,
            width=220, height=28, font=ctk.CTkFont(size=11)
        )
        self.lp_dropdown.pack(side="left", padx=(8, 0))

        self.status_label = ctk.CTkLabel(lp_strip, text="",
                                         text_color="gray", font=ctk.CTkFont(size=10))
        self.status_label.pack(side="left", padx=(12, 0))

        # ── Results display frames (row 1, two-column split) ──────────────────────
        left_panel = ctk.CTkFrame(results_section, fg_color="transparent")
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(8, 3), pady=(0, 4))
        left_panel.grid_rowconfigure(1, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left_panel, text="Parsed Data",
                     font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, sticky="w", padx=5)

        self.data_display_frame = ctk.CTkScrollableFrame(
            left_panel, fg_color="#1e1e1e", corner_radius=4
        )
        self.data_display_frame.grid(row=1, column=0, sticky="nsew")

        # ── Right panel: Review / edit entry boxes ───────────────────────────────
        right_panel = ctk.CTkFrame(results_section, fg_color="transparent")
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(3, 8), pady=(0, 4))
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right_panel, text="Review & Edit",
                     font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, sticky="w", padx=5)

        self.review_frame = ctk.CTkScrollableFrame(
            right_panel, fg_color="#1e1e1e", corner_radius=4
        )
        self.review_frame.grid(row=1, column=0, sticky="nsew")

        # ── Action buttons (row 2, spans both columns) ────────────────────────
        action_frame = ctk.CTkFrame(results_section, fg_color="transparent")
        action_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))

        ctk.CTkButton(action_frame, text="Apply Selected LP", command=self._on_apply_click,
                      width=150, height=30).pack(side="left", padx=(0, 6))
        ctk.CTkButton(action_frame, text="Apply All LPs", command=self._on_apply_all_click,
                      width=130, height=30).pack(side="left", padx=(0, 6))
        ctk.CTkButton(action_frame, text="Export to JSON", command=self._on_export_click,
                      width=130, height=30).pack(side="left")
    
    def _on_parse_click(self):
        """Handle parse button click"""
        email_text = self.email_text.get("1.0", "end-1c").strip()
        
        if not email_text:
            messagebox.showwarning("Empty Input", "Please paste an email body first")
            return
        
        # Parse the email
        self.current_parse_result = self.parser.parse(email_text)
        
        if not self.current_parse_result.success:
            error_msg = "\n".join(self.current_parse_result.errors)
            messagebox.showerror("Parse Error", f"Failed to parse email:\n{error_msg}")
            self.status_label.configure(text=f"Parse failed: {error_msg[:100]}", text_color="red")
            return
        
        # Store in cache
        if self.current_parse_result.language_pairs:
            self.parse_cache.store(self.current_parse_result.language_pairs)
        
        # Update UI
        self._update_results_display()
        
        # Notify Job Data tab of parsed language pairs
        if self.on_parse_complete_callback:
            try:
                self.on_parse_complete_callback(self.current_parse_result)
            except Exception as e:
                print(f"Error calling parse complete callback: {e}")
        
        # Show warnings if any
        if self.current_parse_result.warnings:
            warning_msg = "\n".join(self.current_parse_result.warnings)
            messagebox.showwarning("Parse Warnings", f"Some issues occurred:\n{warning_msg}")
        
        status = f"Successfully parsed {len(self.current_parse_result.language_pairs)} language pair(s)"
        self.status_label.configure(text=status, text_color="green")
    
    def _on_clear_click(self):
        """Clear the email input"""
        self.email_text.delete("1.0", "end")
        self.current_parse_result = None
        self._clear_results_display()
        self.status_label.configure(text="Cleared", text_color="gray")
    
    @staticmethod
    def _extract_lp_name(lp_code: str) -> str:
        """Return only the 'Source > Target' part of an lp_code string."""
        first_line = lp_code.split('\n')[0].strip()
        m = re.match(r'^(.+?(?:>|\u2192|->).+?)(?:\s*[:\(\[]|\s{2,}|$)', first_line)
        if m:
            return m.group(1).strip()
        # Fallback: first 80 chars
        return first_line[:80]

    def _on_lp_select(self, label: str):
        """Handle language pair selection (label is the short display name)."""
        if label == "\u2014" or not self.current_parse_result or not self.current_parse_result.language_pairs:
            return
        full_code = self._lp_label_map.get(label, label)
        lp_data = self.parse_cache.get(full_code)
        if lp_data:
            self._display_lp_details(lp_data)
    
    def _update_results_display(self):
        """Update the results display with parsed data"""
        if not self.current_parse_result or not self.current_parse_result.language_pairs:
            self._clear_results_display()
            return

        # Build short display labels and mapping → full lp_code
        self._lp_label_map = {}
        labels = []
        for lp in self.current_parse_result.language_pairs:
            label = self._extract_lp_name(lp.lp_code)
            # Ensure uniqueness
            base, n = label, 1
            while label in self._lp_label_map:
                n += 1
                label = f"{base} ({n})"
            self._lp_label_map[label] = lp.lp_code
            labels.append(label)

        self.lp_dropdown.configure(values=labels)
        if labels:
            self.lp_var.set(labels[0])
            self._display_lp_details(self.current_parse_result.language_pairs[0])
    
    def _clear_results_display(self):
        """Clear the results display"""
        for widget in self.data_display_frame.winfo_children():
            widget.destroy()
        for widget in self.review_frame.winfo_children():
            widget.destroy()
        self.lp_dropdown.configure(values=["—"])
        self.lp_var.set("—")
        self._entry_fields = {}
    
    def _display_lp_details(self, lp_data: LanguagePairData):
        """Display detailed information for a language pair"""
        # Clear both panels
        for widget in self.data_display_frame.winfo_children():
            widget.destroy()
        for widget in self.review_frame.winfo_children():
            widget.destroy()
        self._entry_fields = {}

        _WC_FIELDS = [
            ("Context",       "context"),
            ("100%",          "fuzzy_100"),
            ("Repetitions",   "repetitions"),
            ("Fuzzy Matches", "fuzzy_matches"),
            ("New Words",     "new_words"),
        ]

        # ── LEFT panel: read-only parsed data ──────────────────────────────────
        ctk.CTkLabel(
            self.data_display_frame,
            text=lp_data.lp_code,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=6, pady=(8, 4))

        # Cumulative (read-only)
        ctk.CTkLabel(
            self.data_display_frame, text="Cumulative (all files)",
            font=ctk.CTkFont(size=10, weight="bold"), text_color="#aaaaaa"
        ).pack(anchor="w", padx=6, pady=(6, 2))

        for lbl, fld in _WC_FIELDS:
            val = getattr(lp_data.cumulative_wc, fld, 0)
            r = ctk.CTkFrame(self.data_display_frame, fg_color="transparent")
            r.pack(fill="x", padx=6, pady=1)
            ctk.CTkLabel(r, text=f"{lbl}:", width=110, anchor="w",
                         font=ctk.CTkFont(size=10)).pack(side="left")
            ctk.CTkLabel(r, text=str(val), anchor="w",
                         font=ctk.CTkFont(size=10)).pack(side="left")

        ctk.CTkLabel(
            self.data_display_frame,
            text=f"Total: {lp_data.cumulative_wc.total}",
            font=ctk.CTkFont(size=10, weight="bold")
        ).pack(anchor="e", padx=10, pady=(2, 6))

        if lp_data.file_breakdowns:
            ctk.CTkLabel(
                self.data_display_frame, text="Per-File Breakdown",
                font=ctk.CTkFont(size=10, weight="bold"), text_color="#aaaaaa"
            ).pack(anchor="w", padx=6, pady=(6, 2))
            for file_bd in lp_data.file_breakdowns:
                ctk.CTkLabel(
                    self.data_display_frame,
                    text=file_bd.file_name,
                    font=ctk.CTkFont(size=9, weight="bold"), text_color="#88aaff"
                ).pack(anchor="w", padx=10, pady=(6, 1))
                for lbl, fld in _WC_FIELDS:
                    val = getattr(file_bd.wc_data, fld, 0)
                    r = ctk.CTkFrame(self.data_display_frame, fg_color="transparent")
                    r.pack(fill="x", padx=14, pady=1)
                    ctk.CTkLabel(r, text=f"{lbl}:", width=100, anchor="w",
                                 font=ctk.CTkFont(size=9)).pack(side="left")
                    ctk.CTkLabel(r, text=str(val), anchor="w",
                                 font=ctk.CTkFont(size=9)).pack(side="left")
                ctk.CTkLabel(
                    self.data_display_frame,
                    text=f"Subtotal: {file_bd.wc_data.total}",
                    font=ctk.CTkFont(size=9)
                ).pack(anchor="e", padx=14, pady=(1, 4))

        if lp_data.tm_config:
            ctk.CTkLabel(
                self.data_display_frame, text="TM Configuration",
                font=ctk.CTkFont(size=10, weight="bold"), text_color="#aaaaaa"
            ).pack(anchor="w", padx=6, pady=(8, 2))
            ctk.CTkLabel(
                self.data_display_frame,
                text=lp_data.tm_config, wraplength=260, justify="left",
                font=ctk.CTkFont(size=9)
            ).pack(anchor="w", padx=10, pady=(0, 8))

        # ── RIGHT panel: editable entry rows ─────────────────────────────────
        cum_frame, cum_inner = create_labeled_frame(
            self.review_frame, text="Cumulative Data (All Files)", fg_color="transparent"
        )
        cum_frame.pack(fill="x", padx=5, pady=5)

        for label, field in _WC_FIELDS:
            self._create_wc_entry_row(cum_inner, f"{label}:", lp_data.cumulative_wc, field)

        ctk.CTkLabel(
            cum_inner,
            text=f"Total: {lp_data.cumulative_wc.total}",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(anchor="e", padx=10, pady=5)

        if lp_data.file_breakdowns:
            for file_bd in lp_data.file_breakdowns:
                file_frame, file_inner = create_labeled_frame(
                    self.review_frame, text=file_bd.file_name, fg_color="transparent"
                )
                file_frame.pack(fill="x", padx=5, pady=5)

                for label, field in _WC_FIELDS:
                    self._create_wc_entry_row(
                        file_inner, f"{label}:", file_bd.wc_data, field, file_bd.file_name
                    )

                ctk.CTkLabel(
                    file_inner,
                    text=f"Subtotal: {file_bd.wc_data.total}",
                    font=ctk.CTkFont(size=10)
                ).pack(anchor="e", padx=20, pady=5)

        # Store reference to LP data for later use
        self.current_displayed_lp = lp_data
    
    def _create_wc_entry_row(self, parent, label_text: str, wc_data: WordCountData, 
                            field_name: str, file_name: str = ""):
        """
        Create an editable row for word count field
        
        Args:
            parent: Parent frame
            label_text: Label for the field
            wc_data: WordCountData object
            field_name: Attribute name (context, fuzzy_100, etc)
            file_name: Optional file name for identification
        """
        row_frame = ctk.CTkFrame(parent)
        row_frame.pack(fill="x", padx=10, pady=3)
        
        label = ctk.CTkLabel(row_frame, text=label_text, width=100, anchor="w")
        label.pack(side="left", padx=5)
        
        current_value = getattr(wc_data, field_name, 0)
        entry_var = ctk.StringVar(value=str(current_value))
        
        # Check if value is 0 (potentially missing data) and set background color
        is_missing = current_value == 0
        bg_color = "#ffcccc" if is_missing else "white"  # Red highlight for missing
        
        entry = ctk.CTkEntry(row_frame, textvariable=entry_var, width=100)
        entry.pack(side="left", padx=5)
        
        # For missing values, change appearance
        if is_missing:
            entry.configure(border_color="red", border_width=2)
        
        # Store reference for later retrieval
        if not hasattr(self, '_entry_fields'):
            self._entry_fields = {}
        
        key = f"{file_name}_{field_name}" if file_name else field_name
        self._entry_fields[key] = (entry_var, wc_data, field_name)
    
    def _on_apply_click(self):
        """Apply selected LP data to main form"""
        if not hasattr(self, 'current_displayed_lp'):
            messagebox.showwarning("No Data", "Please select a language pair first")
            return
        
        lp_data = self.current_displayed_lp
        
        if self.on_apply_callback:
            self.on_apply_callback(lp_data.lp_code, lp_data)
            messagebox.showinfo("Success", f"Applied data for {lp_data.lp_code}")
        else:
            messagebox.showinfo("Applied", f"Data for {lp_data.lp_code} would be applied")
    
    def _on_apply_all_click(self):
        """Apply all parsed LP data"""
        if not self.current_parse_result or not self.current_parse_result.language_pairs:
            messagebox.showwarning("No Data", "Please parse an email first")
            return
        
        count = 0
        for lp_data in self.current_parse_result.language_pairs:
            if self.on_apply_callback:
                self.on_apply_callback(lp_data.lp_code, lp_data)
                count += 1
        
        messagebox.showinfo("Success", f"Applied data for {count} language pair(s)")
    
    def _on_export_click(self):
        """Export parsed data to JSON"""
        if not self.current_parse_result or not self.current_parse_result.language_pairs:
            messagebox.showwarning("No Data", "Please parse an email first")
            return
        
        try:
            json_str = self.parse_cache.to_json()
            
            # Save to file
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                with open(file_path, 'w') as f:
                    f.write(json_str)
                messagebox.showinfo("Success", f"Exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")


def create_parser_tab(parent_frame, on_apply_callback=None, on_parse_complete_callback=None) -> QuoteParserTab:
    """Factory function to create a parser tab"""
    return QuoteParserTab(parent_frame, on_apply_callback, on_parse_complete_callback)
