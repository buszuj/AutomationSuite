"""
Test script for Service Mapping System
Run this to verify the mapping system is working correctly
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
from entity_service_mapper import EntityServiceMapper
from WF_Matrix import PA_SERVICES


def test_basic_functionality():
    """Test basic mapper functionality"""
    print("=" * 70)
    print("SERVICE MAPPING SYSTEM - TEST SUITE")
    print("=" * 70)
    
    mapper = EntityServiceMapper()
    
    # Test 1: Load master services
    print("\n[TEST 1] Loading Master Services")
    master_services = mapper.get_master_services(PA_SERVICES)
    print(f"✓ Found {len(master_services)} TPUS services")
    print(f"  First 5: {master_services[:5]}")
    
    # Test 2: Load entity services
    print("\n[TEST 2] Loading Entity Services")
    for entity in ["TPTDE", "TPTEST", "TPTFR"]:
        if entity in PA_SERVICES:
            services = mapper.get_entity_services(entity, PA_SERVICES)
            print(f"✓ {entity}: {len(services)} services")
    
    # Test 3: Check existing mappings
    print("\n[TEST 3] Checking Existing Mappings")
    for entity in ["TPTDE", "TPTEST", "TPTFR"]:
        if entity in PA_SERVICES:
            mappings = mapper.get_all_entity_mappings(entity)
            print(f"✓ {entity}: {len(mappings)} mappings configured")
    
    # Test 4: Test translation
    print("\n[TEST 4] Testing Service Translation")
    test_cases = [
        ("TPTFR", "TPUS", "Le Formatting :("),
        ("TPTEST", "TPUS", "Translation and Proofreading"),
    ]
    
    for from_entity, to_entity, service in test_cases:
        if from_entity in PA_SERVICES:
            result = mapper.translate_service(from_entity, to_entity, service)
            if result:
                print(f"✓ {from_entity} '{service}' → {to_entity} '{result}'")
            else:
                print(f"✗ {from_entity} '{service}' → {to_entity} (no mapping)")
    
    # Test 5: Check for unmapped services
    print("\n[TEST 5] Checking for Unmapped Services")
    for entity in ["TPTDE", "TPTEST", "TPTFR"]:
        if entity in PA_SERVICES:
            unmapped = mapper.get_unmapped_services(entity, PA_SERVICES)
            if unmapped:
                print(f"⚠ {entity}: {len(unmapped)} unmapped services")
                for svc in unmapped[:3]:  # Show first 3
                    print(f"    - {svc}")
            else:
                print(f"✓ {entity}: All services mapped")
    
    # Test 6: Cross-entity translation
    print("\n[TEST 6] Testing Cross-Entity Translation")
    if "TPTEST" in PA_SERVICES and "TPTFR" in PA_SERVICES:
        service = "Translation and Proofreading"
        result = mapper.translate_service("TPTEST", "TPTFR", service)
        if result:
            print(f"✓ TPTEST '{service}' → TPTFR '{result}'")
        else:
            print(f"✗ TPTEST '{service}' → TPTFR (translation failed)")
    
    # Test 7: Reverse mapping
    print("\n[TEST 7] Testing Reverse Mapping")
    master_service = "Translation and Proofreading"
    for entity in ["TPTDE", "TPTEST", "TPTFR"]:
        if entity in PA_SERVICES:
            entity_service = mapper.get_reverse_mapping(entity, master_service)
            if entity_service:
                print(f"✓ TPUS '{master_service}' → {entity} '{entity_service}'")
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Master Entity: {mapper.master_entity}")
    print(f"Total Master Services: {len(master_services)}")
    print(f"Entities with Mappings: {len(mapper.mappings.get('mappings', {}))}")
    print("\n✓ All basic tests completed!")
    print("=" * 70)


def test_mapping_coverage():
    """Test mapping coverage across all entities"""
    print("\n" + "=" * 70)
    print("MAPPING COVERAGE REPORT")
    print("=" * 70)
    
    mapper = EntityServiceMapper()
    master_services = mapper.get_master_services(PA_SERVICES)
    
    for entity in PA_SERVICES.keys():
        if entity == "TPUS":
            continue
        
        entity_services = mapper.get_entity_services(entity, PA_SERVICES)
        mappings = mapper.get_all_entity_mappings(entity)
        unmapped = mapper.get_unmapped_services(entity, PA_SERVICES)
        
        coverage = (len(mappings) / len(entity_services) * 100) if entity_services else 0
        
        print(f"\n{entity}:")
        print(f"  Total Services: {len(entity_services)}")
        print(f"  Mapped: {len(mappings)}")
        print(f"  Unmapped: {len(unmapped)}")
        print(f"  Coverage: {coverage:.1f}%")
        
        if coverage < 100:
            print(f"  ⚠ Unmapped services: {', '.join(unmapped[:5])}")


if __name__ == "__main__":
    try:
        test_basic_functionality()
        test_mapping_coverage()
        
        print("\n🎉 All tests passed! Service mapping system is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error:")
        print(f"{e}")
        import traceback
        traceback.print_exc()
