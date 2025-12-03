"""
Entity Service Mapping Manager
Handles service name mappings between entities with TPUS as master.
Ensures consistency when switching between different entities.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Path to mappings file
MAPPINGS_FILE = Path(__file__).parent / "service_mappings.json"


class EntityServiceMapper:
    """Manages service mappings between entities with TPUS as master"""
    
    def __init__(self):
        self.mappings = self.load_mappings()
        self.master_entity = self.mappings.get("master_entity", "TPUS")
    
    def load_mappings(self) -> dict:
        """Load mappings from JSON file"""
        if MAPPINGS_FILE.exists():
            with open(MAPPINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"master_entity": "TPUS", "mappings": {}}
    
    def save_mappings(self):
        """Save mappings to JSON file"""
        with open(MAPPINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.mappings, f, indent=2, ensure_ascii=False)
    
    def get_master_services(self, pa_services: dict) -> List[str]:
        """
        Extract service names from master entity (TPUS)
        
        Args:
            pa_services: PA_SERVICES dictionary from WF_Matrix
            
        Returns:
            List of service names (excluding header)
        """
        master_list = pa_services.get(self.master_entity, [])
        if not master_list or len(master_list) < 2:
            return []
        
        # Extract service names (column index 2)
        return [row[2] for row in master_list[1:]]  # Skip header
    
    def get_entity_services(self, entity_name: str, pa_services: dict) -> List[str]:
        """
        Extract service names from a specific entity
        
        Args:
            entity_name: Name of entity
            pa_services: PA_SERVICES dictionary from WF_Matrix
            
        Returns:
            List of service names (excluding header)
        """
        entity_list = pa_services.get(entity_name, [])
        if not entity_list or len(entity_list) < 2:
            return []
        
        return [row[2] for row in entity_list[1:]]  # Skip header
    
    def get_mapping(self, entity_name: str, entity_service_name: str) -> Optional[str]:
        """
        Get the master (TPUS) service name for an entity's service
        
        Args:
            entity_name: Name of entity (e.g., "TPTDE")
            entity_service_name: Service name in that entity
            
        Returns:
            Master service name or None if not mapped
        """
        if entity_name == self.master_entity:
            return entity_service_name
        
        entity_mappings = self.mappings.get("mappings", {}).get(entity_name, {})
        return entity_mappings.get(entity_service_name)
    
    def set_mapping(self, entity_name: str, entity_service_name: str, master_service_name: str):
        """
        Set a mapping from entity service to master service
        
        Args:
            entity_name: Name of entity
            entity_service_name: Service name in that entity
            master_service_name: Service name in master (TPUS)
        """
        if entity_name not in self.mappings["mappings"]:
            self.mappings["mappings"][entity_name] = {}
        
        self.mappings["mappings"][entity_name][entity_service_name] = master_service_name
        self.save_mappings()
    
    def remove_mapping(self, entity_name: str, entity_service_name: str):
        """Remove a service mapping"""
        if entity_name in self.mappings["mappings"]:
            self.mappings["mappings"][entity_name].pop(entity_service_name, None)
            self.save_mappings()
    
    def get_reverse_mapping(self, entity_name: str, master_service_name: str) -> Optional[str]:
        """
        Get the entity service name from master service name
        
        Args:
            entity_name: Name of entity
            master_service_name: Service name in master (TPUS)
            
        Returns:
            Entity service name or None if not mapped
        """
        if entity_name == self.master_entity:
            return master_service_name
        
        entity_mappings = self.mappings.get("mappings", {}).get(entity_name, {})
        
        # Reverse lookup
        for entity_service, master_service in entity_mappings.items():
            if master_service == master_service_name:
                return entity_service
        
        return None
    
    def sync_entity_to_master(self, entity_name: str, pa_services: dict) -> List[str]:
        """
        Sync entity services to match master services.
        Returns list of master services that are missing in entity.
        
        Args:
            entity_name: Name of entity to sync
            pa_services: PA_SERVICES dictionary from WF_Matrix
            
        Returns:
            List of master services that need to be added to entity
        """
        master_services = self.get_master_services(pa_services)
        entity_mappings = self.mappings.get("mappings", {}).get(entity_name, {})
        
        # Find which master services don't have a mapping
        mapped_master_services = set(entity_mappings.values())
        missing_services = [s for s in master_services if s not in mapped_master_services]
        
        return missing_services
    
    def create_entity_mappings(self, entity_name: str, pa_services: dict):
        """
        Create initial 1:1 mappings for a new entity based on master services
        
        Args:
            entity_name: Name of new entity
            pa_services: PA_SERVICES dictionary from WF_Matrix
        """
        if entity_name == self.master_entity:
            return  # Master doesn't need mappings
        
        master_services = self.get_master_services(pa_services)
        entity_services = self.get_entity_services(entity_name, pa_services)
        
        # Create mappings
        if entity_name not in self.mappings["mappings"]:
            self.mappings["mappings"][entity_name] = {}
        
        # Map each entity service to corresponding master service
        # If copied from master, names should match 1:1
        for i, entity_service in enumerate(entity_services):
            if i < len(master_services):
                self.mappings["mappings"][entity_name][entity_service] = master_services[i]
        
        self.save_mappings()
    
    def get_unmapped_services(self, entity_name: str, pa_services: dict) -> List[str]:
        """
        Get list of entity services that don't have mappings
        
        Args:
            entity_name: Name of entity
            pa_services: PA_SERVICES dictionary from WF_Matrix
            
        Returns:
            List of unmapped service names
        """
        if entity_name == self.master_entity:
            return []
        
        entity_services = self.get_entity_services(entity_name, pa_services)
        entity_mappings = self.mappings.get("mappings", {}).get(entity_name, {})
        
        return [s for s in entity_services if s not in entity_mappings]
    
    def translate_service(self, from_entity: str, to_entity: str, service_name: str) -> Optional[str]:
        """
        Translate a service name from one entity to another via master
        
        Args:
            from_entity: Source entity name
            to_entity: Target entity name
            service_name: Service name in source entity
            
        Returns:
            Service name in target entity or None if not mapped
        """
        # First get the master service name
        master_service = self.get_mapping(from_entity, service_name)
        if not master_service:
            return None
        
        # Then get the target entity service name
        return self.get_reverse_mapping(to_entity, master_service)
    
    def get_all_entity_mappings(self, entity_name: str) -> Dict[str, str]:
        """
        Get all mappings for an entity
        
        Args:
            entity_name: Name of entity
            
        Returns:
            Dictionary of {entity_service: master_service}
        """
        return self.mappings.get("mappings", {}).get(entity_name, {})
    
    def update_all_entities_with_new_master_service(self, new_master_service: str, pa_services: dict):
        """
        When a new service is added to TPUS, add it to all other entities
        with the same name (user can edit later)
        
        Args:
            new_master_service: Name of new service in TPUS
            pa_services: PA_SERVICES dictionary from WF_Matrix
        """
        for entity_name in pa_services.keys():
            if entity_name == self.master_entity:
                continue
            
            # Check if this master service already has a mapping
            has_mapping = any(
                master_svc == new_master_service 
                for master_svc in self.mappings.get("mappings", {}).get(entity_name, {}).values()
            )
            
            if not has_mapping:
                # Add default 1:1 mapping (user can edit later)
                self.set_mapping(entity_name, new_master_service, new_master_service)


# Convenience functions
def load_mapper() -> EntityServiceMapper:
    """Load and return the entity service mapper"""
    return EntityServiceMapper()


def translate_service(from_entity: str, to_entity: str, service_name: str) -> Optional[str]:
    """
    Quick function to translate a service between entities
    
    Example:
        translate_service("TPTDE", "TPUS", "Übersetzung")  -> "Translation"
    """
    mapper = load_mapper()
    return mapper.translate_service(from_entity, to_entity, service_name)


if __name__ == "__main__":
    # Test the mapping system
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from WF_Matrix import PA_SERVICES
    
    mapper = EntityServiceMapper()
    
    print("Master Entity:", mapper.master_entity)
    print("\nMaster Services:")
    for service in mapper.get_master_services(PA_SERVICES):
        print(f"  - {service}")
    
    print("\nTesting mapping:")
    # Test translation
    result = mapper.translate_service("TPTFR", "TPUS", "Le Formatting :(")
    print(f"TPTFR 'Le Formatting :(' -> TPUS '{result}'")
    
    # Test unmapped
    unmapped = mapper.get_unmapped_services("TPTDE", PA_SERVICES)
    print(f"\nUnmapped services in TPTDE: {unmapped}")
