# Entity Manager GUI

A GUI tool for managing PA Service entities in the AutomationSuite Core.

## Features

- **Create New Entities**: Create new PA service entity lists (e.g., TPIT, TPFR, TPUK)
- **Copy Services**: Optionally copy services from existing entities
- **View Entities**: See all existing entities and their service counts
- **Auto-formatting**: Automatically formats entity names and updates WF_Matrix.py

## Usage

### Standalone Launch

```bash
python launch_entity_manager.py
```

Or directly:

```bash
python gui/entity_manager_gui.py
```

### Integration with Main App

To integrate into the One_Stop_Shop main application:

```python
from gui.entity_manager_gui import open_entity_manager

# In your main app, add a button or menu item:
entity_btn = ctk.CTkButton(
    parent_frame,
    text="Manage Entities",
    command=lambda: open_entity_manager(self.window)
)
```

## How It Works

### Creating a New Entity

1. Enter the entity name (e.g., "TPIT")
2. Optionally select an existing entity to copy services from
3. Click "Create Entity"

The tool will:
- Validate the entity name (alphanumeric only)
- Convert to uppercase (TPIT)
- Create a new list variable: `TPIT_PA_SERVICES`
- Add it to the `PA_SERVICES` dictionary in `Core/WF_Matrix.py`
- If copying, duplicate all services from the selected entity
- If not copying, create with just the header row

### Entity Naming Convention

- Entity names are automatically uppercased
- Format: `{ENTITYNAME}_PA_SERVICES`
- Example: "tpit" becomes "TPIT_PA_SERVICES"

### File Structure

The created entity is added to `Core/WF_Matrix.py` in this format:

```python
# List of TPIT PA Services
TPIT_PA_SERVICES = [
    ["Service Group 1", "Service Group 2", "Service", "Default UofM"],
    # Additional services if copied from another entity
]

# Dictionary mapping entity names to their service lists
PA_SERVICES = {
    "TPUS": TPUS_PA_SERVICES,
    "TPTDE": TPTDE_PA_SERVICES,
    "TPIT": TPIT_PA_SERVICES,  # <- New entity added here
}
```

## GUI Components

### Left Panel - Entity Creation
- **Entity Name Input**: Enter the new entity name
- **Copy From Dropdown**: Select an existing entity to copy services from
- **Create Button**: Creates the entity
- **Status Display**: Shows success/error messages

### Right Panel - Entity List
- **Refresh Button**: Reload entity list from WF_Matrix.py
- **Entity Cards**: Display all existing entities with service counts

## Requirements

- customtkinter
- Python 3.7+
- Access to Core/WF_Matrix.py

## Error Handling

The tool validates:
- ✓ Entity name not empty
- ✓ Entity name contains only letters and numbers
- ✓ Entity name doesn't already exist
- ✓ WF_Matrix.py file is accessible

## Future Enhancements

Potential additions:
- Delete entity functionality
- Edit entity services directly
- Export/import entity configurations
- Rename entity
- Merge entities
- Service-level management within entities

## Support

For issues or questions, refer to the main AutomationSuite documentation.
