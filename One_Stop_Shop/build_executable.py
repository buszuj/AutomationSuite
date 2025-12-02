"""
One Stop Shop - Build Script
Compiles the application into a standalone executable using PyInstaller.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Script configuration
APP_NAME = "OneStopShop"
MAIN_SCRIPT = "oss_main.py"
ICON_FILE = None  # Set to icon path if available, e.g., "icon.ico"
VERSION = "1.1.0"

# Paths
SCRIPT_DIR = Path(__file__).parent
BUILD_DIR = SCRIPT_DIR / "build"
DIST_DIR = SCRIPT_DIR / "dist"
SPEC_FILE = SCRIPT_DIR / f"{APP_NAME}.spec"

# Files and folders to include with the executable
DATA_FILES = [
    ("One_BP_IQ fixed.01.xlsx", "."),
    ("workflows.json", "."),
    ("service_label_mapping.json", "."),
    ("oss_config.yaml", "."),
]

# Folders to include
DATA_FOLDERS = []

# Hidden imports (modules not automatically detected)
HIDDEN_IMPORTS = [
    "customtkinter",
    "ttkthemes",
    "pandas",
    "openpyxl",
    "tkinter",
    "tkinter.ttk",
]


def clean_previous_builds():
    """Remove previous build artifacts."""
    print("🧹 Cleaning previous builds...")
    
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print(f"   Removed: {BUILD_DIR}")
    
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
        print(f"   Removed: {DIST_DIR}")
    
    if SPEC_FILE.exists():
        SPEC_FILE.unlink()
        print(f"   Removed: {SPEC_FILE}")
    
    # Remove pycache
    for pycache in SCRIPT_DIR.rglob("__pycache__"):
        shutil.rmtree(pycache)
    
    print("✅ Cleanup complete\n")


def check_dependencies():
    """Check if PyInstaller is installed."""
    print("🔍 Checking dependencies...")
    
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} found\n")
        return True
    except ImportError:
        print("❌ PyInstaller not found!")
        print("   Install it with: pip install pyinstaller")
        return False


def build_pyinstaller_command():
    """Build the PyInstaller command with all options."""
    cmd = [
        "pyinstaller",
        "--name", APP_NAME,
        "--onefile",  # Single executable
        "--windowed",  # No console window (GUI app)
        "--clean",
    ]
    
    # Add icon if available
    if ICON_FILE and Path(ICON_FILE).exists():
        cmd.extend(["--icon", ICON_FILE])
    
    # Add data files
    for src, dest in DATA_FILES:
        if Path(src).exists():
            cmd.extend(["--add-data", f"{src};{dest}"])
        else:
            print(f"⚠️  Warning: Data file not found: {src}")
    
    # Add data folders
    for src, dest in DATA_FOLDERS:
        if Path(src).exists():
            cmd.extend(["--add-data", f"{src};{dest}"])
        else:
            print(f"⚠️  Warning: Data folder not found: {src}")
    
    # Add hidden imports
    for module in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", module])
    
    # Add Core modules explicitly
    cmd.extend([
        "--hidden-import", "Core.rate_calculations",
        "--hidden-import", "Core.workflow_manager",
        "--hidden-import", "Core.language_pair_manager",
        "--hidden-import", "Core.service_mapping_manager",
    ])
    
    # Add paths
    core_path = SCRIPT_DIR.parent / "Core"
    if core_path.exists():
        cmd.extend(["--paths", str(core_path)])
    
    # Main script
    cmd.append(MAIN_SCRIPT)
    
    return cmd


def build_executable():
    """Build the executable using PyInstaller."""
    print("🔨 Building executable...")
    print(f"   Application: {APP_NAME}")
    print(f"   Version: {VERSION}")
    print(f"   Main script: {MAIN_SCRIPT}\n")
    
    cmd = build_pyinstaller_command()
    
    # Print command for reference
    print("📝 PyInstaller command:")
    print("   " + " ".join(cmd) + "\n")
    
    # Run PyInstaller
    try:
        result = subprocess.run(cmd, check=True, cwd=SCRIPT_DIR)
        print("\n✅ Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed with error code {e.returncode}")
        return False


def copy_additional_files():
    """Copy additional files to the dist folder."""
    print("\n📦 Copying additional files to dist...")
    
    if not DIST_DIR.exists():
        print("❌ Dist directory not found")
        return
    
    # Files that should be easily accessible alongside the exe
    additional_files = [
        "README.md",
        "TESTING_CHECKLIST.md",
    ]
    
    for filename in additional_files:
        src = SCRIPT_DIR / filename
        if src.exists():
            dst = DIST_DIR / filename
            shutil.copy2(src, dst)
            print(f"   Copied: {filename}")
    
    print("✅ Additional files copied")


def create_portable_package():
    """Create a portable package with all necessary files."""
    print("\n📂 Creating portable package...")
    
    package_name = f"{APP_NAME}_v{VERSION}_portable"
    package_dir = DIST_DIR / package_name
    
    if package_dir.exists():
        shutil.rmtree(package_dir)
    
    package_dir.mkdir(parents=True)
    
    # Copy executable
    exe_file = DIST_DIR / f"{APP_NAME}.exe"
    if exe_file.exists():
        shutil.copy2(exe_file, package_dir)
        print(f"   Copied: {APP_NAME}.exe")
    
    # Copy data files that aren't bundled
    for readme_file in ["README.md", "TESTING_CHECKLIST.md"]:
        src = SCRIPT_DIR / readme_file
        if src.exists():
            shutil.copy2(src, package_dir)
            print(f"   Copied: {readme_file}")
    
    print(f"✅ Portable package created: {package_dir.name}")
    
    # Create zip archive
    try:
        archive_path = shutil.make_archive(
            str(DIST_DIR / package_name),
            'zip',
            package_dir
        )
        print(f"✅ Archive created: {Path(archive_path).name}")
    except Exception as e:
        print(f"⚠️  Failed to create archive: {e}")


def print_summary():
    """Print build summary."""
    print("\n" + "="*60)
    print("🎉 BUILD SUMMARY")
    print("="*60)
    
    exe_file = DIST_DIR / f"{APP_NAME}.exe"
    if exe_file.exists():
        size_mb = exe_file.stat().st_size / (1024 * 1024)
        print(f"\n✅ Executable created successfully!")
        print(f"   Location: {exe_file}")
        print(f"   Size: {size_mb:.2f} MB")
    else:
        print("\n❌ Executable not found!")
    
    print(f"\n📁 Output directory: {DIST_DIR}")
    print(f"📋 Build logs: {BUILD_DIR}")
    
    print("\n" + "="*60)


def main():
    """Main build process."""
    print("\n" + "="*60)
    print(f"🚀 ONE STOP SHOP - BUILD SCRIPT v{VERSION}")
    print("="*60 + "\n")
    
    # Change to script directory
    os.chdir(SCRIPT_DIR)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Clean previous builds
    clean_previous_builds()
    
    # Build executable
    if not build_executable():
        sys.exit(1)
    
    # Copy additional files
    copy_additional_files()
    
    # Create portable package
    create_portable_package()
    
    # Print summary
    print_summary()
    
    print("\n✅ Build process complete!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
