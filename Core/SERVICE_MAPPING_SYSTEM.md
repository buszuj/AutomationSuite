# Service Mapping System Documentation

## Overview

The Service Mapping System ensures consistency when working with PA Services across different entities (TPUS, TPTDE, TPIT, TPFR, etc.). It uses **TPUS as the master entity** and maps all other entity services to TPUS services, enabling seamless translation between entities.

### Complete Workflow System

This is **Component 1** of a larger multi-entity workflow system:

1. **Service Mapping** (this system) - Maps service names between entities
2. **Workflow Definition** - User defines workflows using TPUS master services
3. **Entity Detection** - System identifies target entity for the request
4. **Automatic Translation** - Workflow automatically translates to target entity format

**Key Principle**: Map service names only (column 3). When a service is translated, it automatically brings its own entity-specific data (Service Groups 1 & 2, and UofM) from that entity's configuration.

## Architecture

### Core Components

1. **`Core/entity_service_mapper.py`** - Python backend for managing mappings
2. **`Core/service_mappings.json`** - JSON storage for all mappings
3. **`Core/workflow_translator.py`** - Translates TPUS workflows to target entities
4. **`One_Stop_Shop/gui/service_mapping_gui.py`** - GUI for editing mappings
5. **`One_Stop_Shop/gui/entity_manager_gui.py`** - Integrated with mapping features

### How It Works

**Service Name Mapping** (Column 3 only):
```
Entity Service → Master Service (TPUS) → Target Entity Service
    TPTDE            Translation              TPFR
"Übersetzung"   →   "Translation"    →   "Traduction"
```

**Full Service Row** (All 4 columns stay entity-specific):
```
When "Übersetzung" is used, it automatically brings:
- Its own Service Group 1 (from TPTDE config)
- Its own Service Group 2 (from TPTDE config)  
- Its own UofM (from TPTDE config)

The mapping only links service NAMES. Other data stays with its entity.
```

**Multi-Entity Workflow Example**:
1. User works on account with multiple entities
2. Defines workflow in TPUS: `["Translation", "Desktop Publishing"]`
3. Request comes in → Detected as TPTDE
4. System auto-translates: `["Übersetzung", "DTP"]` with full TPTDE data
5. User can switch entities mid-process if needed

## Features

### 1. Service Mapping GUI

**Access**: Click "🔗 Map Services" button on any entity card (except TPUS)

**Functionality**:
- Side-by-side view of entity services and TPUS master services
- Dropdown selection for 1:1 mapping
- Auto-mapping for services with matching names
- Real-time validation
- Unsaved changes detection

**Example Workflow**:
```
1. Open Entity Manager
2. Find TPTDE entity card
3. Click "🔗 Map Services"
4. Map "Übersetzung" → "Translation"
5. Map "Korrekturlesen" → "Proofreading"
6. Click "Save Mappings"
```

### 2. Master Service Sync

When you add a new service to **TPUS** (the master entity):

1. System detects the new service(s)
2. Prompts: "Do you want to add these to all other entities?"
3. If YES:
   - Adds the service to all entities with the same name
   - Creates default 1:1 mappings
   - User can edit service names and mappings later

**Example**:
```
1. Edit TPUS services
2. Add "Video Subtitling"
3. Save
4. Popup: "Add 'Video Subtitling' to all entities?"
5. If YES: All entities get "Video Subtitling" with default mapping
```

### 3. Automatic Mapping on Entity Creation

When creating a new entity:
- If copying from TPUS: Creates 1:1 mappings automatically
- If copying from another entity: Copies that entity's mappings
- If creating empty: No mappings (add services and map later)

## JSON Structure

**File**: `Core/service_mappings.json`

```json
{
  "master_entity": "TPUS",
  "mappings": {
    "TPTDE": {
      "Übersetzung": "Translation",
      "Korrekturlesen": "Proofreading",
      "DTP": "Desktop Publishing"
    },
    "TPIT": {
      "Traduzione": "Translation",
      "Revisione": "Proofreading",
      "Impaginazione": "Desktop Publishing"
    }
  }
}
```

**Key Points**:
- Only entity services are stored (not TPUS)
- Entity service name → Master service name
- Maps only the "Service" column (column index 2)
- Other columns (Service Groups, UoM) stay entity-specific

## Python API

### EntityServiceMapper Class

```python
from Core.entity_service_mapper import EntityServiceMapper, translate_service

# Initialize
mapper = EntityServiceMapper()

# Get mapping
master_service = mapper.get_mapping("TPTDE", "Übersetzung")
# Returns: "Translation"

# Translate between entities
french_service = mapper.translate_service("TPTDE", "TPFR", "Übersetzung")
# Returns: "Traduction" (via TPUS "Translation")

# Check unmapped services
unmapped = mapper.get_unmapped_services("TPIT", PA_SERVICES)
# Returns: ["Servizio Nuovo", ...] (services without mappings)

# Sync after TPUS update
mapper.update_all_entities_with_new_master_service("Video Subtitling", PA_SERVICES)
```

### Quick Functions

```python
from Core.entity_service_mapper import translate_service

# One-line translation
result = translate_service("TPTDE", "TPUS", "Übersetzung")
# Returns: "Translation"
```

## Use Cases

### Use Case 1: Multi-Entity Workflow (PRIMARY USE CASE)

**Scenario**: User works on account that operates across multiple entities. Workflow is defined in TPUS but needs to execute in different entities based on request.

**Workflow**:
```python
from Core.workflow_translator import WorkflowTranslator

translator = WorkflowTranslator()

# Step 1: User defines workflow in TPUS (master)
tpus_workflow = [
    "Translation and Proofreading",
    "Desktop Publishing", 
    "Proofreading"
]

# Step 2: Request comes in for specific entity
target_entity = "TPTDE"  # Detected from request

# Step 3: System automatically translates workflow
result = translator.translate_workflow(tpus_workflow, target_entity)

# Step 4: Use translated services with entity-specific data
for service in result:
    print(f"Service: {service['entity_service']}")
    print(f"  Service Group 1: {service['service_data']['service_group_1']}")
    print(f"  Service Group 2: {service['service_data']['service_group_2']}")
    print(f"  UofM: {service['service_data']['uom']}")

# Output:
# Service: Übersetzung
#   Service Group 1: Language Services
#   Service Group 2: Translation
#   UofM: Word
# Service: DTP
#   Service Group 1: Desktop Publishing
#   Service Group 2: Translation
#   UofM: Hour
```

**Key Benefits**:
- Define workflow once in TPUS
- Automatically get correct entity-specific names
- Entity-specific Service Groups and UofM preserved
- Switch entities mid-process if needed

### Use Case 2: Entity Switching Mid-Process

**Scenario**: User starts processing in one entity, then realizes they need to switch to another.

```python
from Core.workflow_translator import switch_workflow_entity

# Started in TPTDE
current_workflow = ["Übersetzung", "DTP", "Korrekturlesen"]

# Need to switch to TPFR
new_workflow = switch_workflow_entity(
    current_workflow,
    from_entity="TPTDE",
    to_entity="TPFR"
)

# Now have TPFR services with French names
for service in new_workflow:
    print(service['entity_service'])
# Output: Traduction, Le Formatting :(, Relecture
```

### Use Case 3: Multi-Entity Quote Processing

**Scenario**: Process quotes from different entities using unified logic

```python
from Core.entity_service_mapper import EntityServiceMapper

mapper = EntityServiceMapper()

# Quote from TPTDE
tptde_services = ["Übersetzung", "Korrekturlesen"]

# Translate to master (TPUS) for processing
master_services = [
    mapper.get_mapping("TPTDE", svc) 
    for svc in tptde_services
]
# Result: ["Translation", "Proofreading"]

# Apply TPUS pricing/logic
# ...

# Translate back to TPFR for output
tpfr_services = [
    mapper.get_reverse_mapping("TPFR", master_svc)
    for master_svc in master_services
]
# Result: ["Traduction", "Relecture"]
```

### Use Case 2: Data Migration

**Scenario**: Migrate data from one entity to another

```python
# Migrate TPIT quote to TPTDE format
source_entity = "TPIT"
target_entity = "TPTDE"
source_services = ["Traduzione", "Revisione"]

migrated = [
    mapper.translate_service(source_entity, target_entity, svc)
    for svc in source_services
]
# Result: ["Übersetzung", "Korrekturlesen"]
```

### Use Case 3: Reporting & Analytics

**Scenario**: Aggregate data across entities

```python
# Normalize all entity services to TPUS for reporting
all_entities = ["TPUS", "TPTDE", "TPIT", "TPFR"]

normalized_data = {}
for entity in all_entities:
    for service in get_entity_services(entity):
        master_service = mapper.get_mapping(entity, service)
        if master_service:
            if master_service not in normalized_data:
                normalized_data[master_service] = []
            normalized_data[master_service].append({
                "entity": entity,
                "local_name": service
            })

# Now you can analyze "Translation" across all entities
```

### Use Case 4: Workflow Validation

**Scenario**: Validate that a workflow can be executed in a target entity before processing

```python
from Core.workflow_translator import WorkflowTranslator

translator = WorkflowTranslator()

# Workflow defined in TPUS
workflow = ["Translation and Proofreading", "Desktop Publishing", "Video Subtitling"]

# Check if all services can be translated to TPTDE
valid, unmapped = translator.validate_workflow(workflow, "TPTDE")

if not valid:
    print(f"Warning: {len(unmapped)} services cannot be translated:")
    for service in unmapped:
        print(f"  - {service}")
    print("\nPlease map these services before proceeding.")
else:
    print("✓ All services can be translated. Proceeding...")
    result = translator.translate_workflow(workflow, "TPTDE")
```

### Use Case 5: Workflow Summary Report

**Scenario**: Generate human-readable report of workflow translation

```python
from Core.workflow_translator import WorkflowTranslator

translator = WorkflowTranslator()

workflow = ["Translation and Proofreading", "Desktop Publishing"]
summary = translator.get_workflow_summary(workflow, "TPTDE")

print(summary)

# Output:
# Workflow Translation: TPUS → TPTDE
# ======================================================================
# 
# 1. Translation and Proofreading → Übersetzung
#    Service Group 1: Language Services
#    Service Group 2: Translation
#    UofM: Word
#
# 2. Desktop Publishing → DTP
#    Service Group 1: Desktop Publishing
#    Service Group 2: Translation
#    UofM: Hour
```

## GUI Integration Points

### Entity Manager GUI

**File**: `One_Stop_Shop/gui/entity_manager_gui.py`

**Integration**:
1. **Entity Cards**: Shows "🔗 Map Services" button (except TPUS)
2. **Service Editor**: Detects TPUS changes and offers sync
3. **Entity Creation**: Auto-creates initial mappings

**Code**:
```python
# Open mapping window
def open_service_mapping(self, entity_name):
    mapper = ServiceMappingWindow(self.window, entity_name)
    self.editor_windows.append(mapper)
```

### Service Mapping Window

**File**: `One_Stop_Shop/gui/service_mapping_gui.py`

**Features**:
- Entity service list (left column)
- TPUS master service dropdown (right column)
- Auto-map button for matching names
- Save/Cancel buttons
- Unsaved changes warning

## Best Practices

### 1. Always Map New Services
- When adding services to any entity, map them immediately
- Use "Auto-Map Matching Names" for efficiency
- Review auto-mappings for accuracy

### 2. TPUS is Sacred
- Always update TPUS first when adding new service types
- Let the system sync to other entities
- Avoid deleting TPUS services with existing mappings

### 3. Mapping Validation
- Check for unmapped services regularly
- Use the mapping stats display: "Mapped: 15 / 17"
- Unmapped services won't translate correctly

### 4. Service Naming Conventions
- Keep service names descriptive and unique
- TPUS names should be language-neutral (English)
- Entity names can use local language

### 5. Testing Translations
```python
# Test your mappings
from Core.entity_service_mapper import translate_service

# Forward translation
assert translate_service("TPTDE", "TPUS", "Übersetzung") == "Translation"

# Reverse translation  
assert translate_service("TPUS", "TPTDE", "Translation") == "Übersetzung"

# Cross-entity translation
assert translate_service("TPTDE", "TPIT", "Übersetzung") == "Traduzione"
```

## Troubleshooting

### Problem: Service not translating

**Symptoms**: `translate_service()` returns `None`

**Causes & Solutions**:
1. **No mapping exists**
   - Solution: Open mapping GUI and create mapping
   
2. **Mapping points to wrong master service**
   - Solution: Edit mapping in GUI
   
3. **Typo in service name**
   - Solution: Check exact spelling in WF_Matrix.py

### Problem: New TPUS service not syncing

**Symptoms**: Added service to TPUS but other entities unchanged

**Causes & Solutions**:
1. **Didn't click "Yes" on sync prompt**
   - Solution: Manually add to other entities
   
2. **Error during sync**
   - Solution: Check console for errors, add manually

### Problem: Duplicate services

**Symptoms**: Multiple services mapping to same master service

**Causes & Solutions**:
1. **This is allowed by design** (many-to-one possible)
   - If unintended: Review and update mappings
   - If intended: Document the reason

## Migration Guide

### Migrating Existing Entities

If you have entities created before the mapping system:

```python
from Core.entity_service_mapper import EntityServiceMapper
from Core import WF_Matrix

mapper = EntityServiceMapper()

# Create mappings for existing entity
mapper.create_entity_mappings("TPTEST", WF_Matrix.PA_SERVICES)

# Verify
mappings = mapper.get_all_entity_mappings("TPTEST")
print(f"Created {len(mappings)} mappings")

# Check for unmapped
unmapped = mapper.get_unmapped_services("TPTEST", WF_Matrix.PA_SERVICES)
if unmapped:
    print(f"Still unmapped: {unmapped}")
```

## Future Enhancements

### Planned Features
- [ ] Bulk mapping import/export (CSV, Excel)
- [ ] Mapping validation report
- [ ] Service usage analytics
- [ ] Mapping history/versioning
- [ ] Multi-master support (if needed)
- [ ] Synonym suggestions (AI-powered)

### Potential Extensions
- **Service Categories**: Group related services
- **Context Mappings**: Map based on service context
- **Conditional Mappings**: Map differently based on UoM or Service Groups
- **Approval Workflow**: Require approval for mapping changes

## Support

### Getting Help
- Check this documentation first
- Review example use cases
- Test mappings with small datasets
- Consult Entity Manager GUI tooltips

### Reporting Issues
When reporting mapping issues, include:
1. Source entity and service name
2. Target entity (or TPUS)
3. Expected vs actual translation
4. Current mapping in JSON file
5. Screenshot of mapping GUI (if applicable)

---

**Version**: 1.0  
**Last Updated**: December 2025  
**Maintainer**: AutomationSuite Team
