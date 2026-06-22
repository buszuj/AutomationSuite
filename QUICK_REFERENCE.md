# AutomationSuite - Quick Reference Guide

## 🎯 WHAT EACH FOLDER DOES

### Core/
```
┌─────────────────────────────────────────────────────┐
│ CORE - Shared Business Logic & Configuration       │
├─────────────────────────────────────────────────────┤
│ • Workflow & Account Management                    │
│ • Entity & Service Mapping (TPUS is master)        │
│ • Rate Calculations & Charges Generation           │
│ • Language Pair & Normalization                    │
│ • PA (ProjectA) Template Management                │
│ • Email Parsing for Quote Data                     │
│ • Excel I/O & DataFrame Processing                │
│ • Data Validation                                  │
└─────────────────────────────────────────────────────┘
Files: ~20 Python modules + 10+ JSON config files
```

### CEVA_Launcher/
```
┌─────────────────────────────────────────────────────┐
│ CEVA_LAUNCHER - Document Processing Pipeline      │
├─────────────────────────────────────────────────────┤
│ Launcher.py → Mode Selection (CLI/GUI)             │
│    ↓                                               │
│ [GUI Path]              [CLI Path]                 │
│ gui_controller.py       main_orchestrator.py       │
│    ↓                         ↓                     │
│ FileCounter.py ←→ OCR processing                  │
│ Extract word counts from ZIP/PDFs                  │
│    ↓                                               │
│ NoQuote.py                                         │
│ Read XLS metadata                                  │
│    ↓                                               │
│ Data Merge + ChargesIntegration.py                │
│    ↓                                               │
│ KickOff.py ←→ BrowserRead.py                      │
│ Excel automation + ProjectA import                │
└─────────────────────────────────────────────────────┘
Files: ~40+ Python files + utilities
Entry: Launcher.py
```

### One_Stop_Shop/
```
┌─────────────────────────────────────────────────────┐
│ ONE_STOP_SHOP - Quote Calculator & Job Manager    │
├─────────────────────────────────────────────────────┤
│ Entry: one_stop_shop_main.py / oss_main.py        │
│    ↓                                               │
│ theonebp_app.py (Main GUI)                        │
│    ├─ Job Data Tab                                │
│    │   → Email parser UI                          │
│    │   → Language pair selector                   │
│    ├─ Service Selection Tab                       │
│    │   → Workflow/Service picker                  │
│    ├─ Rates Tab                                   │
│    │   → Rate card display                        │
│    ├─ Charges Tab                                 │
│    │   → Calculated charges                       │
│    ├─ Admin Tab                                   │
│    │   → Entity manager                           │
│    │   → Service mapper                           │
│    │   → Workflow manager                         │
│    └─ Rate Cards Tab                              │
│        → Rate_Card_Builder integration            │
│                                                   │
│ Launchers (in gui/ folder)                        │
│ • entity_manager_gui.py - CRUD entities           │
│ • service_mapping_gui.py - Map services           │
│ • workflow_manager_gui.py - Edit workflows        │
└─────────────────────────────────────────────────────┘
Files: ~30+ Python + configs
Entry: one_stop_shop_main.py
```

### Rate_Card_Builder/
```
┌─────────────────────────────────────────────────────┐
│ RATE_CARD_BUILDER - Rate Management               │
├─────────────────────────────────────────────────────┤
│ rate_card_builder_main.py (Standalone)            │
│    ↓                                               │
│ GUI Components:                                    │
│ • Itemized rate card editor                       │
│ • Tiered rate card editor                         │
│ • Load existing rate cards                        │
│ • Export to JSON/CSV                              │
│                                                   │
│ Integration:                                       │
│ • rate_card_builder_integrated.py                │
│   (used by One_Stop_Shop)                         │
│                                                   │
│ Utilities:                                         │
│ • excel_rate_card_loader.py                       │
│ • language_loader.py (ISO codes)                  │
└─────────────────────────────────────────────────────┘
Files: ~10 Python modules
Entry: rate_card_builder_main.py
```

### KP_Validator/
```
┌─────────────────────────────────────────────────────┐
│ KP_VALIDATOR - Data Validation Engine             │
├─────────────────────────────────────────────────────┤
│ validator_main.py                                  │
│ • Load validation rules from JSON                 │
│ • Validate data against rules                     │
│ • Report validation errors                        │
│ • Uses Core modules for validation                │
└─────────────────────────────────────────────────────┘
Files: 2 Python files + rules
Entry: validator_main.py
```

### Shared_UI/
```
┌─────────────────────────────────────────────────────┐
│ SHARED_UI - Reusable Components                    │
├─────────────────────────────────────────────────────┤
│ components/   - CTk UI components                  │
│ templates/    - Common UI templates               │
│ ui_theme.json - Color themes & styling            │
│                                                   │
│ Used by: One_Stop_Shop, CEVA_Launcher,           │
│          Rate_Card_Builder                        │
└─────────────────────────────────────────────────────┘
```

---

## 📊 DATA FLOW EXAMPLES

### Example 1: Calculating Translation Quote (One_Stop_Shop)
```
User pastes QuoteMe email
    ↓
QuoteMe Email Parser extracts:
  - Language pairs (e.g., "English > Spanish")
  - Word counts by file
  - TM breakdowns (100%, fuzzy, new)
    ↓
User selects account & workflow
  (e.g., "IQVIA" account, "Full Translation + Proof" workflow)
    ↓
Service Mapper normalizes service names to canonical
    ↓
Rate Calculator looks up rates:
  - Gets rates from rate card (by entity & language pair)
  - Calculates: QTY × RATE = CHARGE
    for each service (Translation, TM-Fuzzy, TM-Exact, etc.)
    ↓
Charges Engine generates total charges
    ↓
Export to Excel or send to ProjectA
```

### Example 2: Processing CEVA Document Job (CEVA_Launcher)
```
User selects ZIP file (contains PDFs)
    ↓ FileCounter.py
Scan all PDFs:
  - Native PDFs → Extract text → Count words
  - Scanned PDFs → Run Tesseract OCR → Count words
  - Store: (Sub_ID, Total_WC, OCR_Used, File_Status)
    ↓ (in parallel) NoQuote.py
User selects XLS file:
  - Read metadata (Sponsor, Protocol, PO#)
  - Store: (Sub_ID, Sponsor, Protocol, PO#, ...)
    ↓
main_orchestrator.py
  - Merge both DataFrames on Sub_ID
  - Create combined job data
    ↓
ChargesIntegration.py
  - Load rates from CEVA RATES.xlsx
  - Calculate: WC × Rate = Charge (by language pair)
    ↓
KickOff.py
  - Write to Excel worksheets
  - Rename worksheets by Sub_ID
    ↓
BrowserRead.py (via gui_controller)
  - Detect Firefox/Chrome/Edge
  - Click "Import to ProjectA" button
  - Submit to TransPerfect system
```

### Example 3: Service Mapping Resolution
```
Rate card has service: "Client Review"
    ↓
ServiceMapper.get_canonical_name()
  - Checks: Is "Client Review" in canonical_services?
  - If YES → Use "Client Review"
  - If NO → Try to find match
    ↓
EntityServiceMapper.get_mapped_name()
  - Check service_mappings.json for entity mapping
  - Example: TPTDE "Client Review" → TPUS "Client Review Implementation"
    ↓
Result: Normalized to "Client Review Implementation"
    ↓
Used in PA template field mapping & charges calculation
```

---

## 🔍 KEY FILES TO UNDERSTAND EACH SYSTEM

### To understand CEVA job flow:
1. `CEVA_Launcher/README.md` - Overview
2. `CEVA_Launcher/shared_data.py` - Global DataFrames (WC_DF, CEVA_DF)
3. `CEVA_Launcher/FileCounter.py` - Word counting logic
4. `CEVA_Launcher/main_orchestrator.py` - Orchestration logic

### To understand Quote calculation:
1. `One_Stop_Shop/LAUNCH_MAIN_CONNECTION_MAP_README.md` - Architecture
2. `One_Stop_Shop/theonebp_app.py` - Main UI
3. `Core/rate_calculations.py` - Rate lookup
4. `Core/charges_engine.py` - Charges generation

### To understand configuration system:
1. `Core/WF_Matrix.py` - Master entity definitions
2. `Core/accounts_workflows.json` - Account mappings
3. `Core/service_mappings.json` - Service mapping rules
4. `Core/entity_service_mapper.py` - Mapping logic

### To understand entity system:
1. `Core/WF_Matrix.py` - TPUS_PA_SERVICES definition
2. `One_Stop_Shop/gui/entity_manager_gui.py` - Entity CRUD
3. `Core/sync_entities.py` - Entity syncing to master

---

## ⚙️ CONFIGURATION PRIORITY

When setting up a new account/entity:

1. **Define in Core/WF_Matrix.py** (PA_SERVICES for entity)
2. **Add to Core/accounts_workflows.json** (account → workflows → services)
3. **Set rates in rate card** (Core/master_rate_cards.json or Excel)
4. **Add PA template in Core/pa_template_configs.json** (if using ProjectA)
5. **Configure service labels** (One_Stop_Shop/service_label_mapping.json if needed)

---

## 🧭 NAVIGATION: Where to Find What

| What? | Where? |
|-------|--------|
| Want to calculate a quote? | One_Stop_Shop/one_stop_shop_main.py |
| Need to process CEVA documents? | CEVA_Launcher/Launcher.py |
| Create/edit rate cards? | Rate_Card_Builder/rate_card_builder_main.py |
| Add new entity? | One_Stop_Shop → GUI → Entity Manager tab |
| Add new workflow? | One_Stop_Shop → GUI → Workflow Manager tab |
| Change service mapping? | One_Stop_Shop → GUI → Service Mapping tab |
| Understand data flow? | REPOSITORY_ARCHITECTURE.md (in AutomationSuite root) |
| Check configuration structure? | Core/WF_Matrix.py + Core/*.json |
| Need a specific rate? | Core/master_rate_cards.json or CEVA_Launcher/CEVA RATES.xlsx |
| Validate incoming data? | KP_Validator/validator_main.py |
| Share UI components? | Shared_UI/ |

---

## 🔄 HOW COMPONENTS COMMUNICATE

### Via Configuration Files (JSON)
- Core modules read from `accounts_workflows.json`
- One_Stop_Shop reads from `pa_template_configs.json`
- Service mappings via `service_mappings.json`

### Via Python Imports
- All projects import from `Core/` module
- One_Stop_Shop imports from `Rate_Card_Builder/`
- CEVA_Launcher uses `Core/charges_engine_ceva.py`

### Via Shared DataFrames
- CEVA_Launcher: WC_DF, CEVA_DF, PO_DF (in shared_data.py)
- Used by FileCounter, OCR, NoQuote, KickOff

### Via Excel Files
- Rate cards: `CEVA RATES.xlsx`, One_Stop_Shop Excel templates
- Export/Import: ChargesIntegration → Excel worksheets → ProjectA

---

## 🎓 LEARNING PATHS

### Path 1: Understand Quote Calculation (2-3 hours)
1. Read: One_Stop_Shop/README_MAIN_GUI.md
2. Run: One_Stop_Shop/one_stop_shop_main.py
3. Trace: quoteme_email_parser.py → rate_calculations.py → charges_engine.py
4. Review: Core/accounts_workflows.json, Core/pa_template_configs.json

### Path 2: Understand Document Processing (2-3 hours)
1. Read: CEVA_Launcher/README.md
2. Run: CEVA_Launcher/Launcher.py
3. Trace: FileCounter.py → main_orchestrator.py → KickOff.py
4. Study: shared_data.py (DataFrames), ChargesIntegration.py

### Path 3: Understand Configuration System (1-2 hours)
1. Review: Core/WF_Matrix.py
2. Study: Core/*.json files
3. Trace: EntityServiceMapper + ServiceMapper logic
4. Test: One_Stop_Shop Entity Manager UI

### Path 4: Add New Entity to System (1 hour)
1. Add to: Core/WF_Matrix.py (PA_SERVICES)
2. Add to: Core/accounts_workflows.json
3. Add rate card data to: Core/master_rate_cards.json
4. Test in: One_Stop_Shop Entity Manager

