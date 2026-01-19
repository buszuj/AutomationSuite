"""
QuoteMe Email Parser UI Tab for One Stop Shop

Provides a UI tab for parsing QuoteMe emails, displaying extracted data,
and allowing users to edit and apply the parsed values to the main form.
"""

import customtkinter as ctk
from tkinter import messagebox, scrolledtext
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add Core to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Core.quoteme_email_parser import (
    QuoteeMEmailParser, ParseResult, LanguagePairData, 
    get_parse_cache, WordCountData
)


class QuoteParserTab:
    """UI Tab for QuoteMe email parsing"""
    
    def __init__(self, parent_frame, on_apply_callback=None):
        """
        Initialize the parser tab
        
        Args:
            parent_frame: Parent CTk frame
            on_apply_callback: Callback function when user applies parsed data
                             Should accept (lp_code: str, lp_data: LanguagePairData)
        """
        self.parent = parent_frame
        self.on_apply_callback = on_apply_callback
        self.parser = QuoteeMEmailParser()
        self.parse_cache = get_parse_cache()
        self.current_parse_result: Optional[ParseResult] = None
        self.selected_lp_index = 0
        
        # Create UI
        self._create_widgets()
    
    def _create_widgets(self):
        """Create all UI widgets"""
        # Main container
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # --- Email Input Section ---
        input_frame = ctk.CTkLabelFrame(main_frame, text="Step 1: Paste Email Body", fg_color="transparent")
        input_frame.pack(fill="both", padx=5, pady=5)
        
        ctk.CTkLabel(input_frame, text="Paste the complete email body from QuoteMe:", 
                     font=ctk.CTkFont(size=11)).pack(anchor="w", padx=5, pady=(5, 2))
        
        self.email_text = scrolledtext.ScrolledText(input_frame, height=8, width=80, wrap="word")
        self.email_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Button frame
        button_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=5, pady=5)
        
        parse_btn = ctk.CTkButton(button_frame, text="Parse Email", command=self._on_parse_click)
        parse_btn.pack(side="left", padx=2)
        
        clear_btn = ctk.CTkButton(button_frame, text="Clear", command=self._on_clear_click)
        clear_btn.pack(side="left", padx=2)
        
        # --- Results Section ---
        results_frame = ctk.CTkLabelFrame(main_frame, text="Step 2: Review & Edit Parsed Data", fg_color="transparent")
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Status message
        self.status_label = ctk.CTkLabel(results_frame, text="No data parsed yet", 
                                        text_color="gray", font=ctk.CTkFont(size=10))
        self.status_label.pack(anchor="w", padx=5, pady=(5, 0))
        
        # Language pair selector
        lp_selector_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
        lp_selector_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(lp_selector_frame, text="Language Pair:", font=ctk.CTkFont(size=10)).pack(side="left", padx=2)
        
        self.lp_var = ctk.StringVar(value="")
        self.lp_dropdown = ctk.CTkOptionMenu(lp_selector_frame, variable=self.lp_var, 
                                            values=[], command=self._on_lp_select)
        self.lp_dropdown.pack(side="left", padx=2, fill="x", expand=True)
        
        # Data display area (scrollable notebook-like layout)
        display_frame = ctk.CTkFrame(results_frame)
        display_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create scrollable area for the data display
        canvas = ctk.CTkCanvas(display_frame, fg_color="transparent", bg_color="transparent", highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(display_frame, orientation="vertical", command=canvas.yview)
        scrollable_frame = ctk.CTkFrame(canvas, fg_color="transparent")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.data_display_frame = scrollable_frame
        
        # --- Action Buttons ---
        action_frame = ctk.CTkFrame(results_frame, fg_color="transparent")
        action_frame.pack(fill="x", padx=5, pady=5)
        
        apply_btn = ctk.CTkButton(action_frame, text="Apply Selected LP", command=self._on_apply_click, fg_color="green")
        apply_btn.pack(side="left", padx=2)
        
        apply_all_btn = ctk.CTkButton(action_frame, text="Apply All LPs", command=self._on_apply_all_click)
        apply_all_btn.pack(side="left", padx=2)
        
        export_btn = ctk.CTkButton(action_frame, text="Export to JSON", command=self._on_export_click)
        export_btn.pack(side="left", padx=2)
    
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
    
    def _on_lp_select(self, lp_code: str):
        """Handle language pair selection"""
        if not self.current_parse_result or not self.current_parse_result.language_pairs:
            return
        
        # Find matching LP in cache
        lp_data = self.parse_cache.get(lp_code)
        if lp_data:
            self._display_lp_details(lp_data)
    
    def _update_results_display(self):
        """Update the results display with parsed data"""
        if not self.current_parse_result or not self.current_parse_result.language_pairs:
            self._clear_results_display()
            return
        
        # Update LP dropdown
        lp_codes = [lp.lp_code for lp in self.current_parse_result.language_pairs]
        self.lp_dropdown.configure(values=lp_codes)
        
        if lp_codes:
            self.lp_var.set(lp_codes[0])
            self._display_lp_details(self.current_parse_result.language_pairs[0])
    
    def _clear_results_display(self):
        """Clear the results display"""
        for widget in self.data_display_frame.winfo_children():
            widget.destroy()
        self.lp_dropdown.configure(values=[])
        self.lp_var.set("")
    
    def _display_lp_details(self, lp_data: LanguagePairData):
        """Display detailed information for a language pair"""
        # Clear previous display
        for widget in self.data_display_frame.winfo_children():
            widget.destroy()
        
        # Title
        title = ctk.CTkLabel(
            self.data_display_frame,
            text=f"Language Pair: {lp_data.lp_code}",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        title.pack(anchor="w", padx=5, pady=(10, 5))
        
        # Cumulative Data Section
        cum_frame = ctk.CTkLabelFrame(self.data_display_frame, text="Cumulative Data (All Files)", fg_color="transparent")
        cum_frame.pack(fill="x", padx=5, pady=5)
        
        self._create_wc_entry_row(cum_frame, "Context:", lp_data.cumulative_wc, "context")
        self._create_wc_entry_row(cum_frame, "100%:", lp_data.cumulative_wc, "fuzzy_100")
        self._create_wc_entry_row(cum_frame, "Repetitions:", lp_data.cumulative_wc, "repetitions")
        self._create_wc_entry_row(cum_frame, "Fuzzy Matches:", lp_data.cumulative_wc, "fuzzy_matches")
        self._create_wc_entry_row(cum_frame, "New Words:", lp_data.cumulative_wc, "new_words")
        
        total_label = ctk.CTkLabel(
            cum_frame,
            text=f"Total: {lp_data.cumulative_wc.total}",
            font=ctk.CTkFont(size=11, weight="bold")
        )
        total_label.pack(anchor="e", padx=10, pady=5)
        
        # Per-File Data Section
        if lp_data.file_breakdowns:
            file_frame = ctk.CTkLabelFrame(self.data_display_frame, text="Per-File Breakdown", fg_color="transparent")
            file_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            for file_bd in lp_data.file_breakdowns:
                file_label = ctk.CTkLabel(
                    file_frame,
                    text=f"File: {file_bd.file_name}",
                    font=ctk.CTkFont(size=10, weight="bold")
                )
                file_label.pack(anchor="w", padx=10, pady=(10, 5))
                
                self._create_wc_entry_row(file_frame, "Context:", file_bd.wc_data, "context", file_bd.file_name)
                self._create_wc_entry_row(file_frame, "100%:", file_bd.wc_data, "fuzzy_100", file_bd.file_name)
                self._create_wc_entry_row(file_frame, "Repetitions:", file_bd.wc_data, "repetitions", file_bd.file_name)
                self._create_wc_entry_row(file_frame, "Fuzzy Matches:", file_bd.wc_data, "fuzzy_matches", file_bd.file_name)
                self._create_wc_entry_row(file_frame, "New Words:", file_bd.wc_data, "new_words", file_bd.file_name)
                
                file_total = ctk.CTkLabel(
                    file_frame,
                    text=f"Subtotal: {file_bd.wc_data.total}",
                    font=ctk.CTkFont(size=10)
                )
                file_total.pack(anchor="e", padx=20, pady=5)
        
        # TM Configuration
        if lp_data.tm_config:
            tm_frame = ctk.CTkLabelFrame(self.data_display_frame, text="TM Configuration", fg_color="transparent")
            tm_frame.pack(fill="x", padx=5, pady=5)
            
            tm_label = ctk.CTkLabel(tm_frame, text=lp_data.tm_config, wraplength=400, justify="left")
            tm_label.pack(anchor="w", padx=10, pady=5)
        
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
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
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


def create_parser_tab(parent_frame, on_apply_callback=None) -> QuoteParserTab:
    """Factory function to create a parser tab"""
    return QuoteParserTab(parent_frame, on_apply_callback)
