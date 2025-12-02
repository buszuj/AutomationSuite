# One Stop Shop - Build Instructions

## Prerequisites

1. **Install Dependencies**
   ```powershell
   # Install application dependencies
   pip install -r requirements.txt
   
   # Install build dependencies
   pip install -r requirements-build.txt
   ```

2. **Verify Files Present**
   - `One_BP_IQ fixed.01.xlsx`
   - `workflows.json`
   - `service_label_mapping.json`
   - `oss_config.yaml`

## Building the Executable

### Option 1: Using Build Script (Recommended)

```powershell
cd "d:\BP TECH\Python apps\REPOs\AutomationSuite\One_Stop_Shop"
python build_executable.py
```

The script will:
- Clean previous builds
- Check dependencies
- Build the executable
- Copy additional files
- Create a portable package (ZIP)

### Option 2: Manual PyInstaller Command

```powershell
pyinstaller --name OneStopShop --onefile --windowed --clean ^
  --add-data "One_BP_IQ fixed.01.xlsx;." ^
  --add-data "workflows.json;." ^
  --add-data "service_label_mapping.json;." ^
  --add-data "oss_config.yaml;." ^
  --hidden-import customtkinter ^
  --hidden-import ttkthemes ^
  --hidden-import pandas ^
  --hidden-import openpyxl ^
  --hidden-import Core.rate_calculations ^
  --hidden-import Core.workflow_manager ^
  --hidden-import Core.language_pair_manager ^
  --hidden-import Core.service_mapping_manager ^
  --paths "..\Core" ^
  oss_main.py
```

## Output

After successful build, you'll find:

```
dist/
├── OneStopShop.exe                          # Standalone executable
├── OneStopShop_v1.1.0_portable/             # Portable package folder
│   ├── OneStopShop.exe
│   ├── README.md
│   └── TESTING_CHECKLIST.md
└── OneStopShop_v1.1.0_portable.zip          # ZIP archive
```

## Distribution

### For End Users (Simple)
Distribute **only** the `OneStopShop.exe` file:
- All required data files are bundled inside
- No Python installation needed
- Double-click to run

### For End Users (With Documentation)
Distribute the portable package ZIP:
- Includes executable
- Includes README and testing checklist
- Extract and run

## Build Configuration

Edit `build_executable.py` to customize:

```python
APP_NAME = "OneStopShop"           # Executable name
VERSION = "1.1.0"                  # Version number
ICON_FILE = None                   # Path to .ico file (optional)

# Files to include
DATA_FILES = [
    ("One_BP_IQ fixed.01.xlsx", "."),
    ("workflows.json", "."),
    # Add more files here
]
```

## Troubleshooting

### Issue: "PyInstaller not found"
**Solution:** Install build dependencies
```powershell
pip install -r requirements-build.txt
```

### Issue: "Module not found" errors
**Solution:** Add missing module to `HIDDEN_IMPORTS` in `build_executable.py`
```python
HIDDEN_IMPORTS = [
    "customtkinter",
    "your_missing_module",  # Add here
]
```

### Issue: Data files not included
**Solution:** Check file paths in `DATA_FILES` are correct and files exist

### Issue: Executable too large
**Solution:** Use `--onedir` instead of `--onefile` for smaller individual files
- Edit build script: Change `"--onefile"` to `"--onedir"`
- Creates a folder with multiple files instead of single exe

### Issue: Antivirus blocking executable
**Solution:** This is common with PyInstaller executables
- Add exception in antivirus software
- Sign the executable with a code signing certificate (for production)

## Testing the Executable

1. **Locate the executable**
   ```
   dist/OneStopShop.exe
   ```

2. **Run it**
   - Double-click the .exe file
   - Or run from PowerShell: `.\dist\OneStopShop.exe`

3. **Test thoroughly** using `TESTING_CHECKLIST.md`

4. **Verify bundled files**
   - Excel file loads correctly
   - Workflows load
   - Service mappings work
   - Export functionality works

## Advanced Options

### Add Icon
1. Create or obtain a `.ico` file
2. Edit `build_executable.py`:
   ```python
   ICON_FILE = "path/to/icon.ico"
   ```

### Add Version Info (Windows)
1. Create `version_info.txt`:
   ```
   VSVersionInfo(
     ffi=FixedFileInfo(
       filevers=(1, 1, 0, 0),
       prodvers=(1, 1, 0, 0),
       mask=0x3f,
       flags=0x0,
       OS=0x40004,
       fileType=0x1,
       subtype=0x0,
       date=(0, 0)
     ),
     kids=[
       StringFileInfo([
         StringTable(
           u'040904B0',
           [StringStruct(u'CompanyName', u'Your Company'),
            StringStruct(u'FileDescription', u'One Stop Shop Quote Calculator'),
            StringStruct(u'FileVersion', u'1.1.0'),
            StringStruct(u'ProductName', u'One Stop Shop'),
            StringStruct(u'ProductVersion', u'1.1.0')])
       ]),
       VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
     ]
   )
   ```

2. Add to PyInstaller command:
   ```
   --version-file version_info.txt
   ```

### Console Window (Debug Mode)
Remove `--windowed` to show console for debugging:
```python
# In build_executable.py, remove this line:
"--windowed",
```

## Clean Build

To completely clean and rebuild:

```powershell
# Remove all build artifacts
Remove-Item -Recurse -Force build, dist, *.spec, __pycache__

# Rebuild
python build_executable.py
```

## Performance Tips

1. **First run may be slow** - Application unpacks bundled files
2. **Subsequent runs faster** - Files cached
3. **Keep data files small** - Large Excel files increase build size
4. **Test on target machines** - Ensure compatibility

## Deployment Checklist

- [ ] Build executable
- [ ] Test on clean Windows machine
- [ ] Verify all features work
- [ ] Check file size reasonable
- [ ] Test with different rate sheets
- [ ] Verify workflows load/save
- [ ] Test CSV export
- [ ] Package with documentation
- [ ] Create installation instructions
- [ ] Test antivirus compatibility

## Notes

- Executable is **Windows-only** (built on Windows)
- For Mac/Linux, rebuild on respective platforms
- Size typically 50-150 MB depending on dependencies
- No internet connection required to run
- All Python dependencies bundled

## Support

For build issues, check:
1. PyInstaller documentation: https://pyinstaller.org
2. Build script comments
3. PyInstaller spec file (auto-generated)
