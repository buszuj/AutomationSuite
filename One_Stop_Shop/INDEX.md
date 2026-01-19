# Charges CSV Generation - Documentation Index

**Last Updated:** January 13, 2026
**Status:** Complete Analysis & Implementation Roadmap
**Total Documentation:** 4 comprehensive guides + this index

---

## 📚 START HERE

### For Quick Overview (5 minutes):
→ **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)**
- Summary of all critical gaps
- Priority checklist
- Quick start guide
- Success criteria

### For Complete Workflow Understanding (30 minutes):
→ **[CHARGES_CSV_GENERATION_GUIDE.md](CHARGES_CSV_GENERATION_GUIDE.md)**
- Part 1: Current implementation (what works)
- Part 2: Missing modules (what doesn't)
- Part 3: Implementation roadmap
- Part 4: Code gap checklist
- Part 5: Validation checklist

### For Visual Understanding (20 minutes):
→ **[CHARGES_CSV_FLOW_DIAGRAM.md](CHARGES_CSV_FLOW_DIAGRAM.md)**
- Complete user workflow flowchart
- Data flow diagrams
- Critical gap locations marked
- Test scenarios
- Configuration files status
- 3-week implementation timeline

### For Development (2-3 hours):
→ **[CODE_IMPLEMENTATION_TEMPLATES.md](CODE_IMPLEMENTATION_TEMPLATES.md)**
- Complete `rate_calculations.py` template
- Language mapping configuration
- Enhanced oss_config.yaml
- Unit test templates
- Integration points

---

## 🎯 Implementation by Role

### Project Manager
**Read:**
1. QUICK_REFERENCE.md (overview)
2. CHARGES_CSV_GENERATION_GUIDE.md Part 3 (roadmap)

**Actions:**
- Allocate 22 hours of developer time
- Confirm ratesheet structure with stakeholders
- Identify blocking dependencies

---

### Developer
**Read (in order):**
1. QUICK_REFERENCE.md (orientation)
2. CHARGES_CSV_GENERATION_GUIDE.md (full context)
3. CHARGES_CSV_FLOW_DIAGRAM.md (visual reference)
4. CODE_IMPLEMENTATION_TEMPLATES.md (actual code)

**Actions:**
- Create Core/rate_calculations.py
- Implement rate lookup functions
- Create language mapping
- Write unit tests
- Integrate with GUI

---

### QA / Tester
**Read:**
1. CHARGES_CSV_FLOW_DIAGRAM.md (test scenarios section)
2. CODE_IMPLEMENTATION_TEMPLATES.md (test template)
3. CHARGES_CSV_GENERATION_GUIDE.md Part 4 (validation)

**Actions:**
- Create test cases from scenarios provided
- Verify rates are populated correctly
- Test edge cases (min fee, fallback, etc.)
- Validate CSV format for ProjectA import

---

### Business Analyst
**Read:**
1. QUICK_REFERENCE.md (overview)
2. CHARGES_CSV_GENERATION_GUIDE.md Part 1 (current workflow)

**Actions:**
- Validate workflow matches business requirements
- Confirm CSV headers and format
- Document any variations per account
- Gather feedback from users

---

## 📋 Document Relationship Map

```
                    ┌─────────────────────┐
                    │  YOU ARE HERE       │
                    │  (This Index)       │
                    └──────────┬──────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
    ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
    │ QUICK REFERENCE  │ │ GENERATION GUIDE │ │ FLOW DIAGRAM     │
    │ (5 min overview) │ │ (30 min study)   │ │ (20 min visual)  │
    └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
             │                    │                    │
             └────────────────────┼────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ IMPLEMENTATION TEMPLATES │
                    │ (2-3 hours hands-on)     │
                    │                          │
                    │ • rate_calculations.py   │
                    │ • language_mapping.json  │
                    │ • unit tests             │
                    │ • oss_config.yaml        │
                    └──────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ IMPLEMENT & TEST         │
                    │                          │
                    │ Week 1-3 Development     │
                    └──────────────────────────┘
```

---

## 🔑 Key Concepts

### 1. The User Workflow
User performs these steps in the GUI:
1. Select PA Entity & Rate Sheet
2. Select Services (Translation, Formatting, etc.)
3. Enter Word Counts (QuoteMe or QTC)
4. Add Language Pairs (EN into DE, etc.)
5. Click "Save Charges CSV"
6. System generates CSV with rates

→ **Full details:** CHARGES_CSV_FLOW_DIAGRAM.md (Complete Workflow section)

---

### 2. The Critical Gap
The `save_charges_csv()` function needs three things:
- ❌ `get_word_rate()` function (MISSING)
- ❌ `get_hourly_rate()` function (MISSING)  
- ❌ `normalize_language_code()` function (MISSING)

Without these, CSV export fails silently.

→ **Implementation:** CODE_IMPLEMENTATION_TEMPLATES.md (Rate Calculations section)

---

### 3. The Priority System
**Priority 1 (Critical - 7 hours):** Blocks CSV generation
- Implement rate lookups
- Fix language codes
- Fix MT fallback

**Priority 2 (High - 10 hours):** Improves quality
- Fix minimum fee logic
- Add validation
- Create unit tests

**Priority 3 (Medium - 5 hours):** Enhances robustness
- Error handling
- Documentation
- Logging

→ **Full breakdown:** CHARGES_CSV_GENERATION_GUIDE.md (Part 3)

---

### 4. The Configuration Files
Files needed for rate lookups:
- `One_BP_IQ fixed.01.xlsx` (ratesheet - exists)
- `Core/language_code_mapping.json` (NEW)
- `oss_config.yaml` (enhanced version needed)
- `Core/rate_calculations.py` (NEW)

→ **Templates:** CODE_IMPLEMENTATION_TEMPLATES.md (Sections 1-3)

---

### 5. The Test Strategy
Test in this order:
1. Unit tests for each function in isolation
2. Integration tests for workflow combinations
3. End-to-end tests with real ratesheet
4. Edge case tests (min fee, fallback, etc.)

→ **Templates:** CODE_IMPLEMENTATION_TEMPLATES.md (Section 4)

---

## 🚀 Implementation Timeline

### Phase 1: Analysis & Preparation (4 hours)
- [ ] Read all documentation
- [ ] Examine ratesheet structure
- [ ] Document column names and data format
- [ ] Create language mapping list

**Deliverable:** Ratesheet specification document

---

### Phase 2: Core Implementation (10 hours)
- [ ] Create Core/rate_calculations.py
- [ ] Implement get_word_rate()
- [ ] Implement get_hourly_rate()
- [ ] Implement normalize_language_code()
- [ ] Create Core/language_code_mapping.json
- [ ] Update theonebp_app.py imports

**Deliverable:** Functional CSV export with rates

---

### Phase 3: Testing & Quality (5 hours)
- [ ] Create unit tests
- [ ] Test edge cases
- [ ] Test error handling
- [ ] End-to-end validation
- [ ] Fix issues found

**Deliverable:** Test coverage report

---

### Phase 4: Documentation & Release (3 hours)
- [ ] Document configuration
- [ ] Add logging
- [ ] Create user guide
- [ ] Code review
- [ ] Release to production

**Deliverable:** Production-ready CSV generation

**Total:** ~22 hours (can be phased)

---

## 📊 Current Status

| Component | Status | Priority | Effort |
|-----------|--------|----------|--------|
| GUI Layout | ✅ Complete | - | - |
| Service Selection | ✅ Complete | - | - |
| Word Count Input | ✅ Complete | - | - |
| Language Pairs | ✅ Complete | - | - |
| Preview Grid | ✅ Complete | - | - |
| CSV Header Building | ✅ Complete | - | - |
| **Rate Lookups** | ❌ Missing | P1 | 4h |
| **Language Normalization** | ❌ Missing | P1 | 1h |
| **MT Fallback (Fix)** | ⚠️ Buggy | P1 | 1h |
| **Minimum Fee Logic** | ⚠️ Complex | P2 | 3h |
| **Service Groups** | ⚠️ Incomplete | P2 | 1h |
| **Error Handling** | ⚠️ Minimal | P3 | 3h |
| **Unit Tests** | ❌ None | P2 | 5h |
| **Documentation** | ⚠️ Partial | P3 | 2h |

---

## 🔍 How to Find Things

### "I need to understand the GUI flow"
→ CHARGES_CSV_FLOW_DIAGRAM.md (Complete User Workflow section)

### "I need to write the rate lookup function"
→ CODE_IMPLEMENTATION_TEMPLATES.md (Section 1)

### "I need to understand what's missing"
→ CHARGES_CSV_GENERATION_GUIDE.md (Part 2)

### "I need to know where to start"
→ QUICK_REFERENCE.md (Quick Start section)

### "I need to verify my implementation"
→ CODE_IMPLEMENTATION_TEMPLATES.md (Section 4 - Unit Tests)

### "I need to understand the priority order"
→ CHARGES_CSV_GENERATION_GUIDE.md (Part 3 - Implementation Roadmap)

### "I need to see how everything fits together"
→ CHARGES_CSV_FLOW_DIAGRAM.md (Data Flow section)

### "I need to know what configuration files are needed"
→ CHARGES_CSV_GENERATION_GUIDE.md (Part 2 - GAP #10)

---

## ✅ Verification Checklist

Before starting implementation:
- [ ] All 4 documentation files read
- [ ] QUICK_REFERENCE.md understood
- [ ] Ratesheet structure documented
- [ ] Language pairs listed with ISO codes
- [ ] Expected CSV format confirmed
- [ ] Team members assigned to tasks
- [ ] Timeline agreed upon

During implementation:
- [ ] Each function has accompanying unit test
- [ ] Error handling for missing data
- [ ] Logging captures all rate lookups
- [ ] Integration tests pass
- [ ] Real ratesheet data tested

Before release:
- [ ] All Priority 1 items complete ✅
- [ ] CSV exports without errors
- [ ] Rates properly populated
- [ ] Language codes normalized
- [ ] Min fee logic verified
- [ ] End-to-end workflow tested
- [ ] No silent failures
- [ ] User receives clear error messages

---

## 🤝 Collaboration

### Communication Plan
- **Updates:** Document findings in ISSUES.md
- **Blockers:** Note in this index under "Current Issues"
- **Questions:** Reference relevant documentation section

### Code Review
Before merging:
1. Verify all functions implemented
2. Check error handling
3. Run unit tests
4. Test with real ratesheet
5. Verify CSV format

---

## 📞 Quick FAQ

**Q: What's the difference between these 4 files?**
A: 
- QUICK_REFERENCE: High-level summary (read first)
- GENERATION_GUIDE: Complete step-by-step details
- FLOW_DIAGRAM: Visual flowcharts and data flow
- TEMPLATES: Actual code to implement

**Q: Which file should I give to the developer?**
A: All 4 - they're complementary. Start with QUICK_REFERENCE.

**Q: How long to implement?**
A: 7 hours for critical fixes, 22 hours for full implementation

**Q: Can I skip Priority 3?**
A: Priority 1 is critical. Priority 2 is important for quality. Priority 3 is optional but recommended.

**Q: Where's the actual ratesheet?**
A: One_Stop_Shop/One_BP_IQ fixed.01.xlsx (you need to examine it)

---

## 📁 File Structure After Implementation

```
AutomationSuite/
├── Core/
│   ├── rate_calculations.py                     [NEW]
│   ├── language_code_mapping.json               [NEW]
│   ├── language_pair_manager.py                 [EXISTS]
│   ├── service_mapping_manager.py               [EXISTS]
│   ├── workflow_manager.py                      [EXISTS]
│   └── ... (other files)
│
├── One_Stop_Shop/
│   ├── theonebp_app.py                          [MODIFIED]
│   ├── oss_config.yaml                          [ENHANCED]
│   ├── One_BP_IQ fixed.01.xlsx                  [EXISTS]
│   │
│   ├── Documentation/
│   │   ├── CHARGES_CSV_GENERATION_GUIDE.md      [THIS PACKAGE]
│   │   ├── CHARGES_CSV_FLOW_DIAGRAM.md          [THIS PACKAGE]
│   │   ├── CODE_IMPLEMENTATION_TEMPLATES.md     [THIS PACKAGE]
│   │   ├── QUICK_REFERENCE.md                   [THIS PACKAGE]
│   │   └── INDEX.md                             [THIS FILE]
│   │
│   └── README.md (updated)
│
└── tests/
    ├── test_rate_calculations.py                [NEW]
    └── ... (other tests)
```

---

## 🎓 Learning Path

**New to the codebase:**
1. Start: QUICK_REFERENCE.md (15 min)
2. Study: CHARGES_CSV_GENERATION_GUIDE.md (45 min)
3. Visual: CHARGES_CSV_FLOW_DIAGRAM.md (30 min)
4. Code: CODE_IMPLEMENTATION_TEMPLATES.md (120 min)
5. Implement: Follow templates
6. Test: Create unit tests

**Familiar with codebase:**
1. Start: CHARGES_CSV_GENERATION_GUIDE.md Part 2 (gaps)
2. Implement: CODE_IMPLEMENTATION_TEMPLATES.md
3. Test: Follow test template
4. Integrate: Update theonebp_app.py

**Need quick fix:**
1. Start: CHARGES_CSV_FLOW_DIAGRAM.md (critical gaps marked)
2. Refer: CODE_IMPLEMENTATION_TEMPLATES.md
3. Implement: Specific function
4. Test: Specific unit test

---

## 📝 Notes

- All documentation is current as of January 13, 2026
- Ratesheet structure must be verified (see CHARGES_CSV_GENERATION_GUIDE.md Part 2 - GAP #1)
- Language pairs will vary by customer (use mapping from Excel)
- Service definitions subject to rate sheet configuration

---

## ✨ Final Notes

This documentation package represents a complete analysis of the Charges CSV generation feature. It identifies all missing pieces, provides implementation guidance, and includes code templates.

**Key Takeaways:**
- ✅ The GUI is built and mostly functional
- ❌ The rate calculation backend is incomplete
- ⚠️ Many edge cases and error scenarios need handling
- 📚 4 comprehensive guides provide clear implementation path
- 🚀 Ready to implement with 22 hours of focused effort

**Next Step:** Start with QUICK_REFERENCE.md, then proceed with implementation following CODE_IMPLEMENTATION_TEMPLATES.md

---

**Package Created By:** AI Assistant
**For:** One Stop Shop - Charges CSV Generation
**Status:** Ready for Development

Good luck! 🚀

