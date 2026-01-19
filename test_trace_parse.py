"""
Trace through the actual parse to see where the issue is
"""

from Core.quoteme_email_parser import QuoteeMEmailParser

SAMPLE_EMAIL = """
Quote Breakdown

English (United States) > Arabic (Saudi Arabia)
Context*:	271
100%:	14
Repetitions:	78
Fuzzy Matches:	538
New Words:	2,780
Total Words:	3,681

Remote TM String(s):	https://gl-tptprod5.transperfect.com/TMS?tm=test

TM Configuration:	1585 QUOTEME_Test

File name	Context	100%	Repetitions	Fuzzy Matches	New Words	Total Words
sa-leaflet.pdf.docx.txlf	271	14	78	538	2780	3681
"""

parser = QuoteeMEmailParser()
result = parser.parse(SAMPLE_EMAIL)

print("Parse successful:", result.success)
print("LPs found:", len(result.language_pairs))

if result.language_pairs:
    lp = result.language_pairs[0]
    print(f"\nLP: {lp.lp_code}")
    print(f"Cumulative WC Context: {lp.cumulative_wc.context} (expected 271)")
    print(f"Cumulative WC Fuzzy100: {lp.cumulative_wc.fuzzy_100} (expected 14)")
    print(f"Cumulative WC Repetitions: {lp.cumulative_wc.repetitions} (expected 78)")
    print(f"Cumulative WC FuzzyMatches: {lp.cumulative_wc.fuzzy_matches} (expected 538)")
    print(f"Cumulative WC NewWords: {lp.cumulative_wc.new_words} (expected 2780)")
    print(f"Cumulative WC Total: {lp.cumulative_wc.total} (expected 3681)")
    
    # Also test the conversion function directly
    print("\nDirect conversion test:")
    test_val = "2,780"
    converted = int(test_val.replace(',', '').strip())
    print(f"Convert '{test_val}' -> {converted}")
