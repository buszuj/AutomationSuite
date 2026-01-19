"""
Debug the actual email parsing
"""

from Core.quoteme_email_parser import QuoteeMEmailParser

SAMPLE_EMAIL = """
This quote represents only the live text in the file set. It does not include embedded files or dead text images. If your files do contain embedded images or otherwise "dead" text, you must account for that text in the estimate to avoid underquoting the project.

Always review the pseudo-translated files prior to quoting the client to ensure the desired translation output. 

Download the pseudo-translated files by clicking on the Completed link for your quote in the Quotes list.

Please note - Translation Memory leverage CANNOT BE CONSIDERED ACCURATE UNLESS YOU HAVE A LIVE FILE. A PDF is not a live file (even if it is a "live" PDF)

If the client will not send us a live file (e.g Word, PowerPoint, InDesign, etc.) and you want to be able to pass on the TM savings, please liaise with your local quotes / engineering team to ensure we have enough charges to convert the files for use with TM. Please set clients expectations accordingly that when working from a PDF (or any non-live file), final word count charges will be updated based on final words translated.

Quote Summary

Total # of files included in this quote: 1
Total # of TMs / LPs included in this quote: 1

Click here to open the quote in TransQuote


Quote Breakdown

English (United States) > Arabic (Saudi Arabia)
Context*:	271
100%:	14
Repetitions:	78
Fuzzy Matches:	538
New Words:	2,780
Total Words:	3,681

Remote TM String(s):	https://gl-tptprod5.transperfect.com/TMS?tm=NOV004161/NOV000073&usr=NovartisMerged_EN-US_AR-SA&pwd=877gvh!GHbvbkj7g

TM Configuration:	1585 QUOTEME_Novartis Patient Facing Adult_StaticAttributes

File name	Context	100%	Repetitions	Fuzzy Matches	New Words	Total Words
sa-leaflet.pdf.docx.txlf	271	14	78	538	2780	3681
"""

parser = QuoteeMEmailParser()

# Extract just the breakdown section
breakdown_section = parser._extract_breakdown_section(SAMPLE_EMAIL)
print("BREAKDOWN SECTION:")
print("-" * 60)
print(repr(breakdown_section[:300]))
print()

# Look for the word counts
import re
wc_match = re.search(
    r'Context\*?:\s*([\d,]+|N/A).*?100%:\s*([\d,]+|N/A).*?Repetitions:\s*([\d,]+|N/A).*?Fuzzy Matches:\s*([\d,]+|N/A).*?New Words:\s*([\d,]+|N/A).*?Total Words:\s*([\d,]+|N/A)',
    breakdown_section,
    re.DOTALL | re.IGNORECASE
)

if wc_match:
    print("WORD COUNT MATCH FOUND:")
    print(f"Groups: {wc_match.groups()}")
    for i, g in enumerate(wc_match.groups(), 1):
        print(f"  Group {i}: '{g}'")
else:
    print("NO WORD COUNT MATCH")
