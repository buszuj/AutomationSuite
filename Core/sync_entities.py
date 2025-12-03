"""
Entity Service Synchronization
Ensures all entities have the same services as TPUS (master)
"""

import sys
from pathlib import Path

# Add Core to path
sys.path.insert(0, str(Path(__file__).parent))
from WF_Matrix import PA_SERVICES
from entity_service_mapper import EntityServiceMapper


def sync_all_entities_to_master():
    """
    Synchronize all entities to have the same services as TPUS (master).
    Missing services are added with the same name as TPUS (user can edit later).
    """
    master_entity = "TPUS"
    
    if master_entity not in PA_SERVICES:
        print(f"Error: Master entity '{master_entity}' not found!")
        return False
    
    # Get master services (skip header)
    master_services = PA_SERVICES[master_entity][1:]
    master_service_names = [row[2] for row in master_services]  # Column 3 = Service name
    
    print(f"Master Entity: {master_entity}")
    print(f"Master Services: {len(master_services)}")
    print()
    
    # Load mapper
    mapper = EntityServiceMapper()
    
    # Read WF_Matrix.py file
    wf_matrix_path = Path(__file__).parent / "WF_Matrix.py"
    with open(wf_matrix_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    changes_made = False
    
    # Process each entity
    for entity_name, entity_services in PA_SERVICES.items():
        if entity_name == master_entity:
            continue  # Skip master
        
        print(f"Checking {entity_name}...")
        
        # Get current entity service names (skip header)
        current_services = entity_services[1:]
        current_service_names = [row[2] for row in current_services]
        
        # Find missing services
        missing_services = []
        for master_row in master_services:
            master_service_name = master_row[2]
            if master_service_name not in current_service_names:
                missing_services.append(master_row)
        
        if not missing_services:
            print(f"  ✓ {entity_name}: Already in sync ({len(current_services)} services)")
            continue
        
        print(f"  ⚠ {entity_name}: Missing {len(missing_services)} services")
        
        # Add missing services to this entity
        variable_name = f"{entity_name}_PA_SERVICES"
        
        # Find the entity's list in the file
        start_line = -1
        end_line = -1
        bracket_count = 0
        
        for i, line in enumerate(lines):
            if f"{variable_name} = [" in line:
                start_line = i
                bracket_count = line.count('[') - line.count(']')
            elif start_line != -1:
                bracket_count += line.count('[') - line.count(']')
                if bracket_count == 0:
                    end_line = i
                    break
        
        if start_line == -1:
            print(f"  ✗ Could not find {variable_name} in file!")
            continue
        
        # Build new service list with missing services added
        new_services = entity_services.copy()  # Include header
        for missing_row in missing_services:
            new_services.append(missing_row.copy())  # Add with same data as TPUS
            print(f"    + Adding: {missing_row[2]}")
            
            # Create mapping for new service
            mapper.set_mapping(entity_name, missing_row[2], missing_row[2])
        
        # Replace in file
        new_lines = [f"{variable_name} = [\n"]
        for service in new_services:
            new_lines.append(f"    {service},\n")
        new_lines.append("]\n")
        
        lines = lines[:start_line] + new_lines + lines[end_line + 1:]
        
        changes_made = True
        print(f"  ✓ {entity_name}: Synced to {len(new_services) - 1} services")
    
    if changes_made:
        # Write back to file
        with open(wf_matrix_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("\n✓ All entities synchronized!")
        return True
    else:
        print("\n✓ All entities already in sync!")
        return False


def get_sync_status():
    """Get synchronization status for all entities"""
    master_entity = "TPUS"
    
    if master_entity not in PA_SERVICES:
        return None
    
    master_count = len(PA_SERVICES[master_entity]) - 1  # Exclude header
    
    status = {}
    for entity_name, entity_services in PA_SERVICES.items():
        entity_count = len(entity_services) - 1  # Exclude header
        in_sync = entity_count == master_count
        
        status[entity_name] = {
            "count": entity_count,
            "in_sync": in_sync,
            "missing": master_count - entity_count if not in_sync else 0
        }
    
    return status


if __name__ == "__main__":
    print("=" * 70)
    print("ENTITY SERVICE SYNCHRONIZATION")
    print("=" * 70)
    print()
    
    # Show current status
    print("Current Status:")
    print("-" * 70)
    status = get_sync_status()
    for entity, info in status.items():
        sync_icon = "✓" if info["in_sync"] else "⚠"
        print(f"{sync_icon} {entity}: {info['count']} services", end="")
        if not info["in_sync"]:
            print(f" (missing {info['missing']})", end="")
        print()
    
    print()
    print("-" * 70)
    
    # Ask user
    response = input("\nSynchronize all entities to TPUS? (yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print()
        print("=" * 70)
        sync_all_entities_to_master()
        print("=" * 70)
    else:
        print("Synchronization cancelled.")
