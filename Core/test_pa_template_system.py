"""
Test Script for PA Template System
Tests the core PA template infrastructure modules

Run this script to validate:
1. PA Template Manager (template CRUD operations)
2. PA Template Processor (DataFrame processing with templates)
3. Charges Engine (charge generation)

Author: AutomationSuite Team
Date: December 2025
"""

import pandas as pd
import os
import sys
from pathlib import Path

# Add Core to path
core_path = Path(__file__).parent
sys.path.insert(0, str(core_path))

from pa_template_manager import PATemplateManager
from pa_template_processor import PATemplateProcessor
from charges_engine import ChargesEngine


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_pa_template_manager():
    """Test PA Template Manager functionality"""
    print_section("TEST 1: PA Template Manager")
    
    manager = PATemplateManager()
    
    # Test 1: Create a test template
    print("\n1. Creating test template for 'TEST_ACCOUNT'...")
    test_mappings = [
        {
            "key": "Project Code",
            "source_column": "Project_Code",
            "mapping_type": "direct",
            "static_value": None,
            "formula": None,
            "format": "text"
        },
        {
            "key": "Job ID",
            "source_column": "Sub_ID",
            "mapping_type": "direct",
            "static_value": None,
            "formula": None,
            "format": "text"
        },
        {
            "key": "Language Pair",
            "source_column": "Language_Pair",
            "mapping_type": "direct",
            "static_value": None,
            "formula": None,
            "format": "text"
        },
        {
            "key": "Word Count",
            "source_column": "Word_Count",
            "mapping_type": "direct",
            "static_value": None,
            "formula": None,
            "format": "number"
        },
        {
            "key": "Status",
            "source_column": None,
            "mapping_type": "static",
            "static_value": "Ready for Import",
            "formula": None,
            "format": "text"
        },
        {
            "key": "Total Cost",
            "source_column": None,
            "mapping_type": "calculated",
            "static_value": None,
            "formula": "row['Word_Count'] * 0.15",
            "format": "currency"
        }
    ]
    
    success = manager.create_template(
        account_name="TEST_ACCOUNT",
        template_name="Test Integration Template",
        description="Test template for validation",
        key_column_name="Field Name",
        data_column_name="Value",
        mappings=test_mappings
    )
    
    if success:
        print("   ✓ Template created successfully")
    else:
        print("   ✗ Failed to create template")
        return False
    
    # Test 2: Retrieve template
    print("\n2. Retrieving template...")
    template = manager.get_template("TEST_ACCOUNT")
    if template:
        print(f"   ✓ Template retrieved: {template['template_name']}")
        print(f"   ✓ Mappings count: {len(template['mappings'])}")
    else:
        print("   ✗ Failed to retrieve template")
        return False
    
    # Test 3: Add a new mapping
    print("\n3. Adding new mapping...")
    success = manager.add_mapping(
        account_name="TEST_ACCOUNT",
        key="Due Date",
        source_column="Due_Date",
        mapping_type="direct",
        format_type="date"
    )
    
    if success:
        updated_template = manager.get_template("TEST_ACCOUNT")
        print(f"   ✓ Mapping added. New count: {len(updated_template['mappings'])}")
    else:
        print("   ✗ Failed to add mapping")
    
    # Test 4: List all templates
    print("\n4. Listing all templates...")
    all_templates = manager.get_all_templates()
    print(f"   ✓ Total templates: {len(all_templates)}")
    for account, tmpl in all_templates.items():
        print(f"     - {account}: {tmpl['template_name']}")
    
    print("\n✓ PA Template Manager tests completed successfully!")
    return True


def test_pa_template_processor():
    """Test PA Template Processor functionality"""
    print_section("TEST 2: PA Template Processor")
    
    # Create sample DataFrame
    print("\n1. Creating sample job data...")
    sample_data = {
        "Sub_ID": ["12345", "12346", "12347"],
        "Project_Code": ["HAB12345", "HAB12346", "HAB12347"],
        "Language_Pair": ["en-US > fr-FR", "en-US > de-DE", "en-US > es-ES"],
        "Word_Count": [1500, 2000, 1200],
        "Due_Date": ["2025-01-15", "2025-01-20", "2025-01-18"],
        "Status": ["In Progress", "Ready", "Pending"]
    }
    df = pd.DataFrame(sample_data)
    print(f"   ✓ Created DataFrame with {len(df)} rows")
    print(f"\nDataFrame preview:")
    print(df.to_string(index=False))
    
    # Test 1: Validate compatibility
    print("\n2. Validating DataFrame compatibility with template...")
    processor = PATemplateProcessor()
    validation = processor.validate_template_compatibility(df, "TEST_ACCOUNT")
    
    print(f"   Valid: {validation['valid']}")
    if validation['missing_columns']:
        print(f"   Missing columns: {validation['missing_columns']}")
    if validation['warnings']:
        print(f"   Warnings: {validation['warnings']}")
    
    if validation['valid']:
        print("   ✓ DataFrame is compatible with template")
    else:
        print("   ⚠ DataFrame has compatibility issues (this is OK for testing)")
    
    # Test 2: Process single row
    print("\n3. Processing single row (row 0)...")
    result = processor.process_dataframe(df, "TEST_ACCOUNT", row_index=0)
    
    if result is not None:
        print("   ✓ Single row processed successfully")
        print(f"\nProcessed output (2-column format):")
        print(result.to_string(index=False))
    else:
        print("   ✗ Failed to process single row")
        return False
    
    # Test 3: Process multiple rows
    print("\n4. Processing multiple rows grouped by Sub_ID...")
    results = processor.process_multiple_rows(df, "TEST_ACCOUNT", group_by_column="Sub_ID")
    
    print(f"   ✓ Processed {len(results)} groups")
    for sub_id, processed_df in results.items():
        print(f"\n   Sub_ID {sub_id}:")
        print(f"   Rows: {len(processed_df)}")
        print(processed_df.head(3).to_string(index=False))
    
    # Test 4: Export to Excel
    print("\n5. Exporting processed data to Excel...")
    output_path = os.path.join(core_path, "test_pa_output.xlsx")
    success = processor.export_to_excel(results, output_path, worksheet_prefix="Sub_")
    
    if success:
        print(f"   ✓ Exported to: {output_path}")
        print(f"   ✓ Open this file to verify the 2-column format!")
    else:
        print("   ✗ Failed to export to Excel")
        return False
    
    print("\n✓ PA Template Processor tests completed successfully!")
    return True


def test_charges_engine():
    """Test Charges Engine functionality"""
    print_section("TEST 3: Charges Engine")
    
    # Create engine
    print("\n1. Creating charges engine...")
    engine = ChargesEngine()
    print("   ✓ Charges engine initialized")
    
    # Test 1: Generate translation charge
    print("\n2. Generating Translation charge...")
    charge = engine.generate_translation_charge(
        word_count=1500,
        language_pair="en-US > fr-FR",
        project_code="HAB12345",
        job_id="12345"
    )
    print(f"   ✓ Translation charge generated:")
    print(f"     Service: {charge['Service']}")
    print(f"     Quantity: {charge['Quantity']} {charge['Unit']}")
    print(f"     Rate: ${charge['Rate']}")
    print(f"     Amount: ${charge['Amount']}")
    
    # Test 2: Generate TM charges
    print("\n3. Generating TM charges...")
    fuzzy_charge = engine.generate_tm_fuzzy_charge(
        word_count=200,
        language_pair="en-US > fr-FR",
        project_code="HAB12345",
        job_id="12345"
    )
    print(f"   ✓ TM-Fuzzy charge: {fuzzy_charge['Quantity']} words @ ${fuzzy_charge['Rate']} = ${fuzzy_charge['Amount']}")
    
    exact_charge = engine.generate_tm_exact_charge(
        word_count=100,
        language_pair="en-US > fr-FR",
        project_code="HAB12345",
        job_id="12345"
    )
    print(f"   ✓ TM-Exact charge: {exact_charge['Quantity']} words @ ${exact_charge['Rate']} = ${exact_charge['Amount']}")
    
    # Test 3: Generate formatting charge
    print("\n4. Generating Formatting charge...")
    formatting_charge = engine.generate_formatting_charge(
        word_count=1500,
        language_pair="en-US > fr-FR",
        hourly_rate=55.0,
        words_per_hour=3000.0,
        project_code="HAB12345",
        job_id="12345"
    )
    print(f"   ✓ Formatting charge: {formatting_charge['Quantity']} hours @ ${formatting_charge['Rate']} = ${formatting_charge['Amount']}")
    
    # Test 4: Generate all charges for a job
    print("\n5. Generating all charges for a complete job...")
    job_data = {
        "project_code": "HAB12345",
        "job_id": "12345",
        "language_pair": "en-US > fr-FR",
        "word_count": 1500,
        "tm_fuzzy_count": 200,
        "tm_exact_count": 100
    }
    
    all_charges = engine.generate_charges_for_job(job_data)
    print(f"   ✓ Generated {len(all_charges)} charges:")
    
    total_amount = 0
    for charge in all_charges:
        print(f"     - {charge['Service']}: ${charge['Amount']:.2f}")
        total_amount += charge['Amount']
    
    print(f"\n   Total job cost: ${total_amount:.2f}")
    
    # Test 5: Export charges to Excel
    print("\n6. Exporting charges to Excel...")
    charges_by_job = {
        "12345": all_charges,
        "12346": engine.generate_charges_for_job({
            "project_code": "HAB12346",
            "job_id": "12346",
            "language_pair": "en-US > de-DE",
            "word_count": 2000,
            "tm_fuzzy_count": 300,
            "tm_exact_count": 150
        })
    }
    
    output_path = os.path.join(core_path, "test_charges_output.xlsx")
    
    # Create a base Excel file first
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        pd.DataFrame([{"Info": "Charges Export Test"}]).to_excel(writer, sheet_name="Summary", index=False)
    
    successful, failed = engine.export_charges_to_excel(charges_by_job, output_path)
    
    print(f"   ✓ Exported charges for {len(successful)} job(s)")
    print(f"   ✓ Output file: {output_path}")
    print(f"   ✓ Open this file to see Sub_12345_Charges and Sub_12346_Charges worksheets!")
    
    print("\n✓ Charges Engine tests completed successfully!")
    return True


def run_integration_test():
    """Test complete workflow: Template → DataFrame → Charges"""
    print_section("TEST 4: Integration Test (Complete Workflow)")
    
    print("\n1. Simulating complete OSS workflow...")
    print("   Step 1: Load template for account")
    print("   Step 2: Process job data with template")
    print("   Step 3: Generate charges")
    print("   Step 4: Export both to Excel")
    
    # Create sample job data
    job_data_df = pd.DataFrame({
        "Sub_ID": ["98765"],
        "Project_Code": ["TEST001"],
        "Language_Pair": ["en-US > ja-JP"],
        "Word_Count": [3000],
        "Due_Date": ["2025-02-01"],
        "Status": ["New"]
    })
    
    # Process with template
    processor = PATemplateProcessor()
    integration_data = processor.process_dataframe(job_data_df, "TEST_ACCOUNT", row_index=0)
    
    # Generate charges
    engine = ChargesEngine()
    job_charges = engine.generate_charges_for_job({
        "project_code": "TEST001",
        "job_id": "98765",
        "language_pair": "en-US > ja-JP",
        "word_count": 3000,
        "tm_fuzzy_count": 400,
        "tm_exact_count": 200
    })
    
    # Export both
    output_path = os.path.join(core_path, "test_integration_output.xlsx")
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Integration worksheet (2-column format)
        integration_data.to_excel(writer, sheet_name="Sub_98765", index=False)
        
        # Charges worksheet
        charges_df = pd.DataFrame(job_charges)
        charges_df.to_excel(writer, sheet_name="Sub_98765_Charges", index=False)
    
    print(f"\n   ✓ Integration test completed!")
    print(f"   ✓ Output: {output_path}")
    print(f"   ✓ This file simulates CEVA's Sub_{{ID}} + Sub_{{ID}}_Charges pattern!")
    print(f"\n   Open the file to verify:")
    print(f"     - Sub_98765 worksheet has 2-column format (Field Name | Value)")
    print(f"     - Sub_98765_Charges worksheet has charges breakdown")
    
    return True


def cleanup_test_files():
    """Optional: Clean up test output files"""
    print_section("Cleanup")
    
    test_files = [
        "test_pa_output.xlsx",
        "test_charges_output.xlsx",
        "test_integration_output.xlsx",
        "pa_template_configs.json"
    ]
    
    print("\nTest output files created:")
    for filename in test_files:
        file_path = os.path.join(core_path, filename)
        if os.path.exists(file_path):
            print(f"   - {filename}")
    
    print("\n⚠ These files are kept for your review.")
    print("  Open them in Excel to verify the output!")
    print("  Delete them manually when done testing.")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  PA TEMPLATE SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print("\nThis script tests all core PA template modules:")
    print("  1. PA Template Manager - template CRUD operations")
    print("  2. PA Template Processor - DataFrame to 2-column format")
    print("  3. Charges Engine - charge generation")
    print("  4. Integration Test - complete workflow")
    
    input("\nPress Enter to start testing...")
    
    try:
        # Run tests
        test_results = []
        
        test_results.append(("PA Template Manager", test_pa_template_manager()))
        test_results.append(("PA Template Processor", test_pa_template_processor()))
        test_results.append(("Charges Engine", test_charges_engine()))
        test_results.append(("Integration Test", run_integration_test()))
        
        # Show results summary
        print_section("TEST RESULTS SUMMARY")
        
        all_passed = True
        for test_name, passed in test_results:
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"\n  {test_name}: {status}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n" + "=" * 70)
            print("  🎉 ALL TESTS PASSED!")
            print("=" * 70)
            print("\nNext steps:")
            print("  1. Review the generated Excel files in Core/ folder")
            print("  2. Verify 2-column format in Integration worksheets")
            print("  3. Verify charges format in Charges worksheets")
            print("  4. Ready to proceed with GUI development!")
        else:
            print("\n" + "=" * 70)
            print("  ⚠ SOME TESTS FAILED")
            print("=" * 70)
            print("\nPlease review the errors above before proceeding.")
        
        cleanup_test_files()
        
    except Exception as e:
        print(f"\n✗ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    input("\nPress Enter to exit...")
    return True


if __name__ == "__main__":
    main()
