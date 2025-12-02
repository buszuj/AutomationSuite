import customtkinter as ctk
import pandas as pd
import os
import json
import math
from tkinter import filedialog, messagebox
from tkinter import Listbox
from ttkthemes import ThemedTk
from tkinter import StringVar
from tkinter.ttk import Combobox
import time
from threading import Timer
from tkinter import IntVar
import sys
from pathlib import Path

# Add Core to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import Core modules
from Core.workflow_manager import WorkflowManager
from Core.language_pair_manager import LanguagePairManager
from Core.service_mapping_manager import ServiceMappingManager
from Core.rate_calculations import (
    get_service_type, calculate_hourly_quantity,
    get_word_rate, get_hourly_rate, apply_minimum_fee_logic,
    calculate_percentage_service_rate, sanitize_csv_value
)

# Import admin config UI
from admin_config_ui import open_admin_config


def get_excel_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "One_BP_IQ fixed.01.xlsx")
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "One_BP_IQ fixed.01.xlsx")

current_directory = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))


def get_max_service_count_across_ratesheets():
    """Scan all 'S ' worksheets and return the max number of services."""
    try:
        excel_file = pd.ExcelFile(get_excel_path())
        max_count = 0
        for ws in excel_file.sheet_names:
            if ws.startswith("S "):
                df_services = pd.read_excel(get_excel_path(), sheet_name="Services per account")
                account_name = ws.replace('S ', '')
                if account_name in df_services.columns:
                    count = df_services[df_services[account_name].notna()][account_name].count()
                    if count > max_count:
                        max_count = count
        return max_count
    except Exception as e:
        print(f"Error finding max service count: {e}")
        return 20  # fallback default
WorkSheets = []
try:
    excel_file = pd.ExcelFile(get_excel_path())
    WorkSheets = [ws for ws in excel_file.sheet_names if ws.startswith("S ")]
    if not WorkSheets:
        messagebox.showerror("Error", "No worksheets starting with 'S ' found in the Excel file.")
except Exception as e:
    messagebox.showerror("Error", f"An error occurred while reading the Excel file: {str(e)}")
    WorkSheets = ['S IQVIA']


CurrentWS = WorkSheets[0]

# Initialize managers
workflow_manager = WorkflowManager(os.path.join(current_directory, "workflows.json"))
lp_manager = LanguagePairManager()
mapping_manager = ServiceMappingManager(os.path.join(current_directory, "service_label_mapping.json"))

def load_service_label_mapping():
    return mapping_manager.get_mapping_for_account(CurrentWS)

def get_default_pm_percent():
    return mapping_manager.get_default_pm_percent(CurrentWS)

def reload_service_label_mapping():
    global service_label_mapping
    service_label_mapping = load_service_label_mapping()
    get_default_pm_percent()
    update_preview()

service_label_mapping = load_service_label_mapping()

# Global toggle to determine which input is active
use_qtc_input = False
suspend_preview_update = False

# Deprecated - now using lp_manager
LPs = []  # List to store Language Pairs (LPs)



ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("The One-Stop Shop v.1.1")
# Calculate max service count and set window height
ROW_HEIGHT = 18
BASE_HEIGHT = 400  # Adjust as needed for your non-service UI
MAX_SERVICE_COUNT = get_max_service_count_across_ratesheets()
MAIN_WINDOW_HEIGHT = BASE_HEIGHT + (MAX_SERVICE_COUNT * ROW_HEIGHT)
ACTIVE_SERVICES_FRAME_HEIGHT = MAX_SERVICE_COUNT * ROW_HEIGHT
root.geometry(f"1200x{MAIN_WINDOW_HEIGHT}")

worksheet_var = ctk.StringVar(value=WorkSheets[0])


# Add this near other variable declarations at the top
pa_entities = ["TPTNY",	"TPTUK", "TPTZA",	"TPTFR",	"TPTIT",	"ESTDC",	"TPTSK",	"TPTDE",	"TPTNL",	"TPTBR",	"TPBRA",	"TPTTW",	"TPTSG",	"TPTZH",	"TPTHK",	"TPTJP",	"TPTMI",	"TPTAR",	"QGNTO"] # Add your PA entities here
pa_entity_var = StringVar(root)
pa_entity_var.set(pa_entities[0])  # Set default value

# --- Scrollable root window setup ---
import tkinter as tk

canvas = tk.Canvas(root, borderwidth=0, background="#f0f0f0")
vscrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=vscrollbar.set)
canvas.grid(row=0, column=0, sticky="nsew")
vscrollbar.grid(row=0, column=1, sticky="ns")
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

main_content = ctk.CTkFrame(canvas)

def resize_main_content(event):
    canvas.itemconfig(main_content_id, width=event.width)
canvas.bind("<Configure>", resize_main_content)

main_content_id = canvas.create_window((0, 0), window=main_content, anchor="nw", tags="main_content")


def on_frame_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
main_content.bind("<Configure>", on_frame_configure)

def on_canvas_configure(event):
    canvas.itemconfig(main_content_id, width=event.width)
canvas.bind("<Configure>", on_canvas_configure)

# Initialize tkinter variables AFTER root creation
HourlyDivider = IntVar(root, value=1000)
MinFeeRate = IntVar(root, value=150)

FONT = ctk.CTkFont(size=12)
PADY_LABEL = 1
PADY_ITEM = 1
ROW_HEIGHT = 18





def get_service_quantity(service, use_qtc_input=False):
    """Sum all mapped QuoteMe or QTC fields for the given service."""
    mapping = service_label_mapping.get(service, {})
    total = 0
    if use_qtc_input:
        labels = mapping.get("QTC", [])
        for label in labels:
            entry = qtc_entries.get(label)
            if entry:
                try:
                    total += float(entry.get())
                except Exception:
                    pass
    else:
        labels = mapping.get("QuoteMe", [])
        for label in labels:
            entry = quoteMe_entries.get(label)
            if entry:
                try:
                    total += float(entry.get())
                except Exception:
                    pass
    return total


def refresh_service_checkboxes():
    for widget in ServicesFrame.winfo_children():
        if isinstance(widget, ctk.CTkCheckBox):
            widget.destroy()
    checkbox_state.clear()
    for i, service in enumerate(Services, start=1):
        var = ctk.BooleanVar()
        chk = ctk.CTkCheckBox(ServicesFrame, text=service, variable=var, height=ROW_HEIGHT-5)
        chk.grid(row=i, column=0, padx=5, pady=PADY_ITEM, sticky="w")
        checkbox_state[service] = var
        var.trace_add("write", lambda *args: update_preview())
        
    ServicesFrame.configure(height=ACTIVE_SERVICES_FRAME_HEIGHT)
    PreviewFrame.configure(height=ACTIVE_SERVICES_FRAME_HEIGHT)
def on_worksheet_change(*args):
    global CurrentWS, workflows
    CurrentWS = worksheet_var.get()
    workflows = workflow_manager.get_workflows_for_account(CurrentWS)
    if lp_manager.get_count() > 0:
        if not messagebox.askyesno("Change Worksheet", "Changing the worksheet will clear all language pairs. Continue?"):
            worksheet_var.set(CurrentWS)
            return
    populate_services_and_uom()
    refresh_service_checkboxes()
    populate_languages()
    populate_workflows()
    update_preview()

worksheet_var.trace_add("write", on_worksheet_change)

Services = []
Headers = [
    "Mark New Line Item", "Line Item Description", "Source", "Target", "Hide Unit Costs",
    "Hide Details", "Service Group 1", "Service Group 2", "Service Group 3", "Service",
    "UofM", "Quantity", "Rate", "CommentsForInvoice", "Technology Product",
]

def read_ratesheet():
    ratesheet_path = get_excel_path()
    if os.path.exists(ratesheet_path):
        df = pd.read_excel(ratesheet_path)
        return df
    else:
        messagebox.showerror("File Not Found", "Ratesheet file not found.")
        return None

Languages = []
workflow_file = os.path.join(current_directory, "workflows.json")
Services_UofM = {}
ServiceGroup1 = {}
ServiceGroup2 = {}




def populate_services_and_uom():
    global Services, Services_UofM, ServiceGroup1, ServiceGroup2
    try:
        df_services = pd.read_excel(get_excel_path(), sheet_name="Services per account")
        df_uofm = pd.read_excel(get_excel_path(), sheet_name="UofM")
        Services.clear()
        Services_UofM.clear()
        ServiceGroup1.clear()
        ServiceGroup2.clear()
        account_name = CurrentWS.replace('S ', '')
        if account_name in df_services.columns:
            account_services = df_services[df_services[account_name].notna()][account_name].tolist()
            Services.extend(account_services)
            for _, row in df_uofm.iterrows():
                service = str(row.get("Service name", "")).strip()
                if service:
                    uom = str(row.get("UofM", "")).strip()
                    group1 = str(row.get("Service Group 1", "")).strip()
                    group2 = str(row.get("Service Group 2", "")).strip()
                    if uom:
                        Services_UofM[service] = uom
                    if group1:
                        ServiceGroup1[service] = group1
                    if group2:
                        ServiceGroup2[service] = group2
        else:
            messagebox.showerror("Error", f"Account '{account_name}' not found in Services per account sheet")
    except KeyError as e:
        messagebox.showerror("Error", f"Required column not found: {str(e)}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

populate_services_and_uom()

# Use workflow_manager instead of direct file operations
workflows = workflow_manager.get_workflows_for_account(CurrentWS)

checkbox_state = {}

# --- MAIN LAYOUT: 3 COLUMNS ---
main_content.grid_columnconfigure(0, weight=1)
main_content.grid_columnconfigure(1, weight=1)
main_content.grid_columnconfigure(2, weight=1)
main_content.grid_rowconfigure(0, weight=1)

# --- SERVICES FRAME ---
ServicesFrame = ctk.CTkFrame(main_content)
ServicesFrame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
ServicesFrame.grid_propagate(False)
ServicesFrame.configure(height=800)

# Create a header frame for dropdowns
header_frame = ctk.CTkFrame(ServicesFrame)
header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
header_frame.grid_columnconfigure(0, weight=1)
header_frame.grid_columnconfigure(1, weight=1)

# Add PA entity dropdown and Rate Sheet dropdown in the header frame
ctk.CTkLabel(header_frame, text="PA Entity:", font=FONT).grid(row=0, column=0, padx=5, pady=PADY_LABEL, sticky="w")
pa_entity_dropdown = ctk.CTkOptionMenu(header_frame, variable=pa_entity_var, values=pa_entities)
pa_entity_dropdown.grid(row=0, column=1, padx=5, pady=PADY_ITEM, sticky="ew")

# Add Rate Sheet dropdown next to PA Entity
ctk.CTkLabel(header_frame, text="Rate Sheet:", font=FONT).grid(row=1, column=0, padx=5, pady=PADY_LABEL, sticky="w")
worksheet_dropdown = ctk.CTkOptionMenu(header_frame, variable=worksheet_var, values=WorkSheets)
worksheet_dropdown.grid(row=1, column=1, padx=5, pady=PADY_ITEM, sticky="ew")

# Add File Type dropdown (Live/Dead)
file_types = ["Live", "Dead"]
file_type_var = ctk.StringVar(value=file_types[0])
ctk.CTkLabel(header_frame, text="File Type:", font=FONT).grid(row=2, column=0, padx=5, pady=PADY_LABEL, sticky="w")
file_type_dropdown = ctk.CTkOptionMenu(header_frame, variable=file_type_var, values=file_types)
file_type_dropdown.grid(row=2, column=1, padx=5, pady=PADY_ITEM, sticky="ew")

file_type_var.get()  # returns "Live" or "Dead"

# Move Services label down
ctk.CTkLabel(ServicesFrame, text="Services", font=FONT).grid(row=2, column=0, pady=PADY_LABEL, sticky="n")

# Update the service checkboxes positioning
for i, service in enumerate(Services, start=3):  # Start from row 3 instead of 1
    var = ctk.BooleanVar()
    chk = ctk.CTkCheckBox(ServicesFrame, text=service, variable=var, height=ROW_HEIGHT-5)
    chk.grid(row=i, column=0, padx=5, pady=PADY_ITEM, sticky="w")
    checkbox_state[service] = var
    var.trace_add("write", lambda *args: update_preview())

worksheet_var.trace_add("write", on_worksheet_change)

populate_services_and_uom()



# --- CONTAINER FRAME 1 ---
ContainerFrame1 = ctk.CTkFrame(main_content)
ContainerFrame1.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
ContainerFrame1.grid_propagate(False)
ContainerFrame1.configure(
    height=800)
ContainerFrame1.grid_rowconfigure(0, weight=1)
ContainerFrame1.grid_rowconfigure(1, weight=1)
ContainerFrame1.grid_columnconfigure(0, weight=1)

# --- WORKFLOWS FRAME ---
WorkflowsFrame = ctk.CTkFrame(ContainerFrame1)
WorkflowsFrame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
ctk.CTkLabel(WorkflowsFrame, text="Workflows", font=FONT).pack(pady=PADY_LABEL)
WFlistbox = Listbox(WorkflowsFrame, height=8, width=30)
WFlistbox.pack(fill="both", expand=True, padx=5, pady=PADY_ITEM)

# Add this block to define the entry for new workflow names
new_workflow_entry = ctk.CTkEntry(WorkflowsFrame, width=160)
new_workflow_entry.pack(pady=PADY_ITEM)

# Add a button to save the workflow
save_workflow_button = ctk.CTkButton(
    WorkflowsFrame, text="Save/Update Workflow", command=lambda: save_workflow(new_workflow_entry.get()), width=160
)
save_workflow_button.pack(pady=PADY_ITEM)

def on_workflow_select(event):
    global suspend_preview_update
    if not WFlistbox.curselection():
        return
    selected_workflow = WFlistbox.get(WFlistbox.curselection())
    services = workflows.get(selected_workflow, [])
    suspend_preview_update = True
    for var in checkbox_state.values():
        var.set(False)
    for service in services:
        if service in checkbox_state:
            checkbox_state[service].set(True)
    # --- Add this line to auto-fill the workflow name entry ---
    new_workflow_entry.delete(0, "end")
    new_workflow_entry.insert(0, selected_workflow)
    suspend_preview_update = False
    update_preview()

WFlistbox.bind("<<ListboxSelect>>", on_workflow_select)
workflows = load_workflows()


def get_service_quantity(service, use_qtc_input=False):
    """Sum all mapped QuoteMe or QTC fields for the given service."""
    mapping = service_label_mapping.get(service, {})
    total = 0
    if use_qtc_input:
        labels = mapping.get("QTC", [])
        for label in labels:
            entry = qtc_entries.get(label)
            if entry:
                try:
                    total += float(entry.get())
                except Exception:
                    pass
    else:
        labels = mapping.get("QuoteMe", [])
        for label in labels:
            entry = quoteMe_entries.get(label)
            if entry:
                try:
                    total += float(entry.get())
                except Exception:
                    pass
    return total


def calculate_hourly_quantity(
    service, file_type, use_qtc_input, quoteme_wc, qtc_wc_translation, qtc_wc_revision, config
):
    """
    Calculate the quantity for an hourly service based on admin config and user input.

    - service: service name (str)
    - file_type: "Live" or "Dead"
    - use_qtc_input: bool, True if QTC input is used, False for QuoteMe
    - quoteme_wc: int/float, total QuoteMe wordcount
    - qtc_wc_translation: int/float, QTC WC for Translation
    - qtc_wc_revision: int/float, QTC WC for Revision
    - config: loaded mapping (dict)
    """
    min_hourly_rate = float(config.get("min_hourly_rate", 0.5) or 0.5)
    increment_rate = float(config.get("increment_rate", 0.25) or 0.25)
    svc_conf = config.get(service, {})
    if use_qtc_input:
        qtc_cfg = svc_conf.get("QTC", {})
        divider = float(qtc_cfg.get("live_divider" if file_type == "Live" else "dead_divider", 1) or 1)
        # Use the tickboxes to decide which QTC WC to use
        if qtc_cfg.get("use_wc_for_translation"):
            wc = qtc_wc_translation
        elif qtc_cfg.get("use_wc_for_revision"):
            wc = qtc_wc_revision
        else:
            wc = 0
    else:
        quoteme_cfg = svc_conf.get("QuoteMe", {})
        divider = float(quoteme_cfg.get("live_divider" if file_type == "Live" else "dead_divider", 1) or 1)
        wc = quoteme_wc

    if divider == 0:
        return min_hourly_rate
    hours = wc / divider
    hours_ceiled = math.ceil(hours / increment_rate) * increment_rate
    return max(hours_ceiled, min_hourly_rate)

def save_workflow(workflow_name):
    workflow_name = workflow_name.strip()
    if not workflow_name:
        messagebox.showwarning("Invalid Name", "Please enter a valid workflow name.")
        return
    selected_services = [svc for svc, var in checkbox_state.items() if var.get()]
    if not selected_services:
        messagebox.showwarning("No Services", "Please select at least one service.")
        return
    
    selected_indices = WFlistbox.curselection()
def save_workflow(workflow_name):
    workflow_name = workflow_name.strip()
    if not workflow_name:
        messagebox.showwarning("Invalid Name", "Please enter a valid workflow name.")
        return
    selected_services = [svc for svc, var in checkbox_state.items() if var.get()]
    if not selected_services:
        messagebox.showwarning("No Services", "Please select at least one service.")
        return
    
    selected_indices = WFlistbox.curselection()
    global workflows

    if selected_indices:
        selected_index = selected_indices[0]
        selected_wf_name = WFlistbox.get(selected_index)
        if workflow_name != selected_wf_name:
            workflow_manager.delete_workflow(CurrentWS, selected_wf_name)
            WFlistbox.delete(selected_index)
            WFlistbox.insert(selected_index, workflow_name)
        workflow_manager.save_workflow(CurrentWS, workflow_name, selected_services)
        workflows = workflow_manager.get_workflows_for_account(CurrentWS)
        WFlistbox.selection_clear(0, "end")
        WFlistbox.selection_set(selected_index)
        WFlistbox.activate(selected_index)
        new_workflow_entry.delete(0, "end")
        update_preview()
        messagebox.showinfo("Workflow Updated", f"Workflow '{workflow_name}' has been updated.")
    else:
        if workflow_manager.workflow_exists(CurrentWS, workflow_name):
            messagebox.showwarning("Duplicate Workflow", "A workflow with this name already exists.")
            return
        workflow_manager.save_workflow(CurrentWS, workflow_name, selected_services)
        workflows = workflow_manager.get_workflows_for_account(CurrentWS)
        WFlistbox.insert("end", workflow_name)
        new_workflow_entry.delete(0, "end")
        update_preview()

  
def populate_workflows():
    WFlistbox.delete(0, "end")  # Clear existing items
    for workflow_name in workflows.keys():
        WFlistbox.insert("end", workflow_name)

workflows = workflow_manager.get_workflows_for_account(CurrentWS)
populate_workflows()

# --- PREVIEW FRAME ---
PreviewFrame = ctk.CTkFrame(ContainerFrame1)
PreviewFrame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
PreviewFrame.grid_rowconfigure(1, weight=1)
PreviewFrame.grid_columnconfigure(0, weight=1)
ctk.CTkLabel(PreviewFrame, text="Active Services Preview", font=FONT).grid(
    row=0, column=0, columnspan=3, pady=PADY_LABEL, sticky="ew"
)
preview_grid = ctk.CTkFrame(PreviewFrame)
preview_grid.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
preview_grid.grid_columnconfigure(0, weight=1)
preview_grid.grid_columnconfigure(1, weight=1)
preview_grid.grid_columnconfigure(2, weight=1)
# define the height of the preview grid
preview_grid.configure(height=ACTIVE_SERVICES_FRAME_HEIGHT)
preview_quantities = {}
last_preview_services = []

def create_preview_header():
    """Create the header row for the preview grid"""
    headers = ["Service", "Quantity", "UofM"]
    for col, header in enumerate(headers):
        cell = ctk.CTkFrame(preview_grid, fg_color="gray75")
        cell.grid(row=0, column=col, sticky="nsew", padx=1, pady=1)
        ctk.CTkLabel(cell, text=header, font=FONT).pack(padx=5, pady=2)
        preview_grid.grid_columnconfigure(col, weight=1)  # Ensure all columns expand

def get_quoteMe_value(key):
    """Get value from QuoteMe entries"""
    entry = quoteMe_entries.get(key, None)
    if entry:
        try:
            return int(entry.get().strip())
        except ValueError:
            return 0
    return 0

def get_qtc_value(key):
    """Get value from QTC entries"""
    entry = qtc_entries.get(key, None)
    if entry:
        try:
            return int(entry.get().strip())
        except ValueError:
            return 0
    return 0

def update_preview(*args):
    """Update the Active Service Preview (ASP) grid"""
    global suspend_preview_update
    if suspend_preview_update:
        return

    selected_services = [svc for svc, var in checkbox_state.items() if var.get()]

    # Update word counts based on active input source
    if use_qtc_input:
        translation_value = get_qtc_value("TC WC for TRANSLATION:")
        revision_value = get_qtc_value("TC WC for REVISION:")  # Get revision value for QTC
        word_counts = {
            "new_words": translation_value,
            "tm_exact": 0,
            "tm_fuzzy": 0,
            "revision_words": revision_value  # Add revision words to word_counts
        }
    else:
        translation_value = get_quoteMe_value("New Words:")
        word_counts = {
            "new_words": translation_value,
            "tm_exact": get_quoteMe_value("Context:") + get_quoteMe_value("100%:"),
            "tm_fuzzy": get_quoteMe_value("Repetitions:") + get_quoteMe_value("Fuzzy Matches:"),
            "revision_words": 0
        }

    # Clear the preview grid (except the header row)
    for widget in preview_grid.winfo_children():
        if widget.grid_info()["row"] > 0:
            widget.destroy()

    # Populate the preview grid with selected service
    for row, service in enumerate(selected_services, start=1):
        UofM = Services_UofM.get(service, "")
        service_type = get_service_type(service, UofM)

        if service_type == "hType":
            # Hourly service: use the new calculation
            file_type = file_type_var.get()
            quoteme_wc = get_quoteMe_value("Total Words:")
            qtc_wc_translation = get_qtc_value("TC WC for TRANSLATION:")
            qtc_wc_revision = get_qtc_value("TC WC for REVISION:")
            quantity = calculate_hourly_quantity(
                service,
                file_type,
                use_qtc_input,
                quoteme_wc,
                qtc_wc_translation,
                qtc_wc_revision,
                service_label_mapping
            )
        else:
            # Word-based or other: use the old logic
            quantity = get_service_quantity(service, use_qtc_input)

        # Add service name
        ctk.CTkLabel(preview_grid, text=service, font=FONT).grid(
            row=row, column=0, padx=5, pady=PADY_ITEM, sticky="w"
        )

        # Add quantity entry
        quantity_entry = ctk.CTkEntry(preview_grid, width=100)
        quantity_entry.grid(row=row, column=1, padx=5, pady=PADY_ITEM, sticky="ew")
        quantity_entry.insert(0, str(round(quantity, 2)))
        preview_quantities[service] = quantity_entry

        # Add UofM
        ctk.CTkLabel(preview_grid, text=UofM, font=FONT).grid(
            row=row, column=2, padx=5, pady=PADY_ITEM, sticky="w"
        )

# --- Bindings for Workflow and Services ---
# Input for hourly divider
hourly_divider_input = ctk.CTkEntry(
    main_content, textvariable=HourlyDivider, width=160, height=ROW_HEIGHT-5
)
hourly_divider_input.grid(row=2, column=0, padx=10, pady=PADY_ITEM, sticky="w")


# Ensure the input for Hourly divider accepts integers only
def validate_hourly_divider_input(value_if_allowed):
    if value_if_allowed.isdigit() or value_if_allowed == "":
        return True
    return False

vcmd = (root.register(validate_hourly_divider_input), "%P")
hourly_divider_input.configure(validate="key", validatecommand=vcmd)



# --- Dropdown Filtering ---
def perform_filter(typed_text, combobox, values):
    """Filter and suggest closest matches in the dropdown"""
    if typed_text == "":
        combobox["values"] = values  # Reset to full list if no input
    else:
        filtered_values = [value for value in values if typed_text.lower() in value.lower()]
        combobox["values"] = filtered_values  # Update dropdown with filtered values
    combobox.event_generate("<Down>")  # Open the dropdown to show suggestions

# === REPLACE ContainerFrame section with this updated code ===

# Create a container frame for QuoteMe and QTC
ContainerFrame = ctk.CTkFrame(main_content)
ContainerFrame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
ContainerFrame.grid_propagate(False)
ContainerFrame.configure(height=800)

# Add toggle switch at the top
toggle_var = ctk.BooleanVar(value=False)  # False = QuoteMe (default), True = QTC
toggle_button = ctk.CTkSwitch(
    ContainerFrame,
    text="QTC Mode",
    variable=toggle_var,
    command=lambda: switch_input_mode(),
    onvalue=True,
    offvalue=False
)
toggle_button.grid(row=0, column=0, padx=5, pady=5, sticky="e")

# Configure rows in the container frame
ContainerFrame.grid_rowconfigure(0, weight=0)  # Toggle switch
ContainerFrame.grid_rowconfigure(1, weight=1)  # Language Frame
ContainerFrame.grid_rowconfigure(2, weight=2)  # Input Frame (QuoteMe/QTC)
ContainerFrame.grid_rowconfigure(3, weight=1)  # LP List Frame
ContainerFrame.grid_columnconfigure(0, weight=1)

# Initialize frames but only show QuoteMe by default

# --- QuoteMe Frame ---
QuoteMeFrame = ctk.CTkFrame(ContainerFrame)
QuoteMeFrame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
QuoteMeFrame.grid_columnconfigure(0, weight=1)
QuoteMeFrame.grid_columnconfigure(1, weight=1)
# Define QuoteMe input fields
quoteMe = [
    "Context:", "100%:", "Repetitions:", "Fuzzy Matches:", "New Words:", "Total Words:",
]

# Dictionary to store entry widgets for the second column
quoteMe_entries = {}
for i, field in enumerate(quoteMe):
    # Create label
    ctk.CTkLabel(QuoteMeFrame, text=field, font=FONT).grid(
        row=i, column=0, padx=5, pady=PADY_LABEL, sticky="w"
    )
    # Create entry on the right
    entry = ctk.CTkEntry(QuoteMeFrame, width=160, height=ROW_HEIGHT-5)
    entry.grid(row=i, column=1, padx=5, pady=PADY_ITEM, sticky="ew")
    entry.insert(0, "0")
    quoteMe_entries[field] = entry
    
    # Add validation to ensure only numbers are entered
    def validate_number(value_if_allowed):
        if value_if_allowed == "" or value_if_allowed.isdigit():
            return True
        return False
    vcmd = (root.register(validate_number), '%P')
    entry.configure(validate="key", validatecommand=vcmd)
# Function to update Total Words automatically
def update_total_words(*args):
    total = 0
    for key in ["Context:", "100%:", "Repetitions:", "Fuzzy Matches:", "New Words:"]:
        try:
            val = int(quoteMe_entries[key].get())
        except Exception:
            val = 0
        total += val
    total_words_entry = quoteMe_entries["Total Words:"]
    total_words_entry.configure(state="normal")
    total_words_entry.delete(0, "end")
    total_words_entry.insert(0, str(total))
    total_words_entry.configure(state="readonly")

# Bind update_total_words to all QuoteMe entries except "Total Words:"
for key, entry in quoteMe_entries.items():
    if key != "Total Words:":
        entry.bind("<KeyRelease>", update_total_words)

# Call once at startup to initialize
update_total_words()



# --- QTC Frame ---
QtcFrame = ctk.CTkFrame(ContainerFrame)
QtcFrame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
QuoteMeFrame.grid_columnconfigure(0, weight=1)
QuoteMeFrame.grid_columnconfigure(1, weight=1)

# Define QTC input fields
qtc = [
    "TC WC for TRANSLATION:", "TC WC for REVISION:"
]

QuoteMeFrame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
QtcFrame.grid_remove()  # Hide QTC initially

qtc_entries = {}
for i, field in enumerate(qtc):
    # Create label
    ctk.CTkLabel(QtcFrame, text=field, font=FONT).grid(
        row=i, column=0, padx=5, pady=PADY_LABEL, sticky="w"
    )
    # Create entry
    entry = ctk.CTkEntry(QtcFrame, width=160, height=ROW_HEIGHT-5)
    entry.grid(row=i, column=1, padx=5, pady=PADY_ITEM, sticky="ew")
    entry.insert(0, "0")
    qtc_entries[field] = entry
    
    # Add validation
    entry.configure(validate="key", validatecommand=vcmd)


# Update the switch_input_mode function to handle visibility
def switch_input_mode():
    """Switch between QuoteMe and QTC input modes"""
    global use_qtc_input, suspend_preview_update
    
    if toggle_var.get():  # Switching to QTC
        if not use_qtc_input:  # Only if not already in QTC mode
            quoteme_values = sum(get_quoteMe_value(key) for key in [k for k in quoteMe_entries.keys() if k != "Total Words:"])
            if quoteme_values > 0:
                if not messagebox.askyesno("Clear Values", 
                    "Switching to QTC Input will clear all QuoteMe values. Continue?"):
                    toggle_var.set(False)  # Revert switch if user cancels
                    return
                
            suspend_preview_update = True
            # Hide QuoteMe and show QTC
            QuoteMeFrame.grid_remove()
            QtcFrame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
            
            # Clear QuoteMe entries
            for key, entry in quoteMe_entries.items():
                if key != "Total Words:":
                    entry.delete(0, "end")
                    entry.insert(0, "0")
            
            # Enable QTC entries
            for entry in qtc_entries.values():
                entry.configure(state="normal")
            
            use_qtc_input = True
            suspend_preview_update = False
            update_preview()
    else:  # Switching to QuoteMe
        if use_qtc_input:  # Only if not already in QuoteMe mode
            qtc_values = sum(get_qtc_value(key) for key in qtc_entries.keys())
            if qtc_values > 0:
                if not messagebox.askyesno("Clear Values", 
                    "Switching to QuoteMe Input will clear all QTC values. Continue?"):
                    toggle_var.set(True)  # Revert switch if user cancels
                    return
            
            suspend_preview_update = True
            # Hide QTC and show QuoteMe
            QtcFrame.grid_remove()
            QuoteMeFrame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
            
            # Clear QTC entries
            for entry in qtc_entries.values():
                entry.delete(0, "end")
                entry.insert(0, "0")
            
            # Enable QuoteMe entries
            for key, entry in quoteMe_entries.items():
                if key != "Total Words:":
                    entry.configure(state="normal")
            
            use_qtc_input = False
            suspend_preview_update = False
            update_preview()

# --- Language Frame ---
LanguageFrame = ctk.CTkFrame(ContainerFrame)
LanguageFrame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

# --- LP FRAME (for Language Pairs Listbox and Delete Button) ---
LPFrame = ctk.CTkFrame(ContainerFrame)
LPFrame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
LPFrame.grid_columnconfigure(0, weight=1)

# LP Listbox
LPListbox = Listbox(LPFrame, height=6, width=30)
LPListbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=PADY_ITEM)

# Configure LanguageFrame grid
LanguageFrame.grid_columnconfigure(0, weight=1)
LanguageFrame.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)

# Add labels and dropdowns
ctk.CTkLabel(LanguageFrame, text="Source Language:", font=FONT).grid(
    row=0, column=0, padx=5, pady=PADY_LABEL, sticky="w"
)
source_language_dropdown = Combobox(LanguageFrame, values=Languages, width=30)
source_language_dropdown.grid(row=1, column=0, padx=5, pady=PADY_ITEM, sticky="ew")
source_language_dropdown.set("Select Source Language")

ctk.CTkLabel(LanguageFrame, text="Target Language:", font=FONT).grid(
    row=2, column=0, padx=5, pady=PADY_LABEL, sticky="w"
)
target_language_dropdown = Combobox(LanguageFrame, values=Languages, width=30)
target_language_dropdown.grid(row=3, column=0, padx=5, pady=PADY_ITEM, sticky="ew")
target_language_dropdown.set("Select Target Language")

# --- Typeahead/Autocomplete for language dropdowns with debounce ---
typeahead_after_ids = {"source": None, "target": None}

def filter_combobox_debounced(event, combobox, values, key):
    # Cancel previous scheduled call if any
    if typeahead_after_ids[key]:
        combobox.after_cancel(typeahead_after_ids[key])
    # Schedule the actual filter after 150ms
    def do_filter():
        typed = combobox.get()
        if not typed:
            combobox['values'] = values
        else:
            filtered = [v for v in values if typed.lower() in v.lower()]
            combobox['values'] = filtered
        combobox.event_generate('<Down>')
    typeahead_after_ids[key] = combobox.after(150, do_filter)

source_language_dropdown.bind(
    '<KeyRelease>',
    lambda e: filter_combobox_debounced(e, source_language_dropdown, Languages, "source")
)
target_language_dropdown.bind(
    '<KeyRelease>',
    lambda e: filter_combobox_debounced(e, target_language_dropdown, Languages, "target")
)
def refresh_lp_listbox():
    """Refresh the Listbox with numbered LPs without triggering preview updates."""
    global suspend_preview_update
    suspend_preview_update = True  # Temporarily suspend preview updates
    LPListbox.delete(0, "end")  # Clear the Listbox
    for lp_str in lp_manager.get_numbered_list():
        LPListbox.insert("end", lp_str)
    # Also update legacy LPs list for compatibility
    global LPs
    LPs = lp_manager.get_all_language_pairs()
    suspend_preview_update = False  # Resume preview updates

def save_lp():
    """Save the selected language pair (LP) without resetting ASP values."""
    source_language = source_language_dropdown.get().strip()
    target_language = target_language_dropdown.get().strip()

    success, error_msg = lp_manager.add_language_pair(source_language, target_language)
    
    if not success:
        messagebox.showwarning("Invalid Input", error_msg)
        return

    # Refresh the LP list without triggering preview updates
    refresh_lp_listbox()

# Now create the Save LP button
save_lp_button = ctk.CTkButton(
    LanguageFrame, text="Save LP", command=save_lp, width=160
)
save_lp_button.grid(row=4, column=0, pady=PADY_ITEM, sticky="ew")

def clean_all():
    # Clear Language Pairs
    lp_manager.clear_all()
    refresh_lp_listbox()
    # Clear QuoteMe wordcount entries
    for key, entry in quoteMe_entries.items():
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, "0")
    update_total_words()
    # Clear QTC wordcount entries
    for entry in qtc_entries.values():
        entry.delete(0, "end")
        entry.insert(0, "0")
    update_preview()

# Add the button below Save LP in LanguageFrame
clean_all_button = ctk.CTkButton(
    LanguageFrame, text="Clear all INPUT", command=clean_all, width=160
)
clean_all_button.grid(row=5, column=0, pady=PADY_ITEM, sticky="ew")

def delete_lp():
    selected_index = LPListbox.curselection()
    if not selected_index:
        messagebox.showwarning("No Selection", "Please select a language pair to delete.")
        return

    # Remove the selected LP from the manager
    idx = selected_index[0]
    lp_manager.remove_language_pair(idx)

    refresh_lp_listbox()  # This will call update_preview

# Add "Delete LP" button to the LPFrame
delete_lp_button = ctk.CTkButton(
    LPFrame, text="Delete LP", command=delete_lp, width=160
)
delete_lp_button.grid(pady=PADY_ITEM)

# HOURLY FRAME
# Add a new row in the main window for the hourly divider input
hourly_divider_label = ctk.CTkLabel(
    main_content, text="Hourly Divider - words/hour:", font=FONT
)
hourly_divider_label.grid(row=1, column=0, padx=10, pady=PADY_LABEL, sticky="w")

# Input for hourly divider
hourly_divider_input = ctk.CTkEntry(
    main_content, textvariable=HourlyDivider, width=160, height=ROW_HEIGHT-5
)
hourly_divider_input.grid(row=2, column=0, padx=10, pady=PADY_ITEM, sticky="w")

# Ensure the input for Hourly divider accepts integers only
def validate_hourly_divider_input(value_if_allowed):
    if value_if_allowed.isdigit() or value_if_allowed == "":
        return True
    return False

vcmd = (root.register(validate_hourly_divider_input), "%P")
hourly_divider_input.configure(validate="key", validatecommand=vcmd)

# MIN FEE RATE FRAME
# Add a new row in the main window for the min fee rate input
min_fee_label = ctk.CTkLabel(
    main_content, text="Min fee rate:", font=FONT
)
min_fee_label.grid(row=1, column=1, padx=10, pady=PADY_LABEL, sticky="w")

# Var to store min fee rate
MinFeeRate = IntVar(value=150)  # Use IntVar to store the integer value with a default of 0

# Input for Min Fee rate
min_fee_rate = ctk.CTkEntry(
    main_content, textvariable=MinFeeRate, width=160, height=ROW_HEIGHT-5
)
min_fee_rate.grid(row=2, column=1, padx=10, pady=PADY_ITEM, sticky="w")

def get_service_type(service, uom):
    """Determine the service type based on UofM"""
    if uom == "Word":
        return "wcType"
    elif uom == "Hour":
        return "hType"
    else:
        return "PercentageType"

def calculate_quantity(service_type, service, word_counts, hourly_divider):
    """Calculate quantity based on service type"""
    if service_type == "wcType":
        if service == "Translation" or service == "Machine Translation":
            return word_counts["new_words"]
        elif service == "TM - Exact Match":
            return word_counts["tm_exact"]
        elif service == "TM - Fuzzy Match":
            return word_counts["tm_fuzzy"]
        elif service == "Back Translation":
            return sum(word_counts.values())  # Use total word count
        return 0

    elif service_type == "hType":
        # For hourly services, round up to the nearest 0.5 hour
        if service in ["Formatting", "Review", "Proofreading", "Desktop Publishing (DTP)", "Editing", "Reconciliation"]:
            total_wc = sum(word_counts.values())
            if total_wc > 0 and hourly_divider > 0:
                hours = total_wc / hourly_divider
                # Round up to nearest 0.5
                return math.ceil(hours * 2) / 2
        return 1  # Minimum 1 hour

    else:  # PercentageType
        if service == "Project Management":
            return 10  # Default Project Management percentage
        elif service == "Rush Premium":
            return 25  # Default Rush Premium percentage
        return 0

def get_word_rate(df_s_iqvia, source_lang, target_lang, service):
    """Get word-based rate from S IQVIA worksheet"""
    # Map plural service names to singular column names if needed
    service_column_map = {
        "TM - Fuzzy Matches": "TM - Fuzzy Match",
        "TM - Exact Matches": "TM - Exact Match",
    }
    service_lookup = service_column_map.get(service, service)
    try:
        mask = (df_s_iqvia["Source Language"] == source_lang) & \
               (df_s_iqvia["Target Language"] == target_lang)
        row = df_s_iqvia[mask]
        if not row.empty:
            if service_lookup in df_s_iqvia.columns:
                rate = row[service_lookup].iloc[0]
                return float(rate) if pd.notna(rate) else 0
            else:
                if service in ["Translation", "Machine Translation"]:
                    print(f"Warning: Service '{service_lookup}' not found in worksheet '{CurrentWS}'")
    except Exception as e:
        print(f"Error getting word rate for {service}: {str(e)}")
    return 0

def get_hourly_rate(df_s_iqvia, service):
    """Get hourly rate from S IQVIA worksheet first row"""
    try:
        # Get the rate from the first row of the service column
        if service in df_s_iqvia.columns:
            rate = df_s_iqvia[service].iloc[0]
            return float(rate) if pd.notna(rate) else 0
    except Exception as e:
        print(f"Error getting hourly rate: {e}")
    return 0

# Add this function before update_preview
def get_preview_quantity(service):
    """Get the quantity value from the preview grid for a given service"""
    entry = preview_quantities.get(service)
    if entry:
        try:
            return float(entry.get().strip())
        except ValueError:
            return 0
    return 0

def sanitize_csv_value(val):
    import pandas as pd
    if pd.isna(val) or val is None or str(val).lower() == 'nan':
        return ""
    return str(val)

def save_charges_csv():
    # Get the count of saved Language Pairs (LPs)
    lp_count = len(LPs)
    if lp_count == 0:
        messagebox.showwarning("No Language Pairs", "Please save at least one Language Pair before saving charges.")
        return

    # Get selected services
    selected_services = [svc for svc, var in checkbox_state.items() if var.get()]
    if not selected_services:
        messagebox.showwarning("No Services Selected", "Please select at least one service before saving charges.")
        return

    # Get values directly using the global function
    context_value = get_quoteMe_value("Context:")
    hundred_percent_value = get_quoteMe_value("100%:")
    repetitions_value = get_quoteMe_value("Repetitions:")
    fuzzy_matches_value = get_quoteMe_value("Fuzzy Matches:")
    new_words_value = get_quoteMe_value("New Words:")

    # Calculate sums for TM services
    word_counts = {
        "new_words": new_words_value,
        "tm_exact": context_value + hundred_percent_value,
        "tm_fuzzy": repetitions_value + fuzzy_matches_value
    }

    # Create a DataFrame with headers and duplicated services for each LP
    rows = []

    # Read the S IQVIA worksheet for rates
    try:
        df_s_iqvia = pd.read_excel(
            get_excel_path(), 
            sheet_name=CurrentWS
        )
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read rates from ratesheet: {e}")
        return

    # Prepare quantities and rates for all services
    try:
        hourly_divider = HourlyDivider.get()
        if hourly_divider <= 0:
            messagebox.showerror("Error", "Hourly divider must be greater than zero.")
            return
    except:
        hourly_divider = 1000

    # Determine which service to use for each LP
    use_machine_translation = "Machine Translation" in selected_services
    use_translation = "Translation" in selected_services

    # If both are checked, treat as Machine Translation only
    if use_machine_translation:
        effective_services = [svc for svc in selected_services if svc != "Translation"]
    else:
        effective_services = selected_services[:]

    # Track LPs that will fallback to Translation
    fallback_lps = []

    for lp in LPs:
        source_language = lp.split(" into ")[0]
        target_language = lp.split(" into ")[1]

        # Determine which service to use for this LP
        services_for_lp = []
        if use_machine_translation:
            # Check if Machine Translation rate exists for this LP
            mt_rate = get_word_rate(df_s_iqvia, source_language, target_language, "Machine Translation")
            if mt_rate and mt_rate > 0:
                services_for_lp = [svc for svc in effective_services if svc != "Translation"]  # Use MT, remove Translation
                # Insert Machine Translation at the correct position if needed
                if "Machine Translation" not in services_for_lp:
                    services_for_lp.insert(0, "Machine Translation")
            else:
                # Fallback to Translation for this LP
                fallback_lps.append(lp)
                services_for_lp = [svc for svc in effective_services if svc != "Machine Translation"]
                if "Translation" not in services_for_lp:
                    services_for_lp.insert(0, "Translation")
        elif use_translation:
            services_for_lp = [svc for svc in effective_services if svc != "Machine Translation"]
            if "Translation" not in services_for_lp:
                services_for_lp.insert(0, "Translation")
        else:
            # Neither service is selected, skip both
            services_for_lp = [svc for svc in effective_services if svc not in ["Translation", "Machine Translation"]]

        # Prepare quantities and rates for all services for this LP
        quantities = []
        rates = []
        for service in services_for_lp:
            UofM = Services_UofM.get(service, "")
            service_type = get_service_type(service, UofM)
            if service_type == "hType":
                file_type = file_type_var.get()
                quoteme_wc = get_quoteMe_value("Total Words:")
                qtc_wc_translation = get_qtc_value("TC WC for TRANSLATION:")
                qtc_wc_revision = get_qtc_value("TC WC for REVISION:")
                quantity = calculate_hourly_quantity(
                    service,
                    file_type,
                    use_qtc_input,
                    quoteme_wc,
                    qtc_wc_translation,
                    qtc_wc_revision,
                    service_label_mapping
                )
            else:
                quantity = get_service_quantity(service, use_qtc_input)
            quantities.append(quantity)

            # Get rate based on service type
            rate = 0
            if service_type == "wcType":
                rate = get_word_rate(df_s_iqvia, source_language, target_language, service)
            elif service_type == "hType":
                rate = get_hourly_rate(df_s_iqvia, service)
            rates.append(rate)

        # First pass: build all row data, but leave Project Management and Rush Premium rates as None
        row_data = []
        for i, service in enumerate(services_for_lp):
            UofM = Services_UofM.get(service, "")
            service_type = get_service_type(service, UofM)
            group1 = ServiceGroup1.get(service, "")
            group2 = ServiceGroup2.get(service, "")

            if pd.isna(group1) or group1 is None:
                group1 = ""
            if pd.isna(group2) or group2 is None:
                group2 = ""

            if service == "Project Management":
                quantity = get_preview_quantity(service)
                quantity_csv = float(quantity) / 100
                rate = None  # To be filled in second pass
                quantity_out = quantity_csv
            elif service == "Rush Premium":
                quantity = get_preview_quantity(service)
                quantity_csv = float(quantity) / 100
                rate = None  # To be filled in second pass
                quantity_out = quantity_csv
            else:
                quantity_out = quantities[i]
                rate = rates[i]

            row_data.append({
                "service": service,
                "UofM": UofM,
                "group1": group1,
                "group2": group2,
                "quantity": quantity_out,
                "rate": rate,
                "orig_quantity": quantities[i] if i < len(quantities) else 0,
                "orig_rate": rates[i] if i < len(rates) else 0,
            })

        # --- Apply Min Fee logic before calculating Project Management and Rush Premium ---
        # Find sumproduct for Word services except Back Translation
        word_sumproduct = sum(
            float(row["quantity"]) * float(row["rate"])
            for row in row_data
            if Services_UofM.get(row["service"], "") == "Word" and row["service"] != "Back Translation"
        )
        min_fee = MinFeeRate.get() if isinstance(MinFeeRate, IntVar) else MinFeeRate

        if word_sumproduct < min_fee:
            for row in row_data:
                if row["service"] in ["Translation", "Machine Translation"]:
                    row["UofM"] = "Minimum"
                    row["quantity"] = 1
                    row["rate"] = min_fee
                elif Services_UofM.get(row["service"], "") == "Word" and row["service"] != "Back Translation":
                    row["quantity"] = 0

        # Back Translation min fee logic
        bt_row = next((row for row in row_data if row["service"] == "Back Translation"), None)
        if bt_row:
            bt_sum = float(bt_row["quantity"]) * float(bt_row["rate"])
            if bt_sum < min_fee:
                bt_row["UofM"] = "Minimum"
                bt_row["quantity"] = 1
                bt_row["rate"] = min_fee

        # --- Now calculate Project Management and Rush Premium rates using updated row_data ---
        for i, row in enumerate(row_data):
            if row["service"] == "Project Management":
                # Project Management rate: sum of all services above (excluding itself)
                total_value = 0
                for j in range(i):
                    total_value += float(row_data[j]["quantity"]) * float(row_data[j]["rate"])
                row["rate"] = round(total_value, 6)
            elif row["service"] == "Rush Premium":
                # Rush Premium rate: sum of all services above (including Project Management and itself)
                total_value = 0
                for j in range(i + 1):
                    q = float(row_data[j]["quantity"])
                    r = float(row_data[j]["rate"]) if row_data[j]["rate"] is not None else 0
                    total_value += q * r
                row["rate"] = round(total_value, 6)

        # Now write rows to CSV
        for row in row_data:
            rows.append({
                Headers[0]: sanitize_csv_value("x" if len(rows) % len(services_for_lp) == 0 else ""),
                Headers[1]: sanitize_csv_value(f"{source_language} into {target_language}"),
                Headers[2]: sanitize_csv_value(source_language),
                Headers[3]: sanitize_csv_value(target_language),
                Headers[4]: sanitize_csv_value(0),
                Headers[5]: sanitize_csv_value(0),
                Headers[6]: sanitize_csv_value(row["group1"]),
                Headers[7]: sanitize_csv_value(row["group2"]),
                Headers[9]: sanitize_csv_value(row["service"]),
                Headers[10]: sanitize_csv_value(row["UofM"]),
                Headers[11]: sanitize_csv_value(row["quantity"]),
                Headers[12]: sanitize_csv_value(row["rate"]),
            })

    # Notify user if any LPs fell back to Translation
    if fallback_lps:
        messagebox.showinfo(
            "Machine Translation Fallback",
            "The following Language Pairs do not have a Machine Translation rate and will use Translation instead:\n\n" +
            "\n".join(fallback_lps)
        )

    # Create DataFrame directly from rows
    df = pd.DataFrame(rows, columns=Headers)

    # Replace NaN values with empty strings
    df = df.fillna('')
    df.replace(to_replace=[float('nan'), 'nan', None], value='', inplace=True)

    # --- Calculate sumproduct for Word services except Back Translation, per LP ---
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    df["Rate"] = pd.to_numeric(df["Rate"], errors="coerce").fillna(0)
    min_fee = MinFeeRate.get() if isinstance(MinFeeRate, IntVar) else MinFeeRate

    for lp in df["Line Item Description"].unique():
        lp_mask = df["Line Item Description"] == lp
        # Calculate sumproduct for this LP (excluding Back Translation)
        lp_word_mask = lp_mask & (df["UofM"] == "Word") & (df["Service"] != "Back Translation")
        lp_bt_mask = lp_mask & (df["UofM"] == "Word") & (df["Service"] == "Back Translation")
        lp_sumproduct = (df.loc[lp_word_mask, "Quantity"] * df.loc[lp_word_mask, "Rate"]).sum()
        lp_bt_sum = (df.loc[lp_bt_mask, "Quantity"] * df.loc[lp_bt_mask, "Rate"]).sum()

        # Append sumproduct to CommentsForInvoice for this LP's Word services (except Back Translation)
        #df.loc[lp_word_mask, "CommentsForInvoice"] = f"Sumproduct: {lp_sumproduct:.3f}"

        # For Back Translation, append its own sumproduct (row-wise)
        '''for idx in df[lp_bt_mask].index:
            bt_sum = df.at[idx, "Quantity"] * df.at[idx, "Rate"]
            df.at[idx, "CommentsForInvoice"] = f"Sumproduct: {bt_sum:.3f}" '''

        # --- Enforce Min Fee Logic per LP ---
        if lp_sumproduct < min_fee:
            for svc in ["Translation", "Machine Translation"]:
                svc_mask = lp_mask & (df["Service"] == svc)
                if svc_mask.any():
                    df.loc[svc_mask, "UofM"] = "Minimum"
                    df.loc[svc_mask, "Quantity"] = 1
                    df.loc[svc_mask, "Rate"] = min_fee
            # Set other Word services (except Back Translation) quantity to 0
            other_word_mask = lp_word_mask & ~df["Service"].isin(["Translation", "Machine Translation"])
            df.loc[other_word_mask, "Quantity"] = 0
        # Back Translation min fee logic
        if bt_sum < min_fee:
            bt_mask = lp_mask & (df["Service"] == "Back Translation")
            if bt_mask.any():
                df.loc[bt_mask, "UofM"] = "Minimum"
                df.loc[bt_mask, "Quantity"] = 1
                df.loc[bt_mask, "Rate"] = min_fee


            # Set other Word services (except Back Translation) quantity to 0
            other_word_mask = lp_word_mask & ~df["Service"].isin(["Translation", "Machine Translation"])
            df.loc[other_word_mask, "Quantity"] = 0
        # Back Translation min fee logic
        if bt_sum < min_fee:
            bt_mask = lp_mask & (df["Service"] == "Back Translation")
            if bt_mask.any():
                df.loc[bt_mask, "UofM"] = "Minimum"
                df.loc[bt_mask, "Quantity"] = 1
                df.loc[bt_mask, "Rate"] = min_fee

    # Save to CSV with explicit UTF-8 encoding and no BOM
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if file_path:
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        messagebox.showinfo("Success", "Charges saved successfully!")

# Add "Delete Workflow" button
def delete_workflow():
    global workflows
    if not WFlistbox.curselection():
        messagebox.showwarning("No Selection", "Please select a workflow to delete.")
        return
    selected_workflow = WFlistbox.get(WFlistbox.curselection())
    if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the workflow '{selected_workflow}'?"):
        if workflow_manager.delete_workflow(CurrentWS, selected_workflow):
            workflows = workflow_manager.get_workflows_for_account(CurrentWS)
            WFlistbox.delete(WFlistbox.curselection())
            messagebox.showinfo("Success", f"Workflow '{selected_workflow}' deleted successfully.")

# Add "Delete Workflow" button to the WorkflowsFrame
delete_workflow_button = ctk.CTkButton(
    WorkflowsFrame, text="Delete Workflow", command=delete_workflow, width=160
)
delete_workflow_button.pack(pady=PADY_ITEM)

# Add "Save Charges CSV" button to the bottom of the PreviewFrame
save_charges_button = ctk.CTkButton(
    PreviewFrame, 
    text="Save Charges CSV", 
    command=save_charges_csv, 
    width=200  # Adjust width as needed
)
save_charges_button.grid(row=2, column=0, columnspan=3, pady=10, sticky="ew")  # Place at the bottom of the ASP frame


# Add the button somewhere in your UI, for example, top right corner of main_content
admin_config_button = ctk.CTkButton(
    main_content, text="Admin Config", width=100, 
    command=lambda: open_admin_config(
        root, FONT, Services, Services_UofM, 
        on_save=reload_service_label_mapping, 
        ratesheet_name=CurrentWS,
        account_key=CurrentWS
    )
)

admin_config_button.grid(row=3, column=2, padx=5, pady=5, sticky="ne")

def populate_test_values():
    global suspend_preview_update
    suspend_preview_update = True
    # Populate Services checkboxes
    test_services = [
        "Translation", "TM - Fuzzy Match", "TM - Exact Match", 
        "Machine Translation", "Formatting", "Review", "Proofreading",
        "Desktop Publishing (DTP)", "Back Translation", "Editing",
        "Reconciliation", "Project Management", "Rush Premium"
    ]
    for service in test_services:
        if service in checkbox_state:
            checkbox_state[service].set(True)

    # Populate QuoteMe values
    """ test_quoteme_values = {
        "Context:": "500",
        "100%": "100",
        "Repetitions:": "200",
        "Fuzzy Matches:": "100",
        "New Words:": "2500"
    } """

    # Set Source and Target Languages
    source_language_dropdown.set("English (GB)")
    target_language_dropdown.set("German (Austria)")

    # Add test Language Pairs
    global LPs
    '''LPs = [
        "English (GB) into French (Canada)",
        "English (GB) into Italian (Switzerland)",
        "English (GB) into German (Austria)"
    ]'''
    refresh_lp_listbox()

    # Add test workflows
     # Add test workflows
    """test_workflows = ["Trans + proof", "trans + bt", "allDevTestWF"]
    for workflow in test_workflows:
        if workflow not in workflows:
            WFlistbox.insert("end", workflow)
    suspend_preview_update = False"""
    update_preview()  # Only call once after all changes

# 3. Then define populate_languages function
def populate_languages():
    """Populate Languages list from current worksheet and update dropdowns"""
    global Languages
    prev_source = source_language_dropdown.get()
    prev_target = target_language_dropdown.get()
    Languages.clear()
    try:
        df_s_iqvia = pd.read_excel(
            get_excel_path(),
            sheet_name=CurrentWS
        )
        source_languages = df_s_iqvia["Source Language"].dropna().unique()
        target_languages = df_s_iqvia["Target Language"].dropna().unique()
        unique_languages = sorted(set(source_languages).union(set(target_languages)))
        Languages.extend(unique_languages)
        source_language_dropdown['values'] = Languages
        target_language_dropdown['values'] = Languages
        # Restore previous selection if still valid
        if prev_source in Languages:
            source_language_dropdown.set(prev_source)
        else:
            source_language_dropdown.set("Select Source Language")
        if prev_target in Languages:
            target_language_dropdown.set(prev_target)
        else:
            target_language_dropdown.set("Select Target Language")
        # Clear existing language pairs
        global LPs
        LPs.clear()
        refresh_lp_listbox()
    except KeyError:
        messagebox.showerror("Error", f"The worksheet '{CurrentWS}' does not contain the required columns.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# 4. Finally call populate_languages
populate_languages()

# Call the function to populate test values
populate_test_values()
create_preview_header()

canvas.grid(row=0, column=0, sticky="nsew")
vscrollbar.grid(row=0, column=1, sticky="ns")
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Bind preview updates
def bind_preview_updates():
    # Unbind previous events if needed (not strictly necessary unless rebinding)
    # Bind checkbox state changes
    for var in checkbox_state.values():
        var.trace_add("write", update_preview)

    # Bind QuoteMe entries
    for entry in quoteMe_entries.values():
        entry.bind("<KeyRelease>", update_preview)

    # Bind hourly divider
    hourly_divider_input.bind("<KeyRelease>", update_preview)

bind_preview_updates()
update_preview()  # Add this line to force initial update


# Set max with to match the container frame
ServicesFrame.grid_propagate(True)
ContainerFrame1.grid_propagate(True)
ContainerFrame.grid_propagate(True)

# Replace all direct checkbox creation with refresh_service_checkboxes()
refresh_service_checkboxes()

# Calculate total width and set geometry
#TOTAL_WIDTH = MAX_WIDTH_SERVICES + MAX_WIDTH_WORKFLOWS + MAX_WIDTH_QUOTEME + 40  # 40 for padding
TOTAL_HEIGHT = 1000  # Or whatever height you want


class TheOneBPApp:
    """The One-Stop Shop Application wrapper class."""
    
    def __init__(self):
        """Initialize the application."""
        # The root window and all UI elements are already initialized globally above
        pass
    
    def run(self):
        """Run the application main loop."""
        try:
            root.mainloop()
        except KeyboardInterrupt:
            print("\nProgram terminated by user")
            root.quit()


if __name__ == '__main__':
    app = TheOneBPApp()
    app.run()

