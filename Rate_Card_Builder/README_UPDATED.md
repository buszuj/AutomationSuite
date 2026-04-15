# Rate Card Builder

A standalone GUI application for creating and managing rate cards in the Automation Suite.

## Overview

Rate Card Builder is a comprehensive tool for creating, editing, and managing linguistic rate cards. It supports multiple pricing models (Itemized and Tiered) with automatic ISO language code mapping for 197+ languages.

## Features

- **Modern UI**: Built with customtkinter for a sleek, modern interface
- **Embedded Editor**: Itemized rate card editor embedded directly in main window (default view)
- **Multiple Rate Card Types**: Itemized and Tiered pricing models
- **Automatic Language Mapping**: 197+ language/ISO code mappings
- **Data Validation**: Float validation for all rate entries with error messaging
- **Error Highlighting**: Visual indicators for languages not found in ISO database
- **File Management**: Load, edit, and delete existing rate cards
- **Flexible Input**: Parse languages with `,` or `;` delimiters
- **Extensible**: Modular design ready for integration into One Stop Shop

## Application Structure

### Main Window (Fullscreen, Tabbed)

**Tab 1: Itemized Rate Card** ⭐ **DEFAULT - EMBEDDED**
- Create itemized rate cards with language-based pricing
- Excel-like viewing pane for rate entry
  - Column A: Language Names (locked)
  - Column B: ISO Codes (editable for missing languages)
  - Columns C-G: Service rates (editable floats)
- Automatic ISO code mapping for known languages
- Error highlighting for missing languages
- Double-click cells to edit rates
- Sponsor field for rate card ownership

**Tab 2: Tiered Rate Card** (Separate Window)
- Create tiered rate cards with volume/tier-based pricing
- 4 default tiers: 0-10k, 10k-50k, 50k-100k, 100k+
- 20 rate columns per language (4 tiers × 5 services)
- Same language management as itemized
- Opens in a dedicated window

**Tab 3: Load Rate Card** (Separate Window)
- Browse and load existing rate cards
- View rate card metadata (name, sponsor, type, languages)
- JSON editor for direct editing
- Save changes to existing rate cards
- Delete rate cards with confirmation
- Recent files list sorted by modification date

**Tab 4: Settings**
- Application configuration options (expandable for future features)

## Project Structure

```
Rate_Card_Builder/
├── rate_card_builder_main.py              # Main application with tabbed interface
├── itemized_rate_card_editor.py           # ✓ NEW: Embedded itemized editor
├── itemized_rate_card_window.py           # Legacy: Itemized editor (window version)
├── tiered_rate_card_window.py             # Tiered editor window
├── load_rate_card_window.py               # Load rate card window
├── language_loader.py                     # Language management utilities
├── languages_iso_codes.json               # 197 language/ISO code mappings
├── test_application.py                    # Comprehensive test suite
├── requirements.txt                       # Python dependencies
├── README.md                              # This file
├── __init__.py                            # Package initialization
└── rate_cards_*.json                      # Sample rate cards (test data)
```

## Requirements

- Python 3.8+
- customtkinter ≥ 5.0.0
- tkinter (included with Python)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python rate_card_builder_main.py
```

The application will launch in fullscreen with the **Itemized Rate Card editor as the default view**.

## Usage Guide

### Creating an Itemized Rate Card

1. **Application launches** → Itemized Rate Card editor is displayed by default
2. **Enter Details**:
   - Rate Card Name: A unique identifier for your rate card
   - Sponsor: Organization sponsoring the rate card
3. **Import Languages**: 
   - Paste languages in the text area (separated by `,` or `;`)
   - Click "Import Languages"
   - The system will automatically map ISO codes from the language database
4. **Edit Rates**:
   - Double-click any rate cell to edit
   - Enter float values (e.g., 0.15, 15, 0.5)
   - System validates input as you type
5. **Handle Missing Languages** (if any):
   - Missing languages are highlighted in red
   - Error message lists which languages weren't found
   - Double-click the ISO CODE column to manually enter codes
   - Or correct the language names
6. **Save**:
   - Click "Save Rate Card"
   - File is saved as `rate_cards_<name>.json` in the module directory

### Default Services

All rate cards include these service categories:
- Translation
- TM - Fuzzy Match Low
- TM - Fuzzy Match Medium
- TM - Fuzzy Match High
- TM - Exact Match

### Creating a Tiered Rate Card

1. Navigate to the **Tiered Rate Card** tab
2. Click "Create Tiered Rate Card"
3. Follow same steps as Itemized, plus:
   - Define pricing for each tier level (0-10k, 10k-50k, 50k-100k, 100k+)
   - Each service has a rate for each tier

### Loading Existing Rate Cards

1. Navigate to the **Load Rate Card** tab
2. Click "Load Rate Card" or "Browse Rate Cards"
3. Select a file from your system or recent files list
4. View rate card metadata
5. Click "Open Selected" to edit the rate card
6. Edit JSON directly or use delete button to remove

## Data Format

Rate cards are stored as JSON with this structure:

### Itemized Rate Card
```json
{
  "name": "My Rate Card",
  "sponsor": "ABC Translation Services",
  "type": "itemized",
  "services": [
    "Translation",
    "TM - Fuzzy Match Low",
    "TM - Fuzzy Match Medium",
    "TM - Fuzzy Match High",
    "TM - Exact Match"
  ],
  "languages": {
    "English": {
      "iso_code": "en",
      "rates": {
        "Translation": "0.15",
        "TM - Fuzzy Match Low": "0.12",
        "TM - Fuzzy Match Medium": "0.10",
        "TM - Fuzzy Match High": "0.08",
        "TM - Exact Match": "0.05"
      }
    },
    "Spanish": {
      "iso_code": "es",
      "rates": {
        "Translation": "0.18",
        ...
      }
    }
  }
}
```

### Tiered Rate Card
```json
{
  "name": "My Tiered Rate Card",
  "sponsor": "XYZ Translations",
  "type": "tiered",
  "tiers": ["0-10k", "10k-50k", "50k-100k", "100k+"],
  "services": [...same as above...],
  "languages": {
    "English": {
      "iso_code": "en",
      "rates": {
        "0-10k_Translation": "0.15",
        "0-10k_TM - Fuzzy Match Low": "0.12",
        "10k-50k_Translation": "0.14",
        ...
      }
    }
  }
}
```

## Key Features in Detail

### Language Management
- **Automatic Mapping**: Paste language names and automatically map to ISO codes
- **197+ Languages**: Support for 197 unique language/country combinations
- **Error Handling**: Visual indication of missing language mappings
- **Manual Override**: Edit language names and ISO codes directly in table

### Data Validation
- **Float Validation**: Rate cells accept decimal values (0.15, 15, 0.5, etc.)
- **Error Messages**: Clear feedback for invalid entries
- **Empty Cells Allowed**: Optional rate entries for flexibility

### File Management
- **Save Format**: JSON for easy integration and version control
- **Load Existing**: Browse and open any saved rate card
- **Edit Directly**: JSON editor for advanced customization
- **Delete Safety**: Confirmation before deletion

## Testing

Run the comprehensive test suite:

```bash
python test_application.py
```

**Test Coverage:**
- ✅ File structure integrity (9 files)
- ✅ Language manager functionality (197 languages)
- ✅ Float validation (7 test cases)
- ✅ Language parsing (comma and semicolon delimiters)
- ✅ Sample rate card files (2 examples)

**Test Output:**
- Validates all system components
- Loads and tests all 197 languages
- Confirms JSON structure and data integrity
- Ready for production use

## Development Roadmap

### Phase 1: ✅ Completed
- [x] Main window with tabbed interface
- [x] Embedded Itemized Rate Card editor (default view)
- [x] Tiered Rate Card editor window
- [x] Load/Edit/Delete functionality
- [x] Language management with ISO codes
- [x] Float validation with error handling
- [x] Error highlighting for missing languages
- [x] JSON persistence
- [x] Comprehensive testing suite
- [x] UI improvements and refinements

### Phase 2: Planned - Integration
- [ ] Integration with One Stop Shop
- [ ] Database backend for rate cards
- [ ] User authentication and roles
- [ ] Rate card versioning and history
- [ ] Approval workflow

### Phase 3: Planned - Enhancement
- [ ] Export to Excel format
- [ ] CSV import/export
- [ ] Rate card templates
- [ ] Bulk operations
- [ ] Advanced search and filter
- [ ] Rate card comparison tools

## Troubleshooting

### Languages not mapping correctly
- Check spelling against the ISO code database
- Some languages may be listed as "Language (Country)"
- Try searching in the Load window to see available options

### Float values rejected
- Ensure you enter valid numbers (0.15, 15, 0.5)
- No special characters or text in rate cells
- Empty cells are allowed

### Rate card won't save
- Verify the Rate Card Name is not empty
- Ensure languages have been imported
- Check file system permissions in the module directory

## Contact & Support

This module is part of the Automation Suite. For integration or enhancement requests, contact the development team.

## License

Part of the Automation Suite - Internal Use
