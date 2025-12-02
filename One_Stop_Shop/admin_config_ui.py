"""
One Stop Shop - Admin Configuration Window
Handles service mapping configuration UI.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Dict, List, Callable, Optional
import sys
from pathlib import Path

# Add Core to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from Core.service_mapping_manager import ServiceMappingManager


# Define available labels
QUOTEME_LABELS = ["Context:", "100%:", "Repetitions:", "Fuzzy Matches:", "New Words:", "Total Words:"]
QTC_LABELS = ["TC WC for TRANSLATION:", "TC WC for REVISION:"]


admin_win_instance = None  # Module-level variable


def open_admin_config(
    root: tk.Tk,
    font: ctk.CTkFont,
    services: List[str] = None,
    services_uofm: Dict[str, str] = None,
    on_save: Optional[Callable] = None,
    ratesheet_name: str = None,
    account_key: str = None
):
    """
    Open the admin configuration window.
    
    Args:
        root: Parent window
        font: Font to use for UI elements
        services: List of available services
        services_uofm: Dictionary mapping services to their Unit of Measure
        on_save: Callback function to execute after saving
        ratesheet_name: Display name for the ratesheet
        account_key: Account identifier for storing mappings
    """
    global admin_win_instance
    
    if admin_win_instance is not None and admin_win_instance.winfo_exists():
        admin_win_instance.lift()
        admin_win_instance.focus_force()
        return

    small_font = ctk.CTkFont(family="Arial", size=10)
    title = f"{ratesheet_name} Admin Configuration" if ratesheet_name else "Admin Configuration"
    
    admin_win_instance = tk.Toplevel(root)
    admin_win_instance.title(title)
    admin_win_instance.geometry("900x600")
    ctk.CTkLabel(admin_win_instance, text=title, font=small_font).pack(pady=10)

    # Load current mapping
    mapping_manager = ServiceMappingManager()
    mapping = mapping_manager.get_mapping_for_account(account_key)

    # Filter services by type
    word_services = [svc for svc in services if services_uofm.get(svc) == "Word"] if services and services_uofm else []
    hour_services = [svc for svc in services if services_uofm.get(svc) == "Hour"] if services and services_uofm else []

    # --- PER WORD SERVICES TABLE ---
    Per_word_services_table_frame = tk.Frame(admin_win_instance, bg="#f0f0f0")
    Per_word_services_table_frame.pack(fill="both", expand=True, padx=10, pady=10)

    borderwidth = 1
    cell_width = 16

    def cell(row, col, text="", colspan=1, rowspan=1, bold=False, bg="#f0f0f0"):
        lbl = tk.Label(
            Per_word_services_table_frame, text=text, borderwidth=borderwidth, relief="solid",
            width=cell_width, font=small_font, bg=bg, anchor="center"
        )
        lbl.grid(row=row, column=col, columnspan=colspan, rowspan=rowspan, sticky="nsew")
        return lbl

    # Headers
    cell(0, 0, "Per Word Services", rowspan=2, bold=True, bg="#e0e0e0")
    cell(0, 1, "QuoteMe", colspan=len(QUOTEME_LABELS), bold=True, bg="#e0e0e0")
    cell(0, 1+len(QUOTEME_LABELS), "QTC", colspan=len(QTC_LABELS), bold=True, bg="#e0e0e0")
    
    for i, label in enumerate(QUOTEME_LABELS):
        cell(1, 1+i, label, bg="#f8f8f8")
    for i, label in enumerate(QTC_LABELS):
        cell(1, 1+len(QUOTEME_LABELS)+i, label, bg="#f8f8f8")

    # Checkboxes for word services
    checkbox_vars = {}
    for row_idx, svc in enumerate(word_services, start=2):
        cell(row_idx, 0, svc, bg="#f8f8f8")
        checkbox_vars[svc] = {"QuoteMe": [], "QTC": []}
        
        # QuoteMe checkboxes
        for col_idx, label in enumerate(QUOTEME_LABELS):
            var = tk.BooleanVar()
            if svc in mapping and "QuoteMe" in mapping[svc] and label in mapping[svc]["QuoteMe"]:
                var.set(True)
            frame = tk.Frame(Per_word_services_table_frame, borderwidth=borderwidth, relief="solid", bg="#ffffff")
            frame.grid(row=row_idx, column=1+col_idx, sticky="nsew")
            cb = tk.Checkbutton(frame, variable=var, bg="#ffffff")
            cb.pack(expand=True)
            checkbox_vars[svc]["QuoteMe"].append((label, var))
        
        # QTC checkboxes
        for col_idx, label in enumerate(QTC_LABELS):
            var = tk.BooleanVar()
            if svc in mapping and "QTC" in mapping[svc] and label in mapping[svc]["QTC"]:
                var.set(True)
            frame = tk.Frame(Per_word_services_table_frame, borderwidth=borderwidth, relief="solid", bg="#ffffff")
            frame.grid(row=row_idx, column=1+len(QUOTEME_LABELS)+col_idx, sticky="nsew")
            cb = tk.Checkbutton(frame, variable=var, bg="#ffffff")
            cb.pack(expand=True)
            checkbox_vars[svc]["QTC"].append((label, var))

    for col in range(1 + len(QUOTEME_LABELS) + len(QTC_LABELS)):
        Per_word_services_table_frame.grid_columnconfigure(col, weight=1)

    # --- PER HOUR SERVICES TABLE ---
    Per_hour_services_table_frame = tk.Frame(admin_win_instance, bg="#f0f0f0")
    Per_hour_services_table_frame.pack(fill="both", expand=True, padx=10, pady=10)

    hour_cell_width = 16

    def hour_cell(row, col, text="", colspan=1, rowspan=1, bold=False, bg="#f0f0f0"):
        lbl = tk.Label(
            Per_hour_services_table_frame, text=text, borderwidth=borderwidth, relief="solid",
            width=hour_cell_width, font=small_font, bg=bg, anchor="center"
        )
        lbl.grid(row=row, column=col, columnspan=colspan, rowspan=rowspan, sticky="nsew")
        return lbl

    # Header rows
    hour_cell(0, 0, "Per Hour Services", rowspan=2, bold=True, bg="#e0e0e0")
    hour_cell(0, 1, "QuoteMe Hourly Divider", colspan=2, bold=True, bg="#e0e0e0")
    hour_cell(0, 3, "QTC Hourly Divider", colspan=2, bold=True, bg="#e0e0e0")
    hour_cell(0, 5, "WC for Revision", rowspan=2, bold=True, bg="#e0e0e0")
    hour_cell(0, 6, "WC for Translation", rowspan=2, bold=True, bg="#e0e0e0")
    hour_cell(1, 1, "Live file", bg="#f8f8f8")
    hour_cell(1, 2, "Dead file", bg="#f8f8f8")
    hour_cell(1, 3, "Live file", bg="#f8f8f8")
    hour_cell(1, 4, "Dead file", bg="#f8f8f8")

    # Editable entries and tickboxes
    hourly_divider_vars = {}
    qtc_divider_vars = {}
    wc_for_revision_vars = {}
    wc_for_translation_vars = {}

    for row_idx, svc in enumerate(hour_services, start=2):
        hour_cell(row_idx, 0, svc, bg="#f8f8f8")
        
        # QuoteMe Hourly Divider
        hourly_divider_vars[svc] = {}
        for col, label in enumerate(["live_divider", "dead_divider"]):
            var = tk.StringVar()
            entry = tk.Entry(Per_hour_services_table_frame, textvariable=var, width=8, font=small_font, justify="center")
            entry.grid(row=row_idx, column=1+col, sticky="nsew")
            hourly_divider_vars[svc][label] = var
        
        # QTC Hourly Divider
        qtc_divider_vars[svc] = {}
        for col, label in enumerate(["live_divider", "dead_divider"]):
            var = tk.StringVar()
            entry = tk.Entry(Per_hour_services_table_frame, textvariable=var, width=8, font=small_font, justify="center")
            entry.grid(row=row_idx, column=3+col, sticky="nsew")
            qtc_divider_vars[svc][label] = var
        
        # WC for Revision
        wc_for_revision_vars[svc] = tk.BooleanVar()
        cb_rev = tk.Checkbutton(Per_hour_services_table_frame, variable=wc_for_revision_vars[svc], font=small_font, bg="#ffffff")
        cb_rev.grid(row=row_idx, column=5, sticky="nsew")
        
        # WC for Translation
        wc_for_translation_vars[svc] = tk.BooleanVar()
        cb_trans = tk.Checkbutton(Per_hour_services_table_frame, variable=wc_for_translation_vars[svc], font=small_font, bg="#ffffff")
        cb_trans.grid(row=row_idx, column=6, sticky="nsew")

    for col in range(7):
        Per_hour_services_table_frame.grid_columnconfigure(col, weight=1)

    # --- GLOBAL SETTINGS ---
    min_hourly_rate_var = tk.StringVar()
    increment_rate_var = tk.StringVar()
    default_pm_percent_var = tk.StringVar()
    default_pm_percent_var.set(mapping.get("default_pm_percent", "10"))

    min_rate_frame = tk.Frame(admin_win_instance, bg="#f0f0f0")
    min_rate_frame.pack(fill="x", padx=10, pady=2)
    tk.Label(min_rate_frame, text="min hourly rate", font=small_font, width=20, anchor="w").grid(row=0, column=0, sticky="w")
    tk.Entry(min_rate_frame, textvariable=min_hourly_rate_var, width=8, font=small_font, justify="center").grid(row=0, column=1)
    tk.Label(min_rate_frame, text="increment rate", font=small_font, width=20, anchor="w").grid(row=1, column=0, sticky="w")
    tk.Entry(min_rate_frame, textvariable=increment_rate_var, width=8, font=small_font, justify="center").grid(row=1, column=1)
    tk.Label(min_rate_frame, text="Default Project Management %", font=small_font, width=28, anchor="w").grid(row=2, column=0, sticky="w")
    tk.Entry(min_rate_frame, textvariable=default_pm_percent_var, width=8, font=small_font, justify="center").grid(row=2, column=1)

    # --- LOAD VALUES FROM MAPPING ---
    for svc in hour_services:
        if svc in mapping and "QuoteMe" in mapping[svc]:
            hourly_divider_vars[svc]["live_divider"].set(mapping[svc]["QuoteMe"].get("live_divider", ""))
            hourly_divider_vars[svc]["dead_divider"].set(mapping[svc]["QuoteMe"].get("dead_divider", ""))
        if svc in mapping and "QTC" in mapping[svc]:
            qtc_divider_vars[svc]["live_divider"].set(mapping[svc]["QTC"].get("live_divider", ""))
            qtc_divider_vars[svc]["dead_divider"].set(mapping[svc]["QTC"].get("dead_divider", ""))
            wc_for_revision_vars[svc].set(mapping[svc]["QTC"].get("use_wc_for_revision", False))
            wc_for_translation_vars[svc].set(mapping[svc]["QTC"].get("use_wc_for_translation", False))

    min_hourly_rate_var.set(mapping.get("min_hourly_rate", ""))
    increment_rate_var.set(mapping.get("increment_rate", ""))

    # --- SAVE & CLOSE BUTTON ---
    def save_and_close():
        new_mapping = {}
        
        # Save per-word services
        for svc, groups in checkbox_vars.items():
            new_mapping[svc] = {
                "QuoteMe": [label for label, var in groups["QuoteMe"] if var.get()],
                "QTC": [label for label, var in groups["QTC"] if var.get()]
            }
        
        # Save per-hour services
        for svc in hour_services:
            new_mapping[svc] = new_mapping.get(svc, {})
            new_mapping[svc]["QuoteMe"] = {
                "live_divider": hourly_divider_vars[svc]["live_divider"].get(),
                "dead_divider": hourly_divider_vars[svc]["dead_divider"].get()
            }
            new_mapping[svc]["QTC"] = {
                "live_divider": qtc_divider_vars[svc]["live_divider"].get(),
                "dead_divider": qtc_divider_vars[svc]["dead_divider"].get(),
                "use_wc_for_revision": wc_for_revision_vars[svc].get(),
                "use_wc_for_translation": wc_for_translation_vars[svc].get()
            }
        
        # Save global settings
        new_mapping["min_hourly_rate"] = min_hourly_rate_var.get()
        new_mapping["increment_rate"] = increment_rate_var.get()
        pm_val = default_pm_percent_var.get().strip()
        if not pm_val:
            pm_val = "10"
        new_mapping["default_pm_percent"] = pm_val

        # Save to file
        mapping_manager.save_mapping_for_account(account_key, new_mapping)
        
        if on_save:
            on_save()
        
        if admin_win_instance is not None:
            admin_win_instance.destroy()

    save_btn = ctk.CTkButton(admin_win_instance, text="Save & Close", command=save_and_close)
    save_btn.pack(pady=10)

    # Ensure the window can be closed properly
    def on_close():
        global admin_win_instance
        if admin_win_instance is not None:
            admin_win_instance.destroy()
            admin_win_instance = None
    
    admin_win_instance.protocol("WM_DELETE_WINDOW", on_close)
