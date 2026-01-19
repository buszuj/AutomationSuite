"""
Debug script for QuoteMe Email Parser regex
"""

import re

SAMPLE = """
Context*:	271
100%:	14
Repetitions:	78
Fuzzy Matches:	538
New Words:	2,780
Total Words:	3,681
"""

# Test pattern
pattern = re.compile(
    r'Context\*?:\s*([\d,]+|N/A).*?100%:\s*([\d,]+|N/A).*?Repetitions:\s*([\d,]+|N/A).*?Fuzzy Matches:\s*([\d,]+|N/A).*?New Words:\s*([\d,]+|N/A).*?Total Words:\s*([\d,]+|N/A)',
    re.DOTALL
)

match = pattern.search(SAMPLE)

if match:
    print("REGEX MATCH SUCCESSFUL")
    print(f"Groups: {match.groups()}")
    for i, g in enumerate(match.groups(), 1):
        print(f"  Group {i}: '{g}'")
else:
    print("NO MATCH")

# Try simpler test
simple_test = "New Words:\t2,780"
simple_pattern = re.compile(r'New Words:\s*([\d,]+)')
m = simple_pattern.search(simple_test)
if m:
    print(f"\nSimple test match: '{m.group(1)}'")
