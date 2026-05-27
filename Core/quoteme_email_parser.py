"""
QuoteMe Email Parser Module

Parses TransPerfect QuoteMe email bodies to extract language pair data,
TM breakdowns, and file-level word counts. Supports both cumulative and
per-file data extraction with caching for later CSV generation.
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field, asdict
import json


@dataclass
class WordCountData:
    """Represents TM word count breakdown for a language pair or file"""
    context: int = 0
    fuzzy_100: int = 0
    repetitions: int = 0
    fuzzy_matches: int = 0
    new_words: int = 0
    
    @property
    def total(self) -> int:
        """Calculate total words"""
        return self.context + self.fuzzy_100 + self.repetitions + self.fuzzy_matches + self.new_words
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in ['context', 'fuzzy_100', 'repetitions', 'fuzzy_matches', 'new_words']})


@dataclass
class FileBreakdown:
    """Represents word counts for a single file"""
    file_name: str
    wc_data: WordCountData = field(default_factory=WordCountData)


@dataclass
class LanguagePairData:
    """Represents all data for a language pair from email"""
    lp_code: str  # e.g., "English (United States) > Arabic (Saudi Arabia)"
    source_lang: str
    target_lang: str
    cumulative_wc: WordCountData = field(default_factory=WordCountData)
    file_breakdowns: List[FileBreakdown] = field(default_factory=list)
    tm_config: str = ""
    tm_strings: List[str] = field(default_factory=list)
    
    def get_effective_wc(self, use_cumulative: bool = True) -> WordCountData:
        """Get effective word counts based on preference"""
        if use_cumulative or not self.file_breakdowns:
            return self.cumulative_wc
        else:
            # Sum all file breakdowns
            total_wc = WordCountData()
            for fb in self.file_breakdowns:
                total_wc.context += fb.wc_data.context
                total_wc.fuzzy_100 += fb.wc_data.fuzzy_100
                total_wc.repetitions += fb.wc_data.repetitions
                total_wc.fuzzy_matches += fb.wc_data.fuzzy_matches
                total_wc.new_words += fb.wc_data.new_words
            return total_wc
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for caching"""
        return {
            'lp_code': self.lp_code,
            'source_lang': self.source_lang,
            'target_lang': self.target_lang,
            'cumulative_wc': self.cumulative_wc.to_dict(),
            'file_breakdowns': [
                {'file_name': fb.file_name, 'wc_data': fb.wc_data.to_dict()}
                for fb in self.file_breakdowns
            ],
            'tm_config': self.tm_config,
            'tm_strings': self.tm_strings
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create from dictionary"""
        return cls(
            lp_code=data.get('lp_code', ''),
            source_lang=data.get('source_lang', ''),
            target_lang=data.get('target_lang', ''),
            cumulative_wc=WordCountData.from_dict(data.get('cumulative_wc', {})),
            file_breakdowns=[
                FileBreakdown(
                    file_name=fb['file_name'],
                    wc_data=WordCountData.from_dict(fb['wc_data'])
                )
                for fb in data.get('file_breakdowns', [])
            ],
            tm_config=data.get('tm_config', ''),
            tm_strings=data.get('tm_strings', [])
        )


@dataclass
class ParseResult:
    """Result of parsing an email"""
    success: bool
    language_pairs: List[LanguagePairData] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    raw_email: str = ""


class QuoteeMEmailParser:
    """Parser for QuoteMe email bodies from TransPerfect"""
    
    def __init__(self):
        self.lp_pattern = re.compile(r'([^>]+)\s*>\s*([^>]+)')  # Source > Target
        self.wc_pattern = re.compile(
            r'Context\*?:\s*([\d,]+|N/A).*?100%:\s*([\d,]+|N/A).*?Repetitions:\s*([\d,]+|N/A).*?Fuzzy Matches:\s*([\d,]+|N/A).*?New Words:\s*([\d,]+|N/A).*?Total Words:\s*([\d,]+|N/A)',
            re.DOTALL
        )
    
    def parse(self, email_body: str) -> ParseResult:
        """
        Parse QuoteMe email body and extract language pair data
        
        Args:
            email_body: Full body text of email
            
        Returns:
            ParseResult with extracted language pairs and any errors/warnings
        """
        result = ParseResult(success=False, raw_email=email_body)
        
        if not email_body or not email_body.strip():
            result.errors.append("Email body is empty")
            return result
        
        # Extract only the "Quote Breakdown" section
        breakdown_section = self._extract_breakdown_section(email_body)
        if not breakdown_section:
            result.errors.append("Could not find 'Quote Breakdown' section in email")
            return result
        
        # Find all language pair headers using a more specific pattern
        # Pattern: "Language (Region) > Language (Region)" at the start of a line
        # Language names can contain letters, spaces, parentheses, and hyphens
        lp_header_pattern = r'^\s*([A-Z][A-Za-z\s\(\)\-]+)\s*>\s*([A-Z][A-Za-z\s\(\)\-]+?)\s*$'
        
        lp_headers = []
        for match in re.finditer(lp_header_pattern, breakdown_section, re.MULTILINE):
            lp_headers.append({
                'header': match.group(0).strip(),
                'source': match.group(1).strip(),
                'target': match.group(2).strip(),
                'start': match.start(),
                'end': match.end()
            })
        
        if not lp_headers:
            result.errors.append("No language pairs found in Quote Breakdown section")
            return result
        
        # Extract data for each language pair
        for i, header_info in enumerate(lp_headers):
            # Get the section from this header to the next one (or end of section)
            section_start = header_info['end']
            section_end = lp_headers[i + 1]['start'] if i + 1 < len(lp_headers) else len(breakdown_section)
            lp_section = breakdown_section[section_start:section_end]
            
            try:
                lp_code = f"{header_info['source']} > {header_info['target']}"
                lp_data = self._parse_language_pair(lp_code, lp_section)
                if lp_data:
                    result.language_pairs.append(lp_data)
            except Exception as e:
                result.warnings.append(f"Error parsing {header_info['header']}: {str(e)}")
        
        if result.language_pairs:
            result.success = True
        else:
            result.errors.append("No valid language pairs could be extracted")
        
        return result
    
    def _extract_breakdown_section(self, email_body: str) -> Optional[str]:
        """Extract the Quote Breakdown section from email"""
        # Match from "Quote Breakdown" onwards
        # The section ends at various possible markers or end of email
        match = re.search(r'Quote Breakdown\s*\n(.*?)(?:\Z)', email_body, re.DOTALL)
        if match:
            section = match.group(1)
            # For now, return the entire section - the LP parser will handle splitting it
            return section
        return None
    
    def _parse_language_pair(self, lp_header: str, lp_section: str) -> Optional[LanguagePairData]:
        """
        Parse a single language pair section
        
        Args:
            lp_header: Language pair header (e.g., "English (United States) > Arabic (Saudi Arabia)")
            lp_section: The section containing all data for this LP
            
        Returns:
            LanguagePairData or None if parsing fails
        """
        # Parse language pair
        match = re.match(r'([^>]+)\s*>\s*([^>]+)', lp_header)
        if not match:
            return None
        
        source_lang = match.group(1).strip()
        target_lang = match.group(2).strip()
        lp_code = f"{source_lang} > {target_lang}"
        
        lp_data = LanguagePairData(
            lp_code=lp_code,
            source_lang=source_lang,
            target_lang=target_lang
        )
        
        # Extract TM Configuration
        tm_config_match = re.search(r'TM Configuration:\s*(.+?)(?=\n|$)', lp_section)
        if tm_config_match:
            lp_data.tm_config = tm_config_match.group(1).strip()
        
        # Extract Remote TM String(s)
        tm_strings_match = re.search(r'Remote TM String\(s\):\s*(.+?)(?=\n\n|TM Configuration|$)', lp_section)
        if tm_strings_match:
            tm_str = tm_strings_match.group(1).strip()
            # Extract URLs
            urls = re.findall(r'https?://[^\s]+', tm_str)
            lp_data.tm_strings.extend(urls)
        
        # Extract cumulative word counts (1st table)
        # Match ONLY the first occurrence after the LP name, before "Remote TM String" or similar
        # This ensures we don't accidentally match the file breakdown table header
        wc_section_match = re.search(
            r'(?:Context\*?:|100%:|Repetitions:|Fuzzy Matches:|New Words:|Total Words:).*?(?:Remote TM String|TM Configuration)',
            lp_section,
            re.DOTALL | re.IGNORECASE
        )
        
        if wc_section_match:
            wc_section = wc_section_match.group(0)
            # Now search for the word counts in this section
            wc_match = re.search(
                r'Context\*?:\s*([\d,]+|N/A).*?100%:\s*([\d,]+|N/A).*?Repetitions:\s*([\d,]+|N/A).*?Fuzzy Matches:\s*([\d,]+|N/A).*?New Words:\s*([\d,]+|N/A).*?Total Words:\s*([\d,]+|N/A)',
                wc_section,
                re.DOTALL | re.IGNORECASE
            )
        else:
            wc_match = None
        
        if wc_match:
            # DEBUG: Print what was captured
            groups = wc_match.groups()
            #print(f"DEBUG _parse_language_pair: wc_groups = {groups}")
            lp_data.cumulative_wc = self._parse_word_counts(groups)
        else:
            # Flag as missing
            pass
        
        # Extract per-file breakdown (3rd table)
        file_breakdowns = self._extract_file_breakdowns(lp_section)
        lp_data.file_breakdowns = file_breakdowns
        
        return lp_data
    
    def _parse_word_counts(self, groups: Tuple) -> WordCountData:
        """
        Parse word count values from regex groups
        
        Args:
            groups: Tuple of (context, 100%, repetitions, fuzzy_matches, new_words, total)
            
        Returns:
            WordCountData object
        """
        def to_int(val):
            if val == 'N/A' or not val:
                return 0
            # Remove commas and convert to int
            return int(val.replace(',', '').strip())
        
        # groups has 6 elements: context, 100%, repetitions, fuzzy_matches, new_words, total
        return WordCountData(
            context=to_int(groups[0]),
            fuzzy_100=to_int(groups[1]),
            repetitions=to_int(groups[2]),
            fuzzy_matches=to_int(groups[3]),
            new_words=to_int(groups[4])
        )
    
    def _extract_file_breakdowns(self, lp_section: str) -> List[FileBreakdown]:
        """
        Extract per-file word count breakdowns from the table
        
        Args:
            lp_section: Section containing the language pair data
            
        Returns:
            List of FileBreakdown objects
        """
        file_breakdowns = []
        
        # Look for file breakdown table (3rd table in the LP section)
        # Pattern: file_name followed by numbers for each count (with optional commas)
        file_pattern = re.compile(
            r'(\S+\.(?:pdf|docx|xlsx|pptx|txlf|txt|doc|xls|ppt)(?:\.docx)?\.txlf)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)',
            re.IGNORECASE
        )
        
        for match in file_pattern.finditer(lp_section):
            file_name = match.group(1)
            
            def to_int(val):
                return int(val.replace(',', '').strip())
            
            wc_data = WordCountData(
                context=to_int(match.group(2)),
                fuzzy_100=to_int(match.group(3)),
                repetitions=to_int(match.group(4)),
                fuzzy_matches=to_int(match.group(5)),
                new_words=to_int(match.group(6))
            )
            file_breakdowns.append(FileBreakdown(file_name=file_name, wc_data=wc_data))
        
        return file_breakdowns


class ParseCache:
    """Cache for storing parsed LP data during session"""
    
    def __init__(self):
        self.cache: Dict[str, LanguagePairData] = {}
    
    def store(self, lp_data_list: List[LanguagePairData]) -> None:
        """Store language pair data in cache"""
        for lp_data in lp_data_list:
            self.cache[lp_data.lp_code] = lp_data
    
    def get(self, lp_code: str) -> Optional[LanguagePairData]:
        """Retrieve language pair data from cache"""
        return self.cache.get(lp_code)
    
    def get_all(self) -> List[LanguagePairData]:
        """Get all cached language pairs"""
        return list(self.cache.values())
    
    def clear(self) -> None:
        """Clear cache"""
        self.cache.clear()
    
    def to_json(self) -> str:
        """Serialize cache to JSON"""
        data = {lp_code: lp_data.to_dict() for lp_code, lp_data in self.cache.items()}
        return json.dumps(data)
    
    def from_json(self, json_str: str) -> None:
        """Deserialize cache from JSON"""
        try:
            data = json.loads(json_str)
            self.cache = {
                lp_code: LanguagePairData.from_dict(lp_dict)
                for lp_code, lp_dict in data.items()
            }
        except json.JSONDecodeError as e:
            print(f"Error deserializing cache: {e}")


# Global cache instance
_parse_cache = ParseCache()


def get_parse_cache() -> ParseCache:
    """Get the global parse cache"""
    return _parse_cache
