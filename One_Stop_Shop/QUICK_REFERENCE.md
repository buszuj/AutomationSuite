# QUICK REFERENCE: Charges CSV Generation Implementation

**Generated:** January 13, 2026
**Status:** Ready for Implementation
**Estimated Effort:** 22 hours (priority-based breakdown available)

---

## 📚 Documentation Package Contents

You now have 4 comprehensive guides:

### 1. **CHARGES_CSV_GENERATION_GUIDE.md** (Complete Roadmap)
   - 7-part step-by-step user workflow
   - 10 major code gaps with descriptions
   - 4-tier implementation priority system
   - Detailed checklist for each gap
   - Related files reference

   **Use this to:** Understand the big picture and prioritize work

---

### 2. **CHARGES_CSV_FLOW_DIAGRAM.md** (Visual Reference)
   - Complete user workflow flowchart (ASCII)
   - Data flow: Input → Processing → Output
   - Critical gap locations marked in code
   - Configuration files status
   - Test scenarios checklist
   - Implementation order (3-week timeline)

   **Use this to:** Visualize the process and locate gaps in code

---

### 3. **CODE_IMPLEMENTATION_TEMPLATES.md** (Developer Guide)
   - Full template for `Core/rate_calculations.py`
   - Language mapping JSON configuration
   - Enhanced `oss_config.yaml`
   - Complete unit test template
   - Integration points for existing code

   **Use this to:** Actually write the missing code

---

### 4. **This file** (Quick Reference)
   - Summary of everything
   - Key files and functions
   - Quick jump-to sections

   **Use this to:** Get oriented quickly

---

## 🎯 CRITICAL GAPS (Must Fix First)

| # | Gap | Impact | Time | Fix Location |
|---|-----|--------|------|--------------|
| **GAP-1** | Missing `get_word_rate()` | ❌ CSV has 0/None rates | 2h | Create `Core/rate_calculations.py` |
| **GAP-2** | Missing `get_hourly_rate()` | ❌ Hourly services broken | 2h | Create `Core/rate_calculations.py` |
| **GAP-3** | Language codes not normalized | ❌ CSV won't import to ProjectA | 1h | Create `Core/language_normalization.py` |
| **GAP-4** | MT fallback doesn't handle None | ⚠️ Silent failures | 1h | Update `theonebp_app.py` line ~1140 |
| **GAP-5** | Service groups incomplete | ⚠️ Missing CSV columns | 1h | Validate `populate_services_and_uom()` |

**Total Priority 1 Time: 7 hours**

---

## 📁 Files to Create/Modify

### NEW FILES (Create these):

```
Core/
├── rate_calculations.py              [NEW] 200+ lines, 6 functions
└── language_code_mapping.json        [NEW] Configuration

tests/
└── test_rate_calculations.py         [NEW] Unit tests

One_Stop_Shop/
├── CODE_IMPLEMENTATION_TEMPLATES.md  [NEW] You're reading this
├── CHARGES_CSV_GENERATION_GUIDE.md   [NEW] Full guide
└── CHARGES_CSV_FLOW_DIAGRAM.md       [NEW] Visual reference
```

### MODIFY FILES:

```
One_Stop_Shop/
├── theonebp_app.py                   [UPDATE] Import rate functions
│   └── Line ~1120: Use get_word_rate()
│   └── Line ~1220: Normalize language codes
│   └── Line ~1350: Import functions
│
└── oss_config.yaml                   [ENHANCE] Add rate sheet config

Core/
└── (existing files - no changes needed initially)
```

---

## 🔗 Key File Locations

### Main GUI Application:
- **File:** [One_Stop_Shop/theonebp_app.py](theonebp_app.py)
- **Lines 1-150:** Initialization & manager setup
- **Lines 340-380:** User configuration (PA Entity, Rate Sheet, File Type)
- **Lines 420-550:** Service selection
- **Lines 850-950:** Word count input
- **Lines 1087-1375:** ⚠️ **CSV Export Logic (HAS GAPS)**

### Supporting Managers:
- **File:** [Core/workflow_manager.py](../Core/workflow_manager.py)
- **File:** [Core/language_pair_manager.py](../Core/language_pair_manager.py)
- **File:** [Core/service_mapping_manager.py](../Core/service_mapping_manager.py)

### Ratesheet:
- **File:** `One_Stop_Shop/One_BP_IQ fixed.01.xlsx`
- **Worksheets:** S IQVIA, S [OtherAccounts], Services per account, UofM, Languages

### Reference Implementation (CEVA):
- **File:** [Core/charges_engine_ceva.py](../Core/charges_engine_ceva.py)
- **Similar logic** but for different input model

---

## 🚀 QUICK START (Next 2 Hours)

### Step 1: Understand the Ratesheet (30 min)
```
□ Open: One_BP_IQ fixed.01.xlsx
□ Examine sheet "S IQVIA"
□ Document:
  - What column has service names?
  - What format are language pair columns? (EN > DE, EN_DE, etc.)
  - How are rates stored? (Numbers, NaN, "-", 0?)
  - Are there separate columns for old/new rates?
```

### Step 2: Create Language Mapping (30 min)
```
□ Load current Languages from ratesheet
□ Create Core/language_code_mapping.json
□ Map each display name to ISO 639-1 code:
  - "English (GB)" → "EN"
  - "German (Austria)" → "DE"
  - etc.
□ Test with all language pairs
```

### Step 3: Implement get_word_rate() (60 min)
```
□ Create Core/rate_calculations.py
□ Implement get_word_rate():
  - Normalize language names
  - Find rate column for LP
  - Find service row
  - Return rate value
□ Test with sample data
```

### Step 4: Test in GUI (30 min)
```
□ Update theonebp_app.py line ~1120
□ Import get_word_rate()
□ Add error handling
□ Generate sample CSV
□ Verify rates are populated
```

---

## 🧪 Testing Checklist

### Before Implementation:
- [ ] Ratesheet structure documented (columns, data format)
- [ ] All language pairs listed with ISO codes
- [ ] Test ratesheet data prepared
- [ ] Expected CSV format confirmed with ProjectA

### After Each Function:
- [ ] Standalone unit test passes
- [ ] Error handling tested (missing data, None values)
- [ ] Logging captures issues
- [ ] Matches existing behavior where applicable

### Before Release:
- [ ] All Priority 1 items complete
- [ ] CSV exports with correct rates
- [ ] Min fee logic verified
- [ ] Language codes properly normalized
- [ ] No silent failures (errors logged)
- [ ] Full end-to-end workflow tested

---

## ⚠️ Common Pitfalls to Avoid

1. **Language Code Confusion**
   - ❌ Don't: Use display names in CSV (they won't import)
   - ✅ Do: Always convert to ISO 639-1 codes

2. **Null/None Rates**
   - ❌ Don't: Return None silently (users won't know)
   - ✅ Do: Log warnings and show user-friendly errors

3. **Minimum Fee Edge Cases**
   - ❌ Don't: Forget to recalculate PM/Rush Premium after min fee
   - ✅ Do: Recompute percentage services based on modified word services

4. **Rate Lookup Assumptions**
   - ❌ Don't: Assume ratesheet structure (verify first!)
   - ✅ Do: Document exact column/row structure for each account

5. **Testing**
   - ❌ Don't: Only test happy path (works when rates exist)
   - ✅ Do: Test missing rates, wrong LPs, edge quantities

---

## 📞 Questions & Answers

**Q: Where do I start?**
A: Read CHARGES_CSV_GENERATION_GUIDE.md for complete overview, then CHARGES_CSV_FLOW_DIAGRAM.md for visual flow.

**Q: What's the ratesheet structure?**
A: Examine One_BP_IQ fixed.01.xlsx. Document what you find (columns, format, etc.).

**Q: Which function is most critical?**
A: `get_word_rate()` - without it, all CSV rates are 0/None.

**Q: Can I test without real data?**
A: Yes - Create mock ratesheets in unit tests before implementing.

**Q: How long will this take?**
A: Priority 1 (critical): 7 hours. Full implementation: 22 hours.

**Q: Should I implement all at once?**
A: No - Follow priority order: P1 (Critical) → P2 (High) → P3 (Medium)

**Q: What if I find issues?**
A: Document them in ISSUES.md with:
- What failed
- Expected behavior
- Actual behavior
- Steps to reproduce

---

## 📊 Success Criteria

You'll know it's working when:

✅ CSV exports without errors
✅ Rates are properly populated (not 0 or None)
✅ Language codes are ISO 639-1 format (EN, DE, FR, etc.)
✅ Minimum fee logic applies correctly
✅ Project Management rate = sum of services above
✅ Rush Premium rate = sum of all services
✅ All service rows included in CSV
✅ Service groups populated correctly
✅ File saves to user-selected location
✅ User receives success message

---

## 🔄 Workflow: From Here

### Day 1:
- [ ] Read all 4 documentation files
- [ ] Examine ratesheet structure
- [ ] Create language mapping
- [ ] Start Core/rate_calculations.py

### Day 2:
- [ ] Complete get_word_rate() and get_hourly_rate()
- [ ] Test with real ratesheet data
- [ ] Update theonebp_app.py integration points

### Day 3-5:
- [ ] Fix minimum fee logic
- [ ] Add comprehensive error handling
- [ ] Create unit tests
- [ ] End-to-end testing

### Week 2:
- [ ] Document configuration format
- [ ] Add logging
- [ ] Performance optimization
- [ ] Production release

---

## 📖 Related Documentation

Inside this package:
1. CHARGES_CSV_GENERATION_GUIDE.md - Full implementation guide
2. CHARGES_CSV_FLOW_DIAGRAM.md - Visual flowcharts and diagrams
3. CODE_IMPLEMENTATION_TEMPLATES.md - Copy-paste code templates

External references:
- CEVA_Launcher/ChargesIntegration.py - Similar implementation
- Core/charges_engine.py - Generic charges engine
- One_Stop_Shop/README.md - Application overview
- EXCEL_USAGE_GUIDE.md - Ratesheet documentation

---

## 🎓 Learning Resources

Understanding the system:
1. **Start:** Read CHARGES_CSV_GENERATION_GUIDE.md Part 1 (Current Workflow)
2. **Visualize:** Review CHARGES_CSV_FLOW_DIAGRAM.md
3. **Implement:** Follow CODE_IMPLEMENTATION_TEMPLATES.md
4. **Test:** Create unit tests in tests/test_rate_calculations.py

Understanding the code:
1. **GUI:** theonebp_app.py (main application)
2. **Managers:** Core/workflow_manager.py, language_pair_manager.py
3. **Reference:** CEVA_Launcher/ChargesIntegration.py (similar logic)

---

## ✅ Final Checklist Before You Start

- [ ] Have access to ratesheet file (One_BP_IQ fixed.01.xlsx)
- [ ] Python 3.7+ installed
- [ ] pandas, numpy installed
- [ ] Can edit Python files in VS Code
- [ ] Understand the 4 documentation files
- [ ] Have 22 hours available (or plan in phases)
- [ ] Know who to ask if stuck

---

**You are now ready to implement the Charges CSV generation feature!**

For questions, refer to the comprehensive guides or review the implementation templates.

Good luck! 🚀

