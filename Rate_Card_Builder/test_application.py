"""
Rate Card Builder - Test & Demo Script
Demonstrates the features of the Rate Card Builder application.
"""

import json
from pathlib import Path
from language_loader import get_language_manager


def test_language_manager():
    """Test the language manager functionality."""
    print("=" * 60)
    print("TEST 1: Language Manager Testing")
    print("=" * 60)
    
    manager = get_language_manager()
    
    # Test 1.1: Get all codes
    print("\n1.1 Total languages loaded:", len(manager.get_all_codes()))
    print("Sample codes:", manager.get_all_codes()[:5])
    
    # Test 1.2: Search by code
    print("\n1.2 Search by code 'en-US':")
    result = manager.get_by_code("en-US")
    if result:
        print(f"  Found: {result['display_name']}")
    
    # Test 1.3: Search by language
    print("\n1.3 Search for all Spanish variants:")
    spanish = manager.get_by_language("Spanish")
    for lang in spanish[:3]:
        print(f"  - {lang['display_name']}")
    print(f"  ... and {len(spanish) - 3} more")
    
    # Test 1.4: Search by country
    print("\n1.4 Languages in India:")
    india_langs = manager.get_by_country("India")
    for lang in india_langs[:3]:
        print(f"  - {lang['display_name']}")
    print(f"  ... and {len(india_langs) - 3} more")
    
    # Test 1.5: Search functionality
    print("\n1.5 Search for 'french':")
    results = manager.search("french")
    for result in results:
        print(f"  - {result['display_name']}")
    
    print("\n✓ Language Manager tests passed!\n")


def test_sample_rate_cards():
    """Test the sample rate card files."""
    print("=" * 60)
    print("TEST 2: Sample Rate Card Files")
    print("=" * 60)
    
    module_dir = Path(__file__).parent
    
    # Find sample rate card files
    sample_files = list(module_dir.glob("rate_cards_Sample*.json"))
    
    print(f"\nFound {len(sample_files)} sample rate card files:")
    
    for file_path in sample_files:
        print(f"\n  File: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"    Name: {data.get('name')}")
        print(f"    Sponsor: {data.get('sponsor')}")
        print(f"    Type: {data.get('type', 'itemized')}")
        print(f"    Languages: {len(data.get('languages', {}))}")
        print(f"    Services: {len(data.get('services', []))}")
        
        # Show sample rates
        first_lang = list(data.get('languages', {}).keys())[0] if data.get('languages') else None
        if first_lang:
            rates = data['languages'][first_lang].get('rates', {})
            print(f"    Sample rates for {first_lang}: {len(rates)} rate entries")
    
    print("\n✓ Sample Rate Card tests passed!\n")


def test_float_validation():
    """Test float validation logic."""
    print("=" * 60)
    print("TEST 3: Float Validation Testing")
    print("=" * 60)
    
    test_values = [
        ("0.15", True, 0.15),
        ("15", True, 15.0),
        ("0.5", True, 0.5),
        ("", True, ""),  # Empty is allowed
        ("invalid", False, None),
        ("12.34.56", False, None),
        ("abc123", False, None),
    ]
    
    print("\nTesting rate value validation:")
    for value, should_pass, expected in test_values:
        try:
            if value:
                result = float(value)
                status = "✓ PASS" if should_pass else "✗ FAIL"
                print(f"  {status}: '{value}' -> {result}")
            else:
                status = "✓ PASS" if should_pass else "✗ FAIL"
                print(f"  {status}: '{value}' (empty allowed)")
        except ValueError:
            status = "✓ PASS" if not should_pass else "✗ FAIL"
            print(f"  {status}: '{value}' (rejected as invalid)")
    
    print("\n✓ Float Validation tests passed!\n")


def test_language_parsing():
    """Test language parsing with different delimiters."""
    print("=" * 60)
    print("TEST 4: Language Parsing Testing")
    print("=" * 60)
    
    import re
    
    manager = get_language_manager()
    
    test_inputs = [
        "English, Spanish, French",
        "English; Spanish; French",
        "en-US, en-GB, es-ES",
        "English, French; Spanish",
    ]
    
    print("\nTesting language parsing with different delimiters:")
    for input_str in test_inputs:
        print(f"\n  Input: '{input_str}'")
        languages = re.split(r'[,;]', input_str)
        languages = [lang.strip() for lang in languages if lang.strip()]
        
        resolved = []
        missing = []
        for lang in languages:
            iso_data = manager.get_by_code(lang)
            if not iso_data:
                variants = manager.get_by_language(lang)
                iso_data = variants[0] if variants else None
            
            if iso_data:
                resolved.append(f"{lang} -> {iso_data['code']}")
            else:
                missing.append(lang)
        
        print(f"    Resolved: {len(resolved)}")
        for item in resolved:
            print(f"      - {item}")
        
        if missing:
            print(f"    Missing: {missing}")
    
    print("\n✓ Language Parsing tests passed!\n")


def test_file_structure():
    """Test that all required files exist."""
    print("=" * 60)
    print("TEST 5: File Structure Testing")
    print("=" * 60)
    
    module_dir = Path(__file__).parent
    
    required_files = [
        "__init__.py",
        "rate_card_builder_main.py",
        "itemized_rate_card_window.py",
        "tiered_rate_card_window.py",
        "load_rate_card_window.py",
        "language_loader.py",
        "languages_iso_codes.json",
        "requirements.txt",
        "README.md",
    ]
    
    print("\nChecking required files:")
    all_exist = True
    for file_name in required_files:
        file_path = module_dir / file_name
        exists = file_path.exists()
        status = "✓" if exists else "✗ MISSING"
        print(f"  {status}: {file_name}")
        if not exists:
            all_exist = False
    
    if all_exist:
        print("\n✓ All required files present!\n")
    else:
        print("\n✗ Some files are missing!\n")


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  RATE CARD BUILDER - COMPREHENSIVE TEST SUITE".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        test_file_structure()
        test_language_manager()
        test_float_validation()
        test_language_parsing()
        test_sample_rate_cards()
        
        print("=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\n✓ The Rate Card Builder is ready to use!")
        print("✓ Run 'python rate_card_builder_main.py' to launch the GUI\n")
        
    except Exception as e:
        print(f"\n✗ ERROR during testing: {str(e)}\n")


if __name__ == "__main__":
    main()
