# AutomationSuite - Complete Repository Architecture

**Last Updated:** June 10, 2026  
**Version:** 2.0.2

## 📊 Executive Summary

AutomationSuite is a **unified multi-project Python workspace** for translation/localization automation. It processes translation jobs, manages rate cards, automates Excel workflows, and validates data. The system has a shared **Core** module that provides common functionality to specialized tools.

---

## 📁 FOLDER STRUCTURE & PURPOSE

### 1. **Core/** - Shared Core Module
**Purpose:** Central repository for reusable business logic, data processing, and configuration management

**Key Responsibilities:**
- Workflow and account management
- Service mapping and normalization
- Rate calculations and charges generation
- Language pair management
- PA (ProjectA) template management
- Email parsing for quote data
- Excel I/O and DataFrame processing
- Validators and utilities

**File Categories:**

#### Core Modules (Python Files)
| Module | Purpose |
|--------|---------|
| `account_workflow_manager.py` | Manages accounts and their translation workflows; loads/saves account configurations |
| `entity_service_mapper.py` | Maps service names between different entities with TPUS as master |
| `service_mapper.py` | Normalizes service names across rate cards to canonical names |
| `language_pair_manager.py` | Validates and manages language pair combinations |
| `language_normalizer.py` | Normalizes language names for consistent processing |
| `quoteme_email_parser.py` | Parses TransPerfect QuoteMe emails for language pair data and word counts |
| `quoteme_value_mapper.py` | Maps QuoteMe parsed data to system values |
| `pa_template_manager.py` | CRUD operations for PA (ProjectA) template configurations |
| `pa_template_processor.py` | Applies PA templates to DataFrames for PA import generation |
| `workflow_manager.py` | Loads and saves workflow configurations |
| `workflow_translator.py` | Legacy workflow translation utilities |
| `WF_Matrix.py` | Master matrix of all entities and their PA services (TPUS is canonical) |
| `rate_calculations.py` | Calculates charges based on service types and configurations |
| `charges_engine.py` | Generic charges engine - generates charges for translation jobs |
| `charges_engine_ceva.py` | CEVA-specific charges engine with language-pair rates |
| `excel_io.py` | Excel file reading/writing operations |
| `df_processing.py` | Common DataFrame processing operations |
| `validators.py` | Data validation utilities |
| `sync_entities.py` | Syncs entities to master TPUS configuration |

#### Configuration Files (JSON)
| File | Purpose | Contains |
|------|---------|----------|
| `accounts_workflows.json` | Account and workflow definitions | Account names, workflows, services per workflow |
| `entity_services.json` | Entity service mappings | Service names by entity (TPUS, TPTDE, etc.) |
| `service_mappings.json` | Cross-entity service mappings | Maps service names between entities |
| `canonical_services.json` | Master canonical service list | Standard service names for normalization |
| `service_classification.json` | Service type classifications | Groups services by type (Translation, TM, etc.) |
| `language_mapping.json` | Language code mappings | Language normalizations |
| `master_rate_cards.json` | Master rate data | Rate structures by entity/language |
| `pa_template_configs.json` | PA template definitions | Field mappings for ProjectA imports |
| `job_data_config.json` | Job data field configurations | Field definitions and mappings |
| `column_preferences.json` | UI column display preferences | Display preferences for tables |

#### Directories
| Directory | Purpose |
|-----------|---------|
| `utils/` | Helper modules: logger, file paths, helpers |
| `accounts/` | Account-specific data |
| `mappings/` | Service and entity mappings |
| `templates/` | PA template files |
| `configs/` | Configuration files |
| `entity_service_aliases/` | Entity-specific service aliases |

---

### 2. **CEVA_Launcher/** - Document Processing & Translation Workflow Automation
**Status:** ✅ Fully operational (v2.0.2)

**Purpose:** Automates document processing and translation workflows for CEVA system with:
- Document word counting (native + OCR for scanned PDFs)
- NoQuote XLS data matching
- Excel charges integration
- Browser automation for TransPerfect ProjectA
- Real-time job monitoring

**Entry Points:**
- `Launcher.py` - Main launcher (CLI mode selection)
- `gui_controller.py` - GUI mode (interactive interface)
- `main_orchestrator.py` - Command-line orchestration

**Key Modules:**

| Module | Purpose |
|--------|---------|
| `Launcher.py` | Main entry point - mode selection (GUI/CLI) |
| `KickOff.py` | Excel automation for ProjectA imports; renames worksheets and triggers import |
| `main_orchestrator.py` | Coordinates FileCounter, OCR, NoQuote, and data merging |
| `FileCounter.py` | Extracts word counts from ZIP files; integrates Tesseract OCR for scanned PDFs |
| `ocr_counter.py` | OCR processing for image-based PDFs |
| `NoQuote.py` | Reads NoQuote XLS files and extracts metadata |
| `BrowserRead.py` / `browser_monitor.py` | Browser automation via Playwright; detects Firefox/Chrome/Edge tabs |
| `ChargesIntegration.py` | Integrates charges data with job information |
| `gui_controller.py` | Full GUI interface for job processing control |
| `transperfect_macros.py` | Analyzes TransPerfect macro definitions |
| `shared_data.py` | Global DataFrames: WC_DF, CEVA_DF, PO_DF |

**Data Files:**
| File | Purpose |
|------|---------|
| `browser_tabs.csv` | Cached browser tab information |
| `CEVA RATES.xlsx` | Language pair rates data |
| `CevaKO.xlsm` | Excel template with macros |
| `ChargesIntegration.py` | Charges calculation integration |

**Processing Pipelines:**

1. **Word Count Pipeline:**
   - ZIP files → FileCounter.py → Extract PDFs → Text/OCR processing → WC_DF
   
2. **NoQuote Integration:**
   - XLS file → NoQuote.py → Extract metadata → CEVA_DF
   
3. **Charges Integration:**
   - WC_DF + Rates → ChargesIntegration.py → Generate charges

4. **ProjectA Import:**
   - Prepared worksheets → KickOff.py → Browser automation → Import to ProjectA

---

### 3. **One_Stop_Shop/** - Multi-Scenario Translation Quote Calculator
**Status:** ✅ Active template ready for customization

**Purpose:** Central hub for:
- Job data import from multiple sources
- Translation service quote calculations
- Entity management
- Service mapping configuration
- Workflow management
- PA template configuration
- Rate card integration

**Entry Points:**
- `one_stop_shop_main.py` - Main entry (wrapper)
- `oss_main.py` - Core application
- `theonebp_app.py` - TheOneBP UI application (primary)
- `launch_main.py` - Alternative launcher
- `launch_entity_manager.py` - Entity management launcher
- `launch_service_mapper.py` - Service mapping launcher
- `launch_workflow_manager.py` - Workflow management launcher

**Key Modules:**

| Module | Purpose |
|--------|---------|
| `theonebp_app.py` | Main GUI application - multi-tab interface for quote calculation |
| `oss_main.py` / `oss_main_old.py` | Configuration-driven application wrapper |
| `admin_config_ui.py` / `admin_config_legacy.py` | Admin configuration panels |
| `entity_manager_integration.py` | Entity creation/editing integration |
| `quoteme_parser_ui.py` | QuoteMe email parsing UI tab |
| `scenario_modules/` | Scenario-specific modules |

**GUI Components (in `gui/`):**
| Component | Purpose |
|-----------|---------|
| `entity_manager_gui.py` | Entity CRUD operations |
| `service_mapping_gui.py` | Service mapping configuration |
| `workflow_manager_gui.py` | Workflow editing |
| `pa_template_mapper_gui.py` | PA template configuration |

**Configuration Files:**
| File | Purpose |
|------|---------|
| `oss_config.yaml` | Application settings (ratesheet, theme, defaults) |
| `workflows.json` | Workflow definitions for accounts |
| `service_label_mapping.json` | Custom service label mappings |
| `One_BP_IQ fixed.01.xlsx` | Rate card template |

**Build & Deployment:**
| File | Purpose |
|------|---------|
| `build_executable.py` | Builds standalone .exe |
| `OneStopShop.spec` | PyInstaller specification |
| `requirements.txt` | Python dependencies |

**Documentation:**
- `README_MAIN_GUI.md` - Main GUI documentation
- `LAUNCH_MAIN_CONNECTION_MAP_README.md` - Architecture and connection map
- Various implementation guides (Entity Manager, Service Editor, PA Templates, etc.)

---

### 4. **KP_Validator/** - Validation Automation Tool
**Status:** ✅ Template ready

**Purpose:** Validates data against configurable rules

**Entry Point:**
- `validator_main.py` - Main validator application

**Files:**
| File | Purpose |
|------|---------|
| `validator_main.py` | Main validator class |
| `validator_rules.json` | Validation rule definitions |

**Functionality:**
- Loads validation rules from JSON
- Validates data against rule sets
- Reports validation errors
- Integrates with Core modules for data validation

---

### 5. **Shared_UI/** - Reusable UI Components
**Status:** ✅ Available for shared use

**Purpose:** Provides reusable UI components and themes for all projects

**Structure:**
| Item | Purpose |
|------|---------|
| `components/` | Reusable CTk components |
| `templates/` | Common UI templates |
| `ui_theme.json` | Color theme and styling definitions |

---

### 6. **Rate_Card_Builder/** - Rate Card Management
**Status:** ✅ Operational

**Purpose:** Creates and manages translation service rate cards with multiple formats

**Entry Point:**
- `rate_card_builder_main.py` - Standalone GUI application

**Key Modules:**

| Module | Purpose |
|--------|---------|
| `rate_card_builder_main.py` | Main GUI for rate card creation |
| `rate_card_builder_integrated.py` | Integration with One_Stop_Shop |
| `itemized_rate_card_window.py` | Editor for itemized rate cards |
| `itemized_rate_card_editor.py` | Itemized rate editing logic |
| `tiered_rate_card_window.py` | Editor for tiered rate cards |
| `load_rate_card_window.py` | Load existing rate cards |
| `excel_rate_card_loader.py` | Load rate cards from Excel files |
| `language_loader.py` | ISO language code loading |

**Data Files:**
| File | Format | Purpose |
|------|--------|---------|
| `rate_cards_*.json` | JSON | Rate card definitions (Clario, FORTREA, HS, icon, etc.) |
| `rate_cards_*.csv` | CSV | CSV export format |
| `Canonical_Service_Names.json` | JSON | Canonical service definitions |
| `languages_iso_codes.json` | JSON | ISO language codes |
| `service_columns.json` | JSON | Service column definitions |

---

## 🔄 DATA FLOW BETWEEN COMPONENTS

### Flow 1: Quote Calculation Pipeline (One_Stop_Shop)
```
Job Data Input (Email/File)
    ↓
QuoteMe Email Parser (quoteme_email_parser.py)
    ↓ Extracts: Language pairs, word counts, file breakdowns
    ↓
Service Selection UI (workflow_manager_gui.py)
    ↓ Selects account & workflow
    ↓
PA Template Application (pa_template_processor.py)
    ↓ Maps job data to template fields
    ↓
Rate Lookup (rate_calculations.py, charges_engine.py)
    ↓ Uses entity's rate card (from Core/master_rate_cards.json)
    ↓
Charges Generation & Export
```

### Flow 2: CEVA Document Processing Pipeline
```
Input ZIP File (with PDFs)
    ↓
FileCounter.py / OCR Processing
    ↓ Extracts word counts; uses OCR for scanned files
    ↓ Populates WC_DF (Submission ID, Total WC, File Status)
    ↓
NoQuote.py (Parallel)
    ↓ Reads XLS file → CEVA_DF (Sponsor, Protocol, PO Number, etc.)
    ↓
Data Merging (main_orchestrator.py)
    ↓ Joins WC_DF + CEVA_DF on Submission ID
    ↓
ChargesIntegration.py
    ↓ Calculates charges using rates + word counts
    ↓
KickOff.py (Excel Automation)
    ↓ Writes to Excel worksheets
    ↓ Triggers browser automation for ProjectA import
    ↓
ProjectA (via BrowserRead/gui_controller)
    ↓ Final import to TransPerfect system
```

### Flow 3: Entity & Service Management
```
WF_Matrix.py (Master Configuration)
    ↓ Contains PA_SERVICES for all entities (TPUS is canonical)
    ↓
EntityServiceMapper → Maps services between entities
    ↓
ServiceMapper → Normalizes service names to canonical
    ↓
AccountWorkflowManager → Maps accounts to workflows to services
    ↓
Various UIs (entity_manager_gui, service_mapping_gui, etc.)
    ↓ Used by One_Stop_Shop for configuration
```

### Flow 4: Configuration Hierarchy
```
WF_Matrix.py (Master entity services)
    ↓
entity_services.json (Entity service lists)
    ↓
service_mappings.json (Entity-to-entity mappings)
    ↓
canonical_services.json (Normalization target)
    ↓
accounts_workflows.json (Account-specific workflows)
    ↓
pa_template_configs.json (ProjectA field mappings)
```

---

## 📊 KEY PYTHON MODULES & THEIR RESPONSIBILITIES

### Core Business Logic
- **Workflow & Account Management:** account_workflow_manager.py, WF_Matrix.py
- **Service Operations:** entity_service_mapper.py, service_mapper.py, service_classification.json
- **Language Operations:** language_pair_manager.py, language_normalizer.py
- **Rate & Charges:** rate_calculations.py, charges_engine.py, charges_engine_ceva.py
- **PA Integration:** pa_template_manager.py, pa_template_processor.py

### Data Processing
- **Email Parsing:** quoteme_email_parser.py, quoteme_value_mapper.py
- **DataFrame Operations:** df_processing.py
- **Excel I/O:** excel_io.py
- **Validation:** validators.py

### CEVA-Specific
- **Document Processing:** FileCounter.py, ocr_counter.py
- **Data Integration:** NoQuote.py, ChargesIntegration.py
- **Excel Automation:** KickOff.py
- **Browser Control:** BrowserRead.py, browser_monitor.py

### UI & Configuration
- **Admin Configuration:** admin_config_ui.py
- **Entity Management:** entity_manager_integration.py + gui/entity_manager_gui.py
- **Rate Card Management:** rate_card_builder_main.py
- **Shared Components:** Shared_UI modules

---

## 📋 CONFIGURATION & DATA FILES

### Master Configuration Files
| File | Location | Purpose |
|------|----------|---------|
| `WF_Matrix.py` | Core/ | Master entity and PA service definitions |
| `accounts_workflows.json` | Core/ | Account → Workflow → Service mappings |
| `entity_services.json` | Core/ | Service definitions per entity |
| `canonical_services.json` | Core/ | Master service name definitions |

### Rate & Pricing Files
| File | Location | Purpose |
|------|----------|---------|
| `master_rate_cards.json` | Core/ | Rate card data by entity/language |
| `CEVA RATES.xlsx` | CEVA_Launcher/ | CEVA-specific language pair rates |
| `rate_cards_*.json` | Rate_Card_Builder/ | Format-specific rate cards |

### Application Configuration
| File | Location | Purpose |
|------|----------|---------|
| `oss_config.yaml` | One_Stop_Shop/ | Application settings (theme, defaults) |
| `workflows.json` | One_Stop_Shop/ | Workflow templates |
| `pa_template_configs.json` | Core/ | PA import field mappings |
| `validator_rules.json` | KP_Validator/ | Validation rule definitions |

### UI Configuration
| File | Location | Purpose |
|------|----------|---------|
| `service_label_mapping.json` | One_Stop_Shop/ | Custom service labels |
| `ui_theme.json` | Shared_UI/ | UI colors and themes |
| `column_preferences.json` | Core/ | Table column display preferences |

---

## 🎯 ENTRY POINTS (How to Run Each Component)

### CEVA_Launcher
```bash
# Main launcher (interactive mode selection)
python Launcher.py

# Direct GUI mode
python gui_controller.py

# CLI mode with orchestrator
python main_orchestrator.py

# Excel automation only
python KickOff.py
```

### One_Stop_Shop
```bash
# Main application
python one_stop_shop_main.py
# or
python oss_main.py
# or
python theonebp_app.py

# Specific launchers
python launch_main.py
python launch_entity_manager.py
python launch_service_mapper.py
python launch_workflow_manager.py
```

### KP_Validator
```bash
python validator_main.py
```

### Rate_Card_Builder
```bash
python rate_card_builder_main.py
```

---

## 🔗 KEY DEPENDENCIES & INTEGRATIONS

### Python Libraries
- **Data Processing:** pandas, numpy
- **UI:** customtkinter, tkinter, tkinterdnd2
- **Excel:** openpyxl, xlrd
- **Browser Automation:** Playwright, pyautogui
- **System:** win32com, psutil, pywin32
- **Configuration:** pyyaml, json
- **Utility:** regex, pathlib

### Cross-Module Dependencies
- **All modules depend on:** Core for business logic
- **One_Stop_Shop depends on:** Core, Rate_Card_Builder
- **CEVA_Launcher depends on:** Core (for rates), ChargesIntegration
- **KP_Validator depends on:** Core for validation utilities
- **Shared_UI used by:** One_Stop_Shop, CEVA_Launcher, Rate_Card_Builder

---

## 📈 System Architecture Summary

```
┌─────────────────────────────────────────────┐
│         AutomationSuite (Master)            │
└─────────────────────────────────────────────┘
         ↓           ↓           ↓
    ┌────────────┬─────────────┬──────────────┐
    ↓            ↓             ↓              ↓
┌────────┐  ┌──────────┐ ┌──────────┐  ┌──────────┐
│ Core   │  │   CEVA   │ │One Stop  │  │Rate Card │
│Shared  │  │Launcher  │ │  Shop    │  │ Builder  │
│Logic   │  │Document  │ │Quote     │  │(Shared)  │
│        │  │Process   │ │Calc      │  │          │
└────────┘  └──────────┘ └──────────┘  └──────────┘
    ↑           ↑             ↑              ↑
    └───────────┴─────────────┴──────────────┘
            ↓
    ┌─────────────────────┐
    │   Shared_UI         │
    │ (Components/Themes) │
    └─────────────────────┘
```

---

## 🚀 Getting Started

1. **For Quote Calculations:** Start with `One_Stop_Shop/one_stop_shop_main.py`
2. **For Document Processing:** Start with `CEVA_Launcher/Launcher.py`
3. **For Rate Card Management:** Start with `Rate_Card_Builder/rate_card_builder_main.py`
4. **For Understanding Data:** Review `Core/WF_Matrix.py` and configuration files

---

## 📚 Key Documentation Files

- `One_Stop_Shop/LAUNCH_MAIN_CONNECTION_MAP_README.md` - Architecture map
- `One_Stop_Shop/README_MAIN_GUI.md` - GUI documentation
- `Core/SERVICE_MAPPING_SYSTEM.md` - Service mapping architecture
- `Core/EXCEL_USAGE_GUIDE.md` - Excel integration guide
- `CEVA_Launcher/README.md` - CEVA Launcher overview
- `Rate_Card_Builder/README.md` - Rate card documentation

---

## ✅ System Status

| Component | Status | Version | Notes |
|-----------|--------|---------|-------|
| Core | ✅ Active | 2.0 | Shared by all modules |
| CEVA_Launcher | ✅ Operational | 2.0.2 | Fully migrated, production ready |
| One_Stop_Shop | ✅ Active | 1.1.0 | Template ready, active development |
| KP_Validator | ✅ Ready | 1.0 | Template ready |
| Shared_UI | ✅ Available | 1.0 | For shared use |
| Rate_Card_Builder | ✅ Operational | 1.0 | Standalone and integrated |

