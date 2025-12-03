# Entity Manager GUI - Setup Complete! ✓

## What Was Created

### 1. Main GUI Component
**File**: `One_Stop_Shop/gui/entity_manager_gui.py`
- Complete GUI application for managing PA Service entities
- Built with CustomTkinter for modern UI
- Features:
  - Create new entities
  - Copy services from existing entities
  - View all entities with service counts
  - Real-time validation
  - Auto-refresh capability

### 2. Launcher Script
**File**: `One_Stop_Shop/launch_entity_manager.py`
- Quick launcher for standalone use
- Simple command: `python launch_entity_manager.py`

### 3. Integration Example
**File**: `One_Stop_Shop/entity_manager_integration.py`
- Shows how to integrate into main One_Stop_Shop app
- Template for adding menu items

### 4. Documentation
**File**: `One_Stop_Shop/gui/ENTITY_MANAGER_README.md`
- Complete usage guide
- Feature documentation
- Integration instructions

### 5. Test Script
**File**: `One_Stop_Shop/test_entity_manager.py`
- Validates all imports and dependencies
- Quick health check

## How to Use

### Launch the Entity Manager

```bash
cd "d:\BP TECH\Python apps\REPOs\AutomationSuite\One_Stop_Shop"
python launch_entity_manager.py
```

### Create a New Entity

1. **Enter Entity Name**: Type "TPIT" (will be auto-uppercased)
2. **Optional - Copy Services**: Select "TPUS" or "TPTDE" to copy their services
3. **Click "Create Entity"**

### Result

The tool will:
- Create `TPIT_PA_SERVICES` variable in `Core/WF_Matrix.py`
- Add it to the `PA_SERVICES` dictionary
- If copying: Duplicate all services from selected entity
- If not copying: Create with header row only

### Example Output in WF_Matrix.py

```python
# List of TPIT PA Services
TPIT_PA_SERVICES = [
    ["Service Group 1", "Service Group 2", "Service", "Default UofM"],
    # Services here if copied from another entity
]

# Dictionary mapping entity names to their service lists
PA_SERVICES = {
    "TPUS": TPUS_PA_SERVICES,
    "TPTDE": TPTDE_PA_SERVICES,
    "TPIT": TPIT_PA_SERVICES,  # <- Newly created
}
```

## GUI Layout

```
┌─────────────────────────────────────────────────┐
│      PA Services Entity Manager                 │
├──────────────────┬──────────────────────────────┤
│ Create New       │  Existing Entities           │
│ Entity           │                              │
│                  │  ┌────────────────────┐      │
│ Entity Name:     │  │ 🔄 Refresh List    │      │
│ [TPIT____]       │  └────────────────────┘      │
│                  │                              │
│ Copy From:       │  ┌─────────────────────┐    │
│ [TPUS ▼]        │  │ TPUS                │    │
│                  │  │ 16 services         │    │
│ [Create Entity]  │  └─────────────────────┘    │
│                  │  ┌─────────────────────┐    │
│ ✓ Success!       │  │ TPTDE               │    │
│                  │  │ 1 service           │    │
│                  │  └─────────────────────┘    │
└──────────────────┴──────────────────────────────┘
```

## Features

✓ **User Input Validation**
  - Empty name check
  - Alphanumeric only
  - Duplicate detection
  
✓ **Service Copying**
  - Clone entire service lists
  - Or start fresh with header only
  
✓ **Auto-formatting**
  - Uppercase conversion
  - Naming convention enforcement
  
✓ **Live Updates**
  - Refresh entity list
  - Real-time status messages
  
✓ **Error Handling**
  - Clear error messages
  - Validation feedback

## Integration with One_Stop_Shop Main App

To add a menu button in the main app:

```python
# In theonebp_app.py or wherever you have your main menu

from gui.entity_manager_gui import open_entity_manager

# Add this button
entity_manager_btn = ctk.CTkButton(
    menu_frame,
    text="⚙️ Manage Entities",
    command=lambda: open_entity_manager(self.window),
    width=200,
    height=40
)
entity_manager_btn.pack(pady=5)
```

## Technical Details

**Dependencies**:
- customtkinter >= 5.2.0 ✓ (already installed)
- Python 3.7+
- Core/WF_Matrix.py

**File Operations**:
- Reads `Core/WF_Matrix.py`
- Parses existing entities
- Inserts new entity code
- Updates PA_SERVICES dictionary
- Writes back to file

**Safety**:
- Validates before writing
- Checks file accessibility
- Error handling for all operations

## Next Steps

You can now:
1. Launch the GUI and create entities
2. Test with "TPIT", "TPFR", "TPUK", etc.
3. Integrate into main One_Stop_Shop menu
4. Add to CEVA_Launcher if needed

## Future Enhancements (Optional)

- Delete entity functionality
- Edit services within entities
- Export/import entity configurations
- Bulk entity creation
- Entity templates

---

**Status**: ✅ COMPLETE AND TESTED
**Created**: December 3, 2025
**Location**: `AutomationSuite/One_Stop_Shop/gui/`
