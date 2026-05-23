"""
Bangladesh Laws Scraper - Extract full text from bdlaws.minlaw.gov.bd
Extracts 6 key laws in both English and Bengali interface versions.

Site characteristics:
- Encoding: UTF-16
- Section listing: /act-{id}.html (contains links like /act-{id}/section-{section_id}.html)
- Full text: /act-details-{id}.html (all sections on one page)
- Bengali: append ?lang=bn
- Section structure: div.row.lineremoves > div.col-sm-3.txt-head + div#sec-dec.txt-details
- Part/Chapter headers: div.act-part-group.head
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
import re
from datetime import datetime, timezone

# Configuration
BASE_URL = "http://bdlaws.minlaw.gov.bd"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "target_laws")
os.makedirs(OUTPUT_DIR, exist_ok=True)

REQUEST_DELAY = 1.5  # seconds between requests

# Target laws
LAWS = [
    {
        "act_id": "11",
        "title": "The Penal Code, 1860",
        "act_no": "XLV",
        "year": 1860,
        "category": "Criminal Law",
        "file_en": "penal_code_en.json",
        "file_bn": "penal_code_bn.json",
    },
    {
        "act_id": "75",
        "title": "The Code of Criminal Procedure, 1898",
        "act_no": "V",
        "year": 1898,
        "category": "Criminal Law",
        "file_en": "crpc_en.json",
        "file_bn": "crpc_bn.json",
    },
    {
        "act_id": "86",
        "title": "The Code of Civil Procedure, 1908",
        "act_no": "V",
        "year": 1908,
        "category": "Civil & Contract Law",
        "file_en": "cpc_en.json",
        "file_bn": "cpc_bn.json",
    },
    {
        "act_id": "24",
        "title": "The Evidence Act, 1872",
        "act_no": "I",
        "year": 1872,
        "category": "Civil & Contract Law",
        "file_en": "evidence_act_en.json",
        "file_bn": "evidence_act_bn.json",
    },
    {
        "act_id": "88",
        "title": "The Limitation Act, 1908",
        "act_no": "IX",
        "year": 1908,
        "category": "Civil & Contract Law",
        "file_en": "limitation_act_en.json",
        "file_bn": "limitation_act_bn.json",
    },
    {
        "act_id": "36",
        "title": "The Specific Relief Act, 1877",
        "act_no": "I",
        "year": 1877,
        "category": "Civil & Contract Law",
        "file_en": "specific_relief_en.json",
        "file_bn": "specific_relief_bn.json",
    },
]

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
})


def fetch_page(url, retries=3):
    """Fetch a page with UTF-16 decoding and retry logic."""
    for attempt in range(retries):
        try:
            resp = SESSION.get(url, timeout=120)
            resp.raise_for_status()
            # Site uses UTF-16 encoding
            html = resp.content.decode('utf-16')
            time.sleep(REQUEST_DELAY)
            return html
        except UnicodeDecodeError:
            # Fallback to detected encoding
            try:
                html = resp.content.decode('utf-8')
                time.sleep(REQUEST_DELAY)
                return html
            except:
                html = resp.text
                time.sleep(REQUEST_DELAY)
                return html
        except requests.RequestException as e:
            print(f"    [Attempt {attempt+1}/{retries}] Error: {e}")
            if attempt < retries - 1:
                time.sleep(5 * (attempt + 1))
            else:
                raise
    return None


def get_section_ids(act_id, lang="en"):
    """Get section IDs from the main act page (TOC)."""
    url = f"{BASE_URL}/act-{act_id}.html"
    if lang == "bn":
        url += "?lang=bn"
    
    html = fetch_page(url)
    if not html:
        return {}
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Pattern: /act-{id}/section-{section_id}.html
    section_ids = {}  # title -> section_id
    for a in soup.find_all('a', href=True):
        href = a['href']
        match = re.search(rf'/act-{act_id}/section-(\d+)\.html', href)
        if match:
            section_id = match.group(1)
            title = a.get_text(strip=True)
            # Store both with and without section number prefix
            clean_title = re.sub(r'^\d+[\.\s]+', '', title).strip()
            section_ids[clean_title] = section_id
            section_ids[title] = section_id
    
    return section_ids


def parse_act_details(html, act_id, section_id_map=None):
    """Parse all sections from the act-details page."""
    soup = BeautifulSoup(html, 'lxml')
    sections = []
    
    if section_id_map is None:
        section_id_map = {}
    
    # Find all row containers that hold sections
    rows = soup.find_all('div', class_='row')
    
    current_part = ""
    current_chapter = ""
    section_index = 0
    seen_titles = set()  # Track duplicates
    
    for row in rows:
        # Check for part/chapter headers in this row
        part_divs = row.find_all('div', class_='act-part-group')
        
        # Skip rows that have multiple part headers (these are TOC/navigation rows)
        if len(part_divs) > 1:
            # This is likely the TOC row - skip the part headers but still process section if present
            pass
        elif len(part_divs) == 1:
            # Single part header - this is a real section boundary
            header_text = part_divs[0].get_text(separator=' ', strip=True)
            if header_text:
                if re.match(r'(Part|ভাগ)', header_text, re.I):
                    current_part = header_text
                    current_chapter = ""
                elif re.match(r'(Chapter|অধ্যায়)', header_text, re.I):
                    current_chapter = header_text
                else:
                    current_chapter = header_text
        
        # Check for section content
        title_div = row.find('div', class_='txt-head')
        content_div = row.find('div', id='sec-dec')
        
        if content_div:
            # Get title
            title = ""
            if title_div:
                title = title_div.get_text(strip=True)
            
            # Skip duplicates (sometimes the page has repeated sections)
            content_preview = content_div.get_text(strip=True)[:100]
            dedup_key = f"{title}|{content_preview}"
            if dedup_key in seen_titles:
                continue
            seen_titles.add(dedup_key)
            
            # Get content - preserve structure
            # Replace clbr and na divs with newlines
            for br_div in content_div.find_all('div', class_=['clbr', 'na']):
                br_div.replace_with('\n')
            
            # Get text content
            content_text = content_div.get_text(separator='\n', strip=False)
            # Clean up excessive whitespace while preserving paragraph breaks
            content_text = re.sub(r'\n{3,}', '\n\n', content_text)
            content_text = content_text.strip()
            
            # Build the full section content with context
            full_content = ""
            if current_part:
                full_content += current_part + "\n"
            if current_chapter:
                full_content += current_chapter + "\n"
            if title:
                full_content += title + "\n"
            full_content += content_text
            
            # Try to match section ID from the TOC map
            section_id = ""
            clean_title = re.sub(r'^\d+[\.\s]+', '', title).strip()
            
            # Exact match
            if clean_title in section_id_map:
                section_id = section_id_map[clean_title]
            elif title in section_id_map:
                section_id = section_id_map[title]
            else:
                # Partial match - find best match
                for map_title, map_id in section_id_map.items():
                    map_clean = re.sub(r'^\d+[\.\s]+', '', map_title).strip()
                    if clean_title and len(clean_title) > 5 and (
                        clean_title == map_clean or 
                        (len(clean_title) > 10 and clean_title in map_clean) or
                        (len(map_clean) > 10 and map_clean in clean_title)):
                        section_id = map_id
                        break
            
            if not section_id:
                section_id = str(section_index + 1)
            
            sections.append({
                "section_id": section_id,
                "title": title,
                "content": full_content,
                "has_content": bool(content_text.strip()),
            })
            section_index += 1
    
    return sections


def scrape_law(act_id, lang="en"):
    """Scrape a complete law from bdlaws."""
    lang_label = "BN" if lang == "bn" else "EN"
    print(f"\n  [{lang_label}] Getting section IDs from TOC...")
    
    # Step 1: Get section IDs from main page
    section_id_map = get_section_ids(act_id, lang)
    print(f"  [{lang_label}] Found {len(section_id_map)} section IDs in TOC")
    
    # Step 2: Fetch the full details page
    url = f"{BASE_URL}/act-details-{act_id}.html"
    if lang == "bn":
        url += "?lang=bn"
    
    print(f"  [{lang_label}] Fetching full text from: {url}")
    html = fetch_page(url)
    if not html:
        print(f"  [{lang_label}] ERROR: Could not fetch details page")
        return []
    
    print(f"  [{lang_label}] Page size: {len(html)} chars")
    
    # Step 3: Parse sections
    sections = parse_act_details(html, act_id, section_id_map)
    print(f"  [{lang_label}] Parsed {len(sections)} sections")
    
    return sections


def save_law(law_info, sections, lang, filename):
    """Save scraped law data to JSON file."""
    language = "bn-interface" if lang == "bn" else "en"
    source_url = f"{BASE_URL}/act-{law_info['act_id']}.html"
    if lang == "bn":
        source_url += "?lang=bn"
    
    # Add language note for BN
    language_note = None
    if lang == "bn":
        language_note = ("Bengali UI interface. These colonial-era acts are enacted in English. "
                        "The ?lang=bn view provides Bengali section/chapter headings with original English legal text.")
    
    data = {
        "metadata": {
            "act_id": law_info['act_id'],
            "title": law_info['title'],
            "title_bn": None,
            "act_no": law_info['act_no'],
            "year": law_info['year'],
            "category": law_info['category'],
            "language": language,
            "source_url": source_url,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "source": "Ministry of Law, Justice and Parliamentary Affairs, Bangladesh",
            "source_site": BASE_URL,
            "total_sections": len(sections),
            "sections_with_content": sum(1 for s in sections if s.get('has_content')),
            "total_rag_chunks": len(sections),
        },
        "sections": sections
    }
    
    if language_note:
        data["metadata"]["language_note"] = language_note
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"  Saved: {filename} ({len(sections)} sections, {sum(1 for s in sections if s['has_content'])} with content)")
    return data


def generate_all_laws_rag(all_law_data):
    """Generate the combined all_laws_rag.json file."""
    laws_summary = []
    total_chunks = 0
    
    for law_data, filename in all_law_data:
        meta = law_data['metadata']
        total_chunks += meta['total_rag_chunks']
        laws_summary.append({
            "file": filename,
            "act_id": meta['act_id'],
            "title": meta['title'],
            "title_bn": meta.get('title_bn'),
            "year": meta['year'],
            "act_no": meta['act_no'],
            "category": meta['category'],
            "language": meta['language'],
            "source_url": meta['source_url'],
            "total_sections": meta['total_sections'],
            "total_rag_chunks": meta['total_rag_chunks'],
        })
    
    rag_data = {
        "project": "Bangladesh Laws \u2014 6 Key Laws (EN + BN) \u2014 RAG Database",
        "description": ("Full text of 6 foundational Bangladesh laws: Penal Code, CrPC, "
                       "Specific Relief Act, CPC, Evidence Act, Limitation Act. Each law in "
                       "English and Bengali interface. Source: Ministry of Law, Justice and "
                       "Parliamentary Affairs, Bangladesh (bdlaws.minlaw.gov.bd). "
                       "Authenticated and verified against source."),
        "source": "Ministry of Law, Justice and Parliamentary Affairs, Bangladesh",
        "source_url": BASE_URL,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "total_laws": len(laws_summary),
        "total_rag_chunks": total_chunks,
        "intended_use": "RAG for LLM, AI agents, legal search tools",
        "laws": laws_summary
    }
    
    filepath = os.path.join(OUTPUT_DIR, "all_laws_rag.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(rag_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nGenerated: all_laws_rag.json (Total: {len(laws_summary)} laws, {total_chunks} chunks)")
    return rag_data


def generate_summary(all_law_data):
    """Generate summary.json."""
    laws_summary = []
    total_chunks = 0
    
    for law_data, filename in all_law_data:
        meta = law_data['metadata']
        total_chunks += meta['total_rag_chunks']
        laws_summary.append({
            "file": filename,
            "act_id": meta['act_id'],
            "title": meta['title'],
            "title_bn": meta.get('title_bn'),
            "year": meta['year'],
            "act_no": meta['act_no'],
            "category": meta['category'],
            "language": meta['language'],
            "source_url": meta['source_url'],
            "total_sections": meta['total_sections'],
            "total_rag_chunks": meta['total_rag_chunks'],
        })
    
    all_files = [item[1] for item in all_law_data] + ["all_laws_rag.json", "summary.json"]
    
    summary = {
        "project": "Bangladesh Laws \u2014 6 Key Laws Database",
        "source": "Ministry of Law, Justice and Parliamentary Affairs, Bangladesh",
        "source_url": BASE_URL,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "total_laws_files": len(laws_summary),
        "total_rag_chunks": total_chunks,
        "laws": laws_summary,
        "files": sorted(set(all_files))
    }
    
    filepath = os.path.join(OUTPUT_DIR, "summary.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"Generated: summary.json")


def main():
    print("=" * 70)
    print("  Bangladesh Laws Scraper - bdlaws.minlaw.gov.bd")
    print(f"  Source: {BASE_URL}")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"  Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)
    
    all_law_data = []
    
    for law in LAWS:
        print(f"\n{'#'*70}")
        print(f"  {law['title']} (Act {law['act_id']}, {law['year']})")
        print(f"{'#'*70}")
        
        for lang, filename_key in [("en", "file_en"), ("bn", "file_bn")]:
            filename = law[filename_key]
            
            try:
                sections = scrape_law(law['act_id'], lang)
                
                if sections:
                    law_data = save_law(law, sections, lang, filename)
                    all_law_data.append((law_data, filename))
                else:
                    print(f"  WARNING: No sections extracted for {filename}")
            except Exception as e:
                print(f"  ERROR processing {filename}: {e}")
                import traceback
                traceback.print_exc()
    
    # Generate combined files
    if all_law_data:
        print(f"\n{'='*70}")
        print("  Generating combined files...")
        print(f"{'='*70}")
        generate_all_laws_rag(all_law_data)
        generate_summary(all_law_data)
    
    print(f"\n{'='*70}")
    print(f"  COMPLETED: {datetime.now(timezone.utc).isoformat()}")
    print(f"  Total law files: {len(all_law_data)}")
    print(f"  Total sections: {sum(d['metadata']['total_sections'] for d, _ in all_law_data)}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
