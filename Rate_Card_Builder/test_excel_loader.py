"""
Test script for Excel Rate Card Loader
Run this to verify the Excel rate card loader works correctly.
"""

import sys
from pathlib import Path

# Add Rate_Card_Builder to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Test imports
    print("Testing imports...")
    from excel_rate_card_loader import load_excel_rate_card, find_excel_rate_cards
    print("✓ Successfully imported excel_rate_card_loader")
    
    # Find available Excel rate cards
    print("\nSearching for Excel rate cards...")
    files = find_excel_rate_cards()
    print(f"✓ Found {len(files)} Excel rate card files:")
    for filename, filepath in files:
        print(f"  - {filename}")
    
    # Load first rate card
    if files:
        print("\n" + "="*60)
        filename, filepath = files[0]
        print(f"Loading: {filename}")
        print("="*60)
        
        rate_card = load_excel_rate_card(filepath)
        
        print(f"\nRate Card Loaded Successfully!")
        print(f"  Name: {rate_card.get('name')}")
        print(f"  Sponsor: {rate_card.get('sponsor')}")
        print(f"  Type: {rate_card.get('type')}")
        print(f"  Source: {rate_card.get('source')}")
        print(f"  Languages: {len(rate_card.get('languages', {}))}")
        print(f"  Services: {len(rate_card.get('services', []))}")
        
        # Show sample data
        print(f"\n  Sample Languages (first 5):")
        for i, (lang_name, lang_data) in enumerate(list(rate_card.get('languages', {}).items())[:5], 1):
            rates_count = len(lang_data.get('rates', {}))
            print(f"    {i}. {lang_name} (ISO: {lang_data.get('iso_code')}, Rates: {rates_count})")
        
        print(f"\n  Available Services (first 8):")
        for i, service in enumerate(rate_card.get('services', [])[:8], 1):
            print(f"    {i}. {service}")
        
        print("\n" + "="*60)
        print("✓ Excel rate card loader is working correctly!")
        print("="*60)
    else:
        print("\n⚠ No Excel rate cards found at:")
        print("  d:/BP TECH/Python apps/REPOs/TheOneBP/RateCards/")
        print("  Please verify the directory exists and contains .xlsx files")

except ImportError as e:
    print(f"✗ Import Error: {e}")
    print("\nRequired dependencies:")
    print("  - pandas")
    print("  - openpyxl")
    print("\nInstall with: pip install pandas openpyxl")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
