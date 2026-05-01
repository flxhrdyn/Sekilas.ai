import re
from typing import List

def clean_text_noise(text: str) -> str:
    """
    Cleans common noise patterns from extracted news text,
    specifically tailored for Indonesian news outlets.
    """
    if not text:
        return ""

    # 1. Remove "Read Also" and Navigational noise patterns
    noise_patterns = [
        # Indonesian patterns
        r"(?i)baca juga\s*[:\-].*",
        r"(?i)simak juga\s*[:\-].*",
        r"(?i)klik di sini\s*[:\-].*",
        r"(?i)pilihan editor\s*[:\-].*",
        r"(?i)berita terkait\s*[:\-].*",
        r"(?i)tonton juga\s*[:\-].*",
        r"(?i)simak video\s*[:\-].*",
        r"(?i)baca selengkapnya.*",
        r"(?i)top news.*",
        r"(?i)berita terkini.*",
        
        # International / English patterns
        r"(?i)read also\s*[:\-].*",
        r"(?i)related news\s*[:\-].*",
        r"(?i)most popular.*",
        r"(?i)trending now.*",
        r"(?i)editor's pick.*",
        r"(?i)watch also.*",
        r"(?i)see also.*",
        r"(?i)top stories.*",
        r"(?i)follow us on.*",
    ]
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip lines that match noise patterns
        if any(re.search(p, line) for p in noise_patterns):
            continue
            
        # Skip very short lines that look like breadcrumbs or metadata
        # (e.g. "Home > News", "Oleh: Nama Penulis")
        if len(line) < 30 and ('>' in line or '|' in line or 'Oleh:' in line):
            continue
            
        cleaned_lines.append(line)
        
    result = "\n".join(cleaned_lines)
    
    # 2. Post-processing whitespace
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()

def calculate_content_score(element) -> float:
    """
    Heuristic scoring for HTML elements to identify the main article body.
    Based on text length, comma density, and link density.
    """
    text = element.get_text(" ", strip=True)
    text_len = len(text)
    
    if text_len < 20:
        return 0.0
        
    # Link Density: high link density means it's likely a menu or recommendation block
    links = element.find_all('a')
    link_text_len = sum(len(a.get_text(strip=True)) for a in links)
    link_density = link_text_len / text_len if text_len > 0 else 0
    
    if link_density > 0.5: # More than 50% of text is links
        return 0.0
        
    # Comma density: natural sentences in news usually have commas
    # This helps distinguish between lists/menus and actual prose
    comma_count = text.count(',') + text.count('.')
    comma_score = (comma_count / 10) * 5 # Bonus for punctuation
    
    # Base score is text length
    score = text_len + comma_score
    
    # Penalty for short blocks
    if text_len < 100:
        score *= 0.5
        
    return score
