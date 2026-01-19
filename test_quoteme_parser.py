"""
Test script for QuoteMe Email Parser
"""

from Core.quoteme_email_parser import QuoteeMEmailParser, ParseResult

# Sample email body from user
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

def test_parser():
    """Test the QuoteMe Email Parser"""
    parser = QuoteeMEmailParser()
    result = parser.parse(SAMPLE_EMAIL)
    
    print("=" * 60)
    print("QUOTEME EMAIL PARSER TEST")
    print("=" * 60)
    print(f"\nParse Success: {result.success}")
    print(f"Language Pairs Found: {len(result.language_pairs)}")
    
    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  ❌ {error}")
    
    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  ⚠️  {warning}")
    
    print("\n" + "-" * 60)
    print("EXTRACTED DATA:")
    print("-" * 60)
    
    for i, lp in enumerate(result.language_pairs, 1):
        print(f"\n{i}. Language Pair: {lp.lp_code}")
        print(f"   Source: {lp.source_lang}")
        print(f"   Target: {lp.target_lang}")
        
        print(f"\n   Cumulative Data:")
        print(f"   - Context: {lp.cumulative_wc.context:,}")
        print(f"   - 100%: {lp.cumulative_wc.fuzzy_100:,}")
        print(f"   - Repetitions: {lp.cumulative_wc.repetitions:,}")
        print(f"   - Fuzzy Matches: {lp.cumulative_wc.fuzzy_matches:,}")
        print(f"   - New Words: {lp.cumulative_wc.new_words:,}")
        print(f"   - Total: {lp.cumulative_wc.total:,}")
        
        if lp.file_breakdowns:
            print(f"\n   Per-File Breakdown ({len(lp.file_breakdowns)} files):")
            for fb in lp.file_breakdowns:
                print(f"     - {fb.file_name}: {fb.wc_data.total:,} words")
                print(f"       Context: {fb.wc_data.context:,}, 100%: {fb.wc_data.fuzzy_100:,}, " +
                      f"Repetitions: {fb.wc_data.repetitions:,}, Fuzzy: {fb.wc_data.fuzzy_matches:,}, " +
                      f"New: {fb.wc_data.new_words:,}")
        
        if lp.tm_config:
            print(f"\n   TM Configuration: {lp.tm_config}")
        
        if lp.tm_strings:
            print(f"\n   TM Strings ({len(lp.tm_strings)}):")
            for tm_str in lp.tm_strings:
                print(f"     - {tm_str[:60]}...")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_parser()
