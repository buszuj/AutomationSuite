"""
Workflow Translation System
Handles translation of TPUS-based workflows to target entities
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Add Core to path
sys.path.insert(0, str(Path(__file__).parent))
from entity_service_mapper import EntityServiceMapper
from WF_Matrix import PA_SERVICES


class WorkflowTranslator:
    """
    Translates TPUS-based workflows to target entity formats.
    
    Use Case:
    1. User defines workflow in TPUS (master services)
    2. Request comes in for specific entity (TPTDE, TPFR, etc.)
    3. System automatically translates TPUS workflow to target entity
    4. Returns full service rows with entity-specific data
    """
    
    def __init__(self):
        self.mapper = EntityServiceMapper()
        self.master_entity = "TPUS"
    
    def translate_workflow(
        self, 
        workflow_services: List[str], 
        target_entity: str,
        include_full_data: bool = True
    ) -> List[Dict[str, any]]:
        """
        Translate a TPUS-based workflow to target entity
        
        Args:
            workflow_services: List of TPUS service names
            target_entity: Target entity (e.g., "TPTDE", "TPFR")
            include_full_data: If True, returns full service row data
            
        Returns:
            List of service dictionaries with translated names and entity-specific data
            
        Example:
            workflow = ["Translation and Proofreading", "Desktop Publishing"]
            result = translator.translate_workflow(workflow, "TPTDE")
            # Returns full TPTDE service rows with German names
        """
        if target_entity == self.master_entity:
            # No translation needed for TPUS
            return self._get_service_data(workflow_services, self.master_entity, include_full_data)
        
        results = []
        
        for master_service in workflow_services:
            # Translate service name to target entity
            entity_service = self.mapper.get_reverse_mapping(target_entity, master_service)
            
            if not entity_service:
                # Service not mapped - keep original or flag as unmapped
                results.append({
                    "master_service": master_service,
                    "entity_service": master_service,  # Fallback to master name
                    "entity": target_entity,
                    "mapped": False,
                    "warning": f"No mapping found for '{master_service}' in {target_entity}",
                    "service_data": None
                })
                continue
            
            # Get full service row from target entity
            if include_full_data:
                service_data = self._find_service_in_entity(entity_service, target_entity)
            else:
                service_data = None
            
            results.append({
                "master_service": master_service,
                "entity_service": entity_service,
                "entity": target_entity,
                "mapped": True,
                "service_data": service_data
            })
        
        return results
    
    def _find_service_in_entity(self, service_name: str, entity: str) -> Optional[Dict[str, str]]:
        """
        Find and return full service row data from entity
        
        Returns:
            Dictionary with service data or None if not found
        """
        if entity not in PA_SERVICES:
            return None
        
        entity_services = PA_SERVICES[entity]
        
        # Skip header row
        for row in entity_services[1:]:
            if len(row) >= 4 and row[2] == service_name:
                return {
                    "service_group_1": row[0],
                    "service_group_2": row[1],
                    "service": row[2],
                    "uom": row[3]
                }
        
        return None
    
    def _get_service_data(self, service_names: List[str], entity: str, include_full: bool) -> List[Dict]:
        """Get service data for a list of services from an entity"""
        results = []
        
        for service_name in service_names:
            if include_full:
                service_data = self._find_service_in_entity(service_name, entity)
            else:
                service_data = None
            
            results.append({
                "master_service": service_name,
                "entity_service": service_name,
                "entity": entity,
                "mapped": True,
                "service_data": service_data
            })
        
        return results
    
    def batch_translate(
        self,
        workflow_services: List[str],
        target_entities: List[str]
    ) -> Dict[str, List[Dict]]:
        """
        Translate workflow to multiple entities at once
        
        Args:
            workflow_services: List of TPUS service names
            target_entities: List of target entities
            
        Returns:
            Dictionary mapping entity names to translated workflows
        """
        results = {}
        
        for entity in target_entities:
            results[entity] = self.translate_workflow(workflow_services, entity)
        
        return results
    
    def validate_workflow(self, workflow_services: List[str], target_entity: str) -> Tuple[bool, List[str]]:
        """
        Validate that all workflow services can be translated to target entity
        
        Args:
            workflow_services: List of TPUS service names
            target_entity: Target entity
            
        Returns:
            Tuple of (all_valid, list_of_unmapped_services)
        """
        unmapped = []
        
        for service in workflow_services:
            if target_entity == self.master_entity:
                continue  # TPUS always valid
            
            entity_service = self.mapper.get_reverse_mapping(target_entity, service)
            if not entity_service:
                unmapped.append(service)
        
        return (len(unmapped) == 0, unmapped)
    
    def get_workflow_summary(self, workflow_services: List[str], target_entity: str) -> str:
        """
        Get a human-readable summary of workflow translation
        
        Returns:
            Formatted string with translation details
        """
        results = self.translate_workflow(workflow_services, target_entity, include_full_data=True)
        
        lines = [
            f"Workflow Translation: TPUS → {target_entity}",
            "=" * 70,
            ""
        ]
        
        for i, result in enumerate(results, 1):
            if result["mapped"]:
                master = result["master_service"]
                entity = result["entity_service"]
                
                if target_entity == self.master_entity:
                    lines.append(f"{i}. {master}")
                else:
                    lines.append(f"{i}. {master} → {entity}")
                
                if result["service_data"]:
                    data = result["service_data"]
                    lines.append(f"   Service Group 1: {data['service_group_1']}")
                    lines.append(f"   Service Group 2: {data['service_group_2']}")
                    lines.append(f"   UofM: {data['uom']}")
            else:
                lines.append(f"{i}. {result['master_service']} → ⚠ UNMAPPED")
                lines.append(f"   Warning: {result['warning']}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def switch_entity_context(
        self,
        current_workflow: List[Dict],
        from_entity: str,
        to_entity: str
    ) -> List[Dict]:
        """
        Switch workflow context from one entity to another
        Used when user realizes they need to switch entities mid-process
        
        Args:
            current_workflow: Current workflow data
            from_entity: Current entity
            to_entity: Target entity
            
        Returns:
            Translated workflow for new entity
        """
        # Extract master services from current workflow
        master_services = []
        
        for item in current_workflow:
            if "master_service" in item:
                master_services.append(item["master_service"])
            elif "entity_service" in item:
                # Reverse lookup to get master service
                entity_service = item["entity_service"]
                master = self.mapper.get_mapping(from_entity, entity_service)
                if master:
                    master_services.append(master)
        
        # Translate to new entity
        return self.translate_workflow(master_services, to_entity)


# Convenience functions
def translate_workflow_to_entity(
    workflow_services: List[str],
    target_entity: str
) -> List[Dict]:
    """
    Quick function to translate TPUS workflow to target entity
    
    Example:
        workflow = ["Translation and Proofreading", "Proofreading"]
        result = translate_workflow_to_entity(workflow, "TPTDE")
        
        for service in result:
            print(f"{service['master_service']} → {service['entity_service']}")
            print(f"  Groups: {service['service_data']['service_group_1']}")
    """
    translator = WorkflowTranslator()
    return translator.translate_workflow(workflow_services, target_entity)


def switch_workflow_entity(
    current_services: List[str],
    from_entity: str,
    to_entity: str
) -> List[Dict]:
    """
    Switch workflow from one entity to another
    
    Example:
        # Started in TPUS
        tpus_workflow = ["Translation and Proofreading", "Desktop Publishing"]
        
        # Need to switch to TPTDE
        tptde_workflow = switch_workflow_entity(tpus_workflow, "TPUS", "TPTDE")
        
        # Use TPTDE services
        for service in tptde_workflow:
            print(service['entity_service'])  # German names
    """
    translator = WorkflowTranslator()
    
    # First translate current services to master (if not already)
    if from_entity != "TPUS":
        master_services = []
        for service in current_services:
            master = translator.mapper.get_mapping(from_entity, service)
            master_services.append(master if master else service)
    else:
        master_services = current_services
    
    # Then translate to target entity
    return translator.translate_workflow(master_services, to_entity)


if __name__ == "__main__":
    # Test the workflow translator
    print("=" * 70)
    print("WORKFLOW TRANSLATION SYSTEM - TEST")
    print("=" * 70)
    
    translator = WorkflowTranslator()
    
    # Scenario: User defines workflow in TPUS
    print("\n📋 SCENARIO: Multi-Entity Account Workflow")
    print("-" * 70)
    
    tpus_workflow = [
        "Translation and Proofreading",
        "Desktop Publishing",
        "Proofreading"
    ]
    
    print("\n1. Workflow defined in TPUS (master):")
    for i, service in enumerate(tpus_workflow, 1):
        print(f"   {i}. {service}")
    
    # User realizes request is for TPTDE
    print("\n2. Request identified as TPTDE → Translating workflow...")
    print()
    
    tptde_result = translator.translate_workflow(tpus_workflow, "TPTDE")
    
    for result in tptde_result:
        if result["mapped"]:
            print(f"   ✓ {result['master_service']} → {result['entity_service']}")
            if result["service_data"]:
                data = result["service_data"]
                print(f"     • Service Group 1: {data['service_group_1']}")
                print(f"     • Service Group 2: {data['service_group_2']}")
                print(f"     • UofM: {data['uom']}")
        else:
            print(f"   ⚠ {result['master_service']} → UNMAPPED")
    
    # Validation test
    print("\n3. Validation Check:")
    valid, unmapped = translator.validate_workflow(tpus_workflow, "TPTDE")
    if valid:
        print("   ✓ All services can be translated to TPTDE")
    else:
        print(f"   ⚠ Warning: {len(unmapped)} unmapped services: {unmapped}")
    
    # Switch entity test
    print("\n4. Entity Switch Test (TPTDE → TPFR):")
    tpfr_result = translator.switch_entity_context(tptde_result, "TPTDE", "TPFR")
    for result in tpfr_result:
        if result["mapped"]:
            print(f"   ✓ {result['entity_service']}")
    
    print("\n" + "=" * 70)
    print("✓ Workflow translation test complete!")
    print("=" * 70)
