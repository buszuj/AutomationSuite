# 🚀 AutomationSuite

A unified multi-project workspace for automation tools with shared core utilities.

## 📁 Structure

```
AutomationSuite/
├── Core/                    # Shared utilities and common functionality
├── CEVA_Launcher/          # Document processing and translation workflow automation (v2.0.2)
├── One_Stop_Shop/          # Multi-scenario automation processor (template)
├── KP_Validator/           # Validation automation tool (template)
└── Shared_UI/              # Reusable UI components
```

## 🎯 Quick Start

### Opening the Workspace

1. Open VS Code
2. File → Open Workspace from File
3. Navigate to `AutomationSuite.code-workspace`

### First-Time Setup

Each project needs its own Python interpreter:
1. Click Python version in bottom-left status bar
2. Select your Python environment
3. Repeat for each project folder in the workspace

### Optional Dependencies

For full Core module functionality:
```powershell
pip install pyyaml
```

## 📦 Projects

### ✅ CEVA_Launcher (Active)
- **Status**: Fully migrated and operational
- **Version**: 2.0.2
- **Entry Point**: `Launcher.py`
- **Files**: 17,427 files migrated
- **Backup**: Available at `../CEVA_Launcher_BACKUP/`

### 📝 One_Stop_Shop (Template)
- **Status**: Template ready for customization
- **Entry Point**: `oss_main.py`
- **Configuration**: `oss_config.yaml`
- **Features**: Scenario-based automation with extensible modules

### 📝 KP_Validator (Template)
- **Status**: Template ready for customization
- **Entry Point**: `validator_main.py`
- **Configuration**: `validator_rules.json`
- **Features**: Rule-based data validation

### 📝 Shared_UI (Template)
- **Status**: Template for UI components
- **Configuration**: `ui_theme.json`
- **Purpose**: Centralized UI theming and components

## 🔧 Core Module

The `Core` module provides shared functionality across all projects:

### Excel Operations
```python
from Core.excel_io import excel_handler

# Read Excel file
df = excel_handler.read_excel('file.xlsx', sheet_name='Sheet1')

# Write Excel file
excel_handler.write_excel(df, 'output.xlsx')
```

### DataFrame Processing
```python
from Core.df_processing import df_processor

# Clean data
clean_df = df_processor.clean_dataframe(df, drop_na=True)

# Filter data
filtered = df_processor.filter_dataframe(df, {'Status': 'Active'})
```

### Validation
```python
from Core.validators import validator

# Validate email
is_valid = validator.validate_email('user@example.com')

# Validate required fields
is_valid, missing = validator.validate_required_fields(
    data_dict, 
    ['field1', 'field2']
)
```

### Utilities
```python
from Core.utils.logger import get_logger
from Core.utils.helpers import load_json, save_json
from Core.utils.file_paths import path_manager

# Logging
logger = get_logger('MyProject')
logger.info('Processing started')

# JSON operations
data = load_json('config.json')
save_json(data, 'output.json')

# Path management
project_path = path_manager.get_project_path('ceva')
```

## 🐛 Debugging

Each project has independent debug configurations:

### CEVA_Launcher
- `F5` to debug Launcher.py
- Separate debug configurations in `.vscode/launch.json`

### One_Stop_Shop / KP_Validator
- `F5` to debug main entry point
- Customizable launch configurations

## 🔨 Building

PyInstaller builds work independently per project:

```powershell
# From CEVA_Launcher directory
pyinstaller CEVA_Launcher.spec

# Each project can have its own build script
```

## 📋 Configuration Files

### Master Configuration
- `Core/configs/master_settings.yaml` - Global settings for all projects

### Project-Specific Configs
- `CEVA_Launcher/` - Uses existing configuration files
- `One_Stop_Shop/oss_config.yaml` - OSS settings
- `KP_Validator/validator_rules.json` - Validation rules
- `Shared_UI/ui_theme.json` - UI theme configuration

### Mapping Files
- `Core/mappings/ceva_mapping.json` - CEVA-specific mappings
- `Core/mappings/oss_mapping.json` - OSS mappings
- `Core/mappings/default_mapping.json` - Default mappings

## 🎨 Adding New Projects

1. Create new folder in `AutomationSuite/`
2. Add project to workspace file:
   ```json
   {
     "name": "MyProject",
     "path": "AutomationSuite/MyProject"
   }
   ```
3. Create `.vscode/` folder with `settings.json` and `launch.json`
4. Add `__init__.py`
5. Import Core modules:
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent))
   
   from Core.excel_io import excel_handler
   ```

## 📊 Benefits

### ✅ Code Reusability
- Shared utilities eliminate duplication
- Centralized configuration management
- Common patterns across projects

### ✅ Independent Development
- Each project debugs independently
- Separate Python interpreters
- Individual version control possible

### ✅ Scalability
- Easy to add new projects
- Template structure provided
- Consistent architecture

### ✅ Maintainability
- Update Core utilities once, benefit everywhere
- Clear separation of concerns
- Organized structure

## 🔄 Migration Info

All CEVA Launcher files have been safely migrated to the new structure.

- **Backup Location**: `../CEVA_Launcher_BACKUP/`
- **Files Preserved**: 100% (17,427 files)
- **Original Files**: Unchanged in original location
- **See Full Report**: `../MIGRATION_REPORT.md`

## 🆘 Troubleshooting

### Import Errors
If you see "Cannot resolve import 'Core'":
1. Open workspace using `.code-workspace` file (not individual folders)
2. Check `.vscode/settings.json` has correct `python.analysis.extraPaths`
3. Reload VS Code window

### Python Interpreter
Each project folder needs its own interpreter selected:
1. Open a file in the project
2. Click Python version in status bar
3. Select your environment

### YAML Import Errors
```powershell
pip install pyyaml
```

## 📝 Version History

- **v1.0.0** (Nov 20, 2025) - Initial AutomationSuite creation
  - Core module established
  - CEVA_Launcher migrated (v2.0.2)
  - Template projects created

## 🤝 Contributing

When adding features to Core:
1. Keep utilities generic and reusable
2. Document with docstrings
3. Add to appropriate __init__.py
4. Test across multiple projects

## 📄 License

Internal use - Your Organization

---

**Ready to automate!** 🎉
