# AutomationSuite - Beginner's Guide

## What Is This Project?

**AutomationSuite** is a collection of tools that help manage translation and document processing workflows. Think of it as a **translation business assistant** that:

1. **Calculates quotes** for translation jobs (how much to charge a customer)
2. **Processes documents** and counts words
3. **Manages rate cards** (pricing tables)
4. **Tracks workflows** (who does what and when)
5. **Automates document import** into project management systems

The system has **four main applications**, each with a specific job.

---

## 🎯 The Four Main Applications

### 1. **One_Stop_Shop** - The Quote Calculator & Admin Center
**Location:** `One_Stop_Shop/one_stop_shop_main.py`

**What it does:**
- You upload a job with customer details
- The app looks up pricing from a rate card
- It calculates charges based on language pair and services
- You can create custom workflows and templates

**Who uses it:** Sales, Operations, Quote specialists

**How to use it:**
1. Run `one_stop_shop_main.py`
2. Select an account (customer)
3. Import job data or enter it manually
4. Choose services needed
5. Get a quote/charge calculation
6. Export to CSV for billing

**Key tabs:**
- **Job Data** - Upload and view job information
- **Rate Cards** - Manage pricing tables
- **Configuration** - Set up accounts, workflows, service mappings
- **PA Template** - Map fields for automated import to ProjectA

---

### 2. **CEVA_Launcher** - The Document Processor
**Location:** `CEVA_Launcher/Launcher.py`

**What it does:**
- Processes exported ZIP files from document systems
- Counts words (with OCR for images)
- Extracts metadata from XLS files
- Merges PO data
- Calculates charges
- Exports to Excel format
- Kicks off automation to import into ProjectA

**Who uses it:** Document processors, operations team

**How to use it:**
1. Run `Launcher.py`
2. Choose mode (Normal, Debug, Manual)
3. Select a ZIP file to process
4. System automatically:
   - Extracts files
   - Counts words
   - Gets metadata
   - Calculates charges
   - Exports final Excel

**Key components:**
- **FileCounter** - Word counting engine
- **ChargesIntegration** - Calculates fees and costs
- **KickOff** - Automation trigger to ProjectA

---

### 3. **Rate_Card_Builder** - The Pricing Tool
**Location:** `Rate_Card_Builder/rate_card_builder_main.py`

**What it does:**
- Create and edit rate cards (pricing tables)
- Define prices per language pair and service
- Support two pricing types: **Itemized** (flat rates) and **Tiered** (volume discounts)
- Export to JSON or CSV
- Import from Excel

**Who uses it:** Account managers, pricing specialists

**How to use it:**
1. Run `rate_card_builder_main.py`
2. Create a new rate card or edit existing
3. Add services and prices
4. Set currency and effective dates
5. Export for use in One_Stop_Shop or CEVA_Launcher

---

### 4. **KP_Validator** - The Data Checker
**Location:** `KP_Validator/validator_main.py`

**What it does:**
- Validates incoming data against rules
- Ensures data meets requirements
- Prevents bad data from entering the system

**Who uses it:** Data quality team

---

## 📁 Folder Structure & Key Files

### **Core/** - The Engine Room 🔧
This folder contains all the **shared logic** that powers the other applications.

**Key files:**

| File | What It Does |
|------|-------------|
| `WF_Matrix.py` | Master list of all entities and their services (like a phone book) |
| `account_workflow_manager.py` | Manages workflows for each customer account |
| `service_mapper.py` | Converts service names between different systems |
| `entity_service_mapper.py` | Maps services from customer systems to master services |
| `pa_template_manager.py` | Templates for auto-importing to ProjectA |
| `quoteme_value_mapper.py` | Connects QuoteMe fields to service types |
| `language_normalizer.py` | Standardizes language names (e.g., "Polish" = "pl-PL") |
| `charges_engine.py` | Calculates fees, rates, and totals |
| `df_processing.py` | Data manipulation utilities |
| `excel_io.py` | Reading/writing Excel files |

**Config files (JSON):**

| File | What It Stores |
|------|--------|
| `accounts_workflows.json` | All customer workflows and their services |
| `entity_services.json` | Services available for each entity |
| `canonical_services.json` | Master list of all possible services |
| `service_mappings.json` | How customer services map to master services |
| `master_rate_cards.json` | Saved rate cards |
| `language_mapping.json` | Language name translations |
| `languages_iso_codes.json` | Language codes (like "en-US", "de-DE") |
| `column_preferences.json` | UI preferences (which columns to show) |

---

## 🔄 How Data Flows Through the System

### **Scenario 1: Quote Calculation in One_Stop_Shop**

```
Customer calls
    ↓
Operator enters job details in One_Stop_Shop
    ↓
System loads rate card (prices)
    ↓
System looks up service in entity mapper
    ↓
System normalizes language names
    ↓
System calculates charges (word count × rate)
    ↓
Quote is shown on screen
    ↓
Operator exports to CSV
```

### **Scenario 2: Document Processing in CEVA_Launcher**

```
ZIP file from document system
    ↓
FileCounter extracts files and counts words (+ OCR for images)
    ↓
NoQuote reads XLS metadata
    ↓
System merges word counts + metadata
    ↓
ChargesIntegration calculates fees
    ↓
KickOff automates ProjectA import
    ↓
Final Excel exported to shared folder
```

### **Scenario 3: Service Name Translation**

```
Customer's rate card has: "German Translation"
    ↓
Service Mapper checks canonical_services.json
    ↓
Matches to: "Translation"
    ↓
System looks up price for "Translation"
    ↓
Quote calculated correctly
```

---

## 👤 Account & Workflow Concepts

### **What is an Account?**
A customer or project. Examples: "ICON", "Janssen", "PXL"

Each account has:
- A set of services they provide
- Workflows (combinations of services)
- Rate cards (pricing)
- Fee defaults (minimums, rush charges)

### **What is a Workflow?**
A **combination of services** that work together for a specific job type.

Example workflow: "Legal Document Translation"
- Service 1: Translation (1000 words)
- Service 2: Proofreading (1000 words)
- Service 3: Formatting (5 hours)

---

## 🗂️ Config Hierarchy (What Overrides What?)

```
1. WF_Matrix.py (Master - defines all entities and services)
   ↓
2. entity_services.json (What services each entity has)
   ↓
3. service_mappings.json (How to map customer service names to master names)
   ↓
4. canonical_services.json (Approved service list)
   ↓
5. Account-specific configs (account folder in Core/accounts/)
   ├── quoteme_mappings.json (How to extract data from emails)
   ├── fee_service_defaults.json (Minimum charges per service)
   └── service_mappings/{rate_card}.json (Custom mappings per rate card)
```

---

## 🚀 Quick Start for Different Roles

### **I'm a Sales Person**
1. Open **One_Stop_Shop** (`launch_main.py`)
2. Select account
3. Upload customer job data
4. Select workflow
5. Get quote in Charges tab
6. Export to CSV

### **I'm an Operations Manager**
1. Use **One_Stop_Shop** to manage accounts
2. Configure Workflows tab
3. Create/edit rate cards in **Rate_Card_Builder**
4. Monitor CEVA_Launcher processing

### **I'm a Developer**
1. All logic is in **Core/** - add features here
2. UI is in **One_Stop_Shop/** and **CEVA_Launcher/**
3. Configuration is JSON files
4. Run tests with test files in root directory

### **I'm a Data Quality Person**
1. Use **KP_Validator** to check data
2. Verify language mappings work correctly
3. Test rate card calculations

---

## 📊 Key Concepts Explained

### **Entity**
A business or service provider. TPUS is the **master entity** (source of truth).

### **Service**
A type of work: Translation, Proofreading, Formatting, Rush Fee, etc.

### **Rate Card**
A pricing table. Example:
```
Language Pair: English > Spanish
Translation: $0.15 per word
Proofreading: $0.05 per word
```

### **Language Pair**
Source + Target languages. Example: "English (US) > German (Germany)"

### **UofM (Unit of Measure)**
How you charge for a service:
- **Word** - per word ($0.15 per word)
- **Hour** - per hour ($75 per hour)
- **Fee** - flat rate ($500 project fee)

### **QuoteMe Data**
Email parsing system that extracts:
- Word counts (New Words, 100% Matches, Fuzzy Matches, etc.)
- Language pairs
- Metadata

---

## 🔌 How Components Connect

```
┌─────────────────────────────────────────────────────────┐
│                    ONE_STOP_SHOP                        │
│  (Quote calculator & configuration hub)                 │
└────────────┬────────────────────────────┬───────────────┘
             │                            │
         needs                        needs
             │                            │
    ┌────────▼──────────┐    ┌────────────▼──────────┐
    │   CORE (Engine)   │    │ RATE_CARD_BUILDER    │
    │                   │    │ (Pricing editor)     │
    │ - Mapping logic   │    └──────────────────────┘
    │ - Calculations    │
    │ - JSON configs    │
    └────────┬──────────┘
             │
         feeds
             │
    ┌────────▼──────────┐    ┌──────────────────────┐
    │ CEVA_LAUNCHER    │    │  KP_VALIDATOR        │
    │ (Document proc)  │    │  (Data checker)      │
    └───────────────────┘    └──────────────────────┘
```

---

## 📝 Where to Find Things

### **To add a new service:**
1. Edit `Core/WF_Matrix.py` (add to TPUS_PA_SERVICES)
2. Update `Core/canonical_services.json`
3. Use Entity Manager in One_Stop_Shop to add to other entities

### **To create a workflow:**
1. Open One_Stop_Shop
2. Go to Configuration > Manage Workflows
3. Click "Add New"
4. Select services

### **To change pricing:**
1. Open Rate_Card_Builder
2. Edit or create a rate card
3. Export to JSON
4. Use in One_Stop_Shop

### **To add a customer:**
1. Open One_Stop_Shop Configuration tab
2. Select account
3. Add to accounts_workflows.json

---

## 🎓 Understanding the Code Structure

### **Python Module Naming Pattern**
- `*_manager.py` - Manages a resource (workflows, rate cards, etc.)
- `*_processor.py` - Processes data (templates, parsing)
- `*_engine.py` - Core calculation logic
- `*_mapper.py` - Converts between formats
- `*_io.py` - Input/Output (reading/writing files)

### **JSON File Pattern**
- Top-level keys = categories or record types
- `"account"` or `"entity"` field = who it belongs to
- Nested structure = relationships between data

---

## 🔍 Common Questions

**Q: Where do I change prices?**
A: In `Rate_Card_Builder` or directly edit JSON rate cards

**Q: How does the system know what a service costs?**
A: Rate card lookup → service name → language pair → price

**Q: What happens if a service isn't in the rate card?**
A: System looks for it in service_mappings, then uses canonical name

**Q: Can I have different prices for different customers?**
A: Yes! Each rate card can be assigned to different accounts

**Q: How do I add a new language?**
A: Edit `languages_iso_codes.json` or use language_normalizer mappings

---

## 📚 File Types You'll See

- **`.py`** - Python code (logic)
- **`.json`** - Configuration & data storage
- **`.xlsx`** - Excel files (input/output)
- **`.csv`** - CSV files (export data)
- **`.md`** - Markdown documentation
- **`.bat`** - Batch files (Windows scripts)

---

## ✅ Next Steps

1. **Read `One_Stop_Shop/README.md`** for detailed UI guide
2. **Read `CEVA_Launcher/` documentation** for document processing
3. **Explore `Core/` files** - read docstrings in Python files
4. **Check test files** (`test_*.py`) for usage examples
5. **Review JSON configs** to understand data structure

---

**Created:** 2026-06-10  
**For:** AutomationSuite v1.1.0 + CEVA_Launcher v2.0.2  
**Questions?** See README.md files in each folder for component-specific details.
