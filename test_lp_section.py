"""
Check what is actually in the lp_section
"""

from Core.quoteme_email_parser import QuoteeMEmailParser
import re

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
breakdown_section = parser._extract_breakdown_section(SAMPLE_EMAIL)

# The regex pattern used in parser
wc_pattern = re.compile(
    r'Context\*?:\s*([\d,]+|N/A).*?100%:\s*([\d,]+|N/A).*?Repetitions:\s*([\d,]+|N/A).*?Fuzzy Matches:\s*([\d,]+|N/A).*?New Words:\s*([\d,]+|N/A).*?Total Words:\s*([\d,]+|N/A)',
    re.DOTALL | re.IGNORECASE
)

# Try on whole breakdown_section
match = wc_pattern.search(breakdown_section)
if match:
    print("Match on full breakdown_section:")
    print(f"Groups: {match.groups()}")
else:
    print("No match on breakdown_section")

# Now simulate what _parse_language_pair does
lp_matches = list(re.finditer(r'([^>]+)\s*>\s*([^>]+)', breakdown_section))

print(f"\nFound {len(lp_matches)} LP matches")

for i, lp_match in enumerate(lp_matches):
    lp_start = lp_match.start()
    lp_end = lp_matches[i + 1].start() if i + 1 < len(lp_matches) else len(breakdown_section)
    lp_section = breakdown_section[lp_start:lp_end]
    
    print(f"\nLP {i} section length: {len(lp_section)}")
    print(f"LP {i} section content:")
    print("=" * 60)
    print(lp_section)
    print("=" * 60)
    
    # Try regex on this section
    match = wc_pattern.search(lp_section)
    if match:
        print(f"\nWC match on LP {i}: {match.groups()}")
    else:
        print(f"\nNo WC match on LP {i}")

