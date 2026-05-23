"""Scrape Bangladesh Legal Practitioners and Bar Council Order, 1972 from bdlaws."""
import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os
from datetime import datetime, timezone

BASE_URL = "http://bdlaws.minlaw.gov.bd"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "target_laws")

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
})

def fetch_utf16(url):
    resp = SESSION.get(url, timeout=120)
    return resp.content.decode('utf-16')

def get_section_ids(act_id, lang="en"):
    url = f"{BASE_URL}/act-{act_id}.html"
    if lang == "bn":
        url += "?lang=bn"
    html = fetch_utf16(url)
    soup = BeautifulSoup(html, 'lxml')
    section_ids = {}
    for a in soup.find_all('a', href=True):
        href = a['href']
        match = re.search(rf'/act-{act_id}/section-(\d+)\.html', href)
        if match:
            section_id = match.group(1)
            title = a.get_text(strip=True)
            clean_title = re.sub(r'^\d+[\.\s]+', '', title).strip()
            section_ids[clean_title] = section_id
            section_ids[title] = section_id
    return section_ids

def parse_act_details(html, act_id, section_id_map=None):
    soup = BeautifulSoup(html, 'lxml')
    sections = []
    if section_id_map is None:
        section_id_map = {}
    
    rows = soup.find_all('div', class_='row')
    current_part = ""
    current_chapter = ""
    section_index = 0
    seen_titles = set()
    
    for row in rows:
        part_divs = row.find_all('div', class_='act-part-group')
        if len(part_divs) > 1:
            pass
        elif len(part_divs) == 1:
            header_text = part_divs[0].get_text(separator=' ', strip=True)
            if header_text:
                if re.match(r'(Part|ভাগ)', header_text, re.I):
                    current_part = header_text
                    current_chapter = ""
                elif re.match(r'(Chapter|অধ্যায়)', header_text, re.I):
                    current_chapter = header_text
                else:
                    current_chapter = header_text
        
        title_div = row.find('div', class_='txt-head')
        content_div = row.find('div', id='sec-dec')
        
        if content_div:
            title = ""
            if title_div:
                title = title_div.get_text(strip=True)
            
            content_preview = content_div.get_text(strip=True)[:100]
            dedup_key = f"{title}|{content_preview}"
            if dedup_key in seen_titles:
                continue
            seen_titles.add(dedup_key)
            
            for br_div in content_div.find_all('div', class_=['clbr', 'na']):
                br_div.replace_with('\n')
            
            content_text = content_div.get_text(separator='\n', strip=False)
            content_text = re.sub(r'\n{3,}', '\n\n', content_text).strip()
            
            full_content = ""
            if current_part:
                full_content += current_part + "\n"
            if current_chapter:
                full_content += current_chapter + "\n"
            if title:
                full_content += title + "\n"
            full_content += content_text
            
            section_id = ""
            clean_title = re.sub(r'^\d+[\.\s]+', '', title).strip()
            if clean_title in section_id_map:
                section_id = section_id_map[clean_title]
            elif title in section_id_map:
                section_id = section_id_map[title]
            else:
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

def scrape_and_save(act_id, title, act_no, year, category, file_en, file_bn):
    for lang, filename in [("en", file_en), ("bn", file_bn)]:
        lang_label = "BN" if lang == "bn" else "EN"
        print(f"  [{lang_label}] Getting section IDs...")
        section_id_map = get_section_ids(act_id, lang)
        print(f"  [{lang_label}] Found {len(section_id_map)} section IDs")
        
        time.sleep(1.5)
        
        url = f"{BASE_URL}/act-details-{act_id}.html"
        if lang == "bn":
            url += "?lang=bn"
        print(f"  [{lang_label}] Fetching: {url}")
        html = fetch_utf16(url)
        print(f"  [{lang_label}] Page size: {len(html)} chars")
        
        sections = parse_act_details(html, act_id, section_id_map)
        print(f"  [{lang_label}] Parsed {len(sections)} sections")
        
        language = "bn-interface" if lang == "bn" else "en"
        source_url = f"{BASE_URL}/act-{act_id}.html"
        if lang == "bn":
            source_url += "?lang=bn"
        
        data = {
            "metadata": {
                "act_id": act_id,
                "title": title,
                "title_bn": None,
                "act_no": act_no,
                "year": year,
                "category": category,
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
        
        if lang == "bn":
            data["metadata"]["language_note"] = "Bengali UI interface with original English legal text."
        
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"  [{lang_label}] Saved: {filename} ({len(sections)} sections)")
        time.sleep(1.5)

if __name__ == "__main__":
    print("Scraping Bangladesh Legal Practitioners and Bar Council Order, 1972...")
    print("=" * 60)
    scrape_and_save(
        act_id="387",
        title="The Bangladesh Legal Practitioners and Bar Council Order, 1972",
        act_no="P.O. No. 46 of 1972",
        year=1972,
        category="Legal Profession",
        file_en="bar_council_order_en.json",
        file_bn="bar_council_order_bn.json",
    )
    print("\nDone!")
