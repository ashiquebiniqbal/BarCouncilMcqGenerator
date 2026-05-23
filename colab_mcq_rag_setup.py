"""
Bangladesh Bar Council MCQ Generator - Colab RAG Setup
======================================================
This script prepares the 6-law dataset for fine-tuning and RAG-based
MCQ generation for the Bangladesh Bar Council Advocates' Enrolment Examination.

Usage in Google Colab:
1. Upload the data/target_laws/ folder to your Colab environment
2. Run this script to prepare training data
3. Use with your preferred LLM (GPT-4, Gemini, LLaMA, etc.)

Laws covered:
1. The Penal Code, 1860 (দণ্ডবিধি)
2. The Code of Criminal Procedure, 1898 (ফৌজদারি কার্যবিধি)
3. The Code of Civil Procedure, 1908 (দেওয়ানি কার্যবিধি)
4. The Evidence Act, 1872 (সাক্ষ্য আইন)
5. The Limitation Act, 1908 (তামাদি আইন)
6. The Specific Relief Act, 1877 (সুনির্দিষ্ট প্রতিকার আইন)
"""

import json
import os
import re
from typing import List, Dict, Any

# ============================================================
# CONFIGURATION
# ============================================================

DATA_DIR = "data/target_laws"  # Adjust path for Colab

# Law metadata with Bengali names and exam weight
LAW_CONFIG = {
    "penal_code": {
        "en_file": "penal_code_en.json",
        "bn_file": "penal_code_bn.json",
        "title_en": "The Penal Code, 1860",
        "title_bn": "দণ্ডবিধি, ১৮৬০",
        "act_no": "XLV of 1860",
        "exam_weight": 0.15,
        "priority_sections": [
            # General Exceptions (76-106)
            "76", "79", "80", "81", "82", "83", "84", "85", "86", "87", "88", "89", "90", "91", "92", "96", "97", "99", "100", "101", "102", "103", "104", "105", "106",
            # Abetment (107-120)
            "107", "108", "109", "110", "111", "113", "114", "115", "116", "117", "118", "119", "120",
            # Criminal Conspiracy (120A, 120B)
            "120A", "120B",
            # Offences against State (121-130)
            "121", "121A", "122", "123", "124", "124A",
            # Public Servants (161-171)
            "161", "162", "163", "164", "165", "166", "167", "168", "169", "170", "171",
            # False Evidence (191-229)
            "191", "192", "193", "194", "195", "196", "197", "199", "200", "201", "202", "203", "204", "211", "212",
            # Hurt (319-338)
            "319", "320", "321", "322", "323", "324", "325", "326", "329", "330", "331", "332", "333", "334", "335",
            # Wrongful Restraint/Confinement (339-348)
            "339", "340", "341", "342", "343", "346", "347", "348",
            # Criminal Force (349-358)
            "349", "350", "351", "352", "354", "355",
            # Kidnapping (359-374)
            "359", "360", "361", "362", "363", "364", "365", "366",
            # Theft/Extortion/Robbery (378-402)
            "378", "379", "380", "381", "382", "383", "384", "385", "390", "391", "392", "393", "394", "395", "396", "397", "398", "399", "400", "401", "402",
            # Criminal Breach of Trust (405-409)
            "405", "406", "407", "408", "409",
            # Cheating (415-420)
            "415", "416", "417", "418", "419", "420",
            # Mischief (425-440)
            "425", "426", "427", "428", "429", "430", "431", "435", "436", "437", "438",
            # Criminal Trespass (441-462)
            "441", "442", "443", "445", "446", "447", "448", "449", "450", "451", "452", "453", "454", "456", "457", "458", "459", "460", "461", "462",
            # Defamation (499-502)
            "499", "500", "501", "502",
            # Murder/Culpable Homicide (299-311)
            "299", "300", "301", "302", "303", "304", "304A", "304B", "305", "306", "307", "308",
        ],
    },
    "crpc": {
        "en_file": "crpc_en.json",
        "bn_file": "crpc_bn.json",
        "title_en": "The Code of Criminal Procedure, 1898",
        "title_bn": "ফৌজদারি কার্যবিধি, ১৮৯৮",
        "act_no": "V of 1898",
        "exam_weight": 0.25,
        "priority_sections": [
            "4", "6", "10", "22", "28", "29", "30", "31", "32", "33", "34", "35",
            "54", "55", "57", "59", "61", "127", "128", "129", "130", "131", "132", "133",
            "145", "146", "147", "148", "154", "155", "156", "157", "158", "159", "160",
            "161", "162", "163", "164", "167", "169", "170", "172", "173",
            "190", "191", "192", "193", "195", "196", "197", "198", "199", "200",
            "202", "203", "204", "205", "206", "207", "208", "209", "210",
            "221", "222", "223", "224", "225", "226", "227", "228", "229", "230", "231", "232", "233", "234", "235", "236", "237", "238", "239", "240", "241",
            "242", "243", "244", "245", "246", "247", "248", "249", "250", "251", "252", "253", "254", "255", "256", "257", "258", "259", "260", "261", "262", "263", "264", "265",
            "339", "340", "341", "342", "344", "345", "346", "347", "348", "349", "350",
            "401", "402", "403", "404", "405", "406", "407", "408", "409", "410", "411", "412", "413", "414", "415", "416", "417", "418", "419", "420", "421", "422", "423", "424", "425", "426",
            "435", "436", "437", "438", "439", "439A",
            "476", "477", "478", "479", "480", "481", "482", "483", "484", "485", "486", "487", "488", "489", "490", "491",
            "492", "493", "494", "495", "496", "497", "498",
            "526", "527", "528", "529", "530", "531", "532", "533", "534", "535", "536", "537", "538", "539", "540", "541", "542", "543", "544", "545", "546", "547", "548", "549", "550", "551", "552", "553", "554", "555", "556", "557", "558", "559", "560", "561", "561A",
        ],
    },
    "cpc": {
        "en_file": "cpc_en.json",
        "bn_file": "cpc_bn.json",
        "title_en": "The Code of Civil Procedure, 1908",
        "title_bn": "দেওয়ানি কার্যবিধি, ১৯০৮",
        "act_no": "V of 1908",
        "exam_weight": 0.25,
        "priority_sections": [
            "2", "3", "6", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25",
            "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "60",
            "73", "74", "75", "76", "77", "78", "79", "80", "81", "82", "83", "84", "85", "86", "87", "88", "89", "90", "91", "92", "93", "94", "95", "96", "97", "98", "99", "100", "101", "102", "103", "104", "105", "106", "107", "108", "109", "110", "111", "112", "113", "114", "115",
            "141", "144", "148", "149", "150", "151", "152", "153",
        ],
    },
    "evidence_act": {
        "en_file": "evidence_act_en.json",
        "bn_file": "evidence_act_bn.json",
        "title_en": "The Evidence Act, 1872",
        "title_bn": "সাক্ষ্য আইন, ১৮৭২",
        "act_no": "I of 1872",
        "exam_weight": 0.15,
        "priority_sections": [
            "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17",
            "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32",
            "56", "57", "58", "59", "60", "61", "62", "63", "64", "65", "66", "67",
            "79", "80", "81", "82", "83", "84", "85", "86", "87", "88", "89", "90",
            "101", "102", "103", "104", "105", "106", "107", "108", "109", "110", "111", "112", "113", "114",
            "115", "116", "117", "118", "119", "120",
            "122", "123", "124", "125", "126", "127", "128", "129", "130", "131", "132",
            "133", "134", "135", "136", "137", "138", "139", "140", "141", "142", "143", "144", "145", "146", "147", "148", "149", "150", "151", "152", "153", "154", "155", "156", "157", "158", "159", "160", "161", "162", "163", "164", "165", "166", "167",
        ],
    },
    "limitation_act": {
        "en_file": "limitation_act_en.json",
        "bn_file": "limitation_act_bn.json",
        "title_en": "The Limitation Act, 1908",
        "title_bn": "তামাদি আইন, ১৯০৮",
        "act_no": "IX of 1908",
        "exam_weight": 0.08,
        "priority_sections": [
            "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29",
        ],
    },
    "specific_relief": {
        "en_file": "specific_relief_en.json",
        "bn_file": "specific_relief_bn.json",
        "title_en": "The Specific Relief Act, 1877",
        "title_bn": "সুনির্দিষ্ট প্রতিকার আইন, ১৮৭৭",
        "act_no": "I of 1877",
        "exam_weight": 0.07,
        "priority_sections": [
            "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55", "56",
        ],
    },
}


# ============================================================
# DATA LOADING
# ============================================================

def load_law_data(law_key: str) -> Dict[str, Any]:
    """Load both EN and BN versions of a law."""
    config = LAW_CONFIG[law_key]
    
    en_path = os.path.join(DATA_DIR, config["en_file"])
    bn_path = os.path.join(DATA_DIR, config["bn_file"])
    
    with open(en_path, 'r', encoding='utf-8') as f:
        en_data = json.load(f)
    
    with open(bn_path, 'r', encoding='utf-8') as f:
        bn_data = json.load(f)
    
    return {
        "en": en_data,
        "bn": bn_data,
        "config": config,
    }


def load_all_laws() -> Dict[str, Any]:
    """Load all 6 laws."""
    all_laws = {}
    for key in LAW_CONFIG:
        try:
            all_laws[key] = load_law_data(key)
            print(f"  ✓ Loaded {LAW_CONFIG[key]['title_en']} ({len(all_laws[key]['en']['sections'])} sections)")
        except FileNotFoundError as e:
            print(f"  ✗ Missing: {e}")
    return all_laws


# ============================================================
# RAG CHUNK PREPARATION
# ============================================================

def prepare_rag_chunks(all_laws: Dict) -> List[Dict]:
    """
    Prepare RAG chunks optimized for MCQ generation.
    Each chunk contains:
    - The section text (EN + BN context)
    - Metadata for filtering and retrieval
    """
    chunks = []
    
    for law_key, law_data in all_laws.items():
        config = law_data["config"]
        en_sections = law_data["en"]["sections"]
        bn_sections = law_data["bn"]["sections"]
        
        # Create a BN lookup by section_id
        bn_lookup = {s["section_id"]: s for s in bn_sections}
        
        for en_section in en_sections:
            section_id = en_section["section_id"]
            bn_section = bn_lookup.get(section_id, {})
            
            # Extract section number from title or content
            section_num = ""
            title_text = en_section.get("title", "")
            content_text = en_section.get("content", "")
            
            # Try title first: "299. Culpable homicide" or "4A. Construction"
            title_match = re.match(r'^(\d+[A-Z]?)', title_text.strip())
            if title_match:
                section_num = title_match.group(1)
            else:
                # Try content: starts with section number
                content_match = re.search(r'(?:^|\n)\s*(\d+[A-Z]?)\.\s', content_text[:200])
                if content_match:
                    section_num = content_match.group(1)
            
            # Determine if this is a priority section
            is_priority = section_num in config.get("priority_sections", [])
            
            chunk = {
                "id": f"{law_key}_{section_id}",
                "law_key": law_key,
                "law_title_en": config["title_en"],
                "law_title_bn": config["title_bn"],
                "act_no": config["act_no"],
                "section_id": section_id,
                "section_num": section_num,
                "title": en_section.get("title", ""),
                "content_en": en_section.get("content", ""),
                "content_bn": bn_section.get("content", ""),
                "is_priority": is_priority,
                "exam_weight": config["exam_weight"],
            }
            chunks.append(chunk)
    
    return chunks


def prepare_training_pairs(chunks: List[Dict]) -> List[Dict]:
    """
    Prepare instruction-response training pairs for fine-tuning.
    Format suitable for OpenAI fine-tuning, Gemini, or open-source models.
    """
    training_data = []
    
    for chunk in chunks:
        if not chunk["content_en"].strip():
            continue
        
        # Training pair 1: Section identification
        pair1 = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a Bangladesh Bar Council MCQ generator. Generate questions in Bengali based on authentic Bangladesh law sections."
                },
                {
                    "role": "user",
                    "content": f"Generate a Bar Council MCQ from {chunk['law_title_bn']} based on this section:\n\n{chunk['content_en']}"
                },
                {
                    "role": "assistant",
                    "content": f"[MCQ will be generated based on {chunk['law_title_bn']}, Section {chunk['section_num']}: {chunk['title']}]"
                }
            ],
            "metadata": {
                "law": chunk["law_key"],
                "section": chunk["section_num"],
                "priority": chunk["is_priority"],
            }
        }
        training_data.append(pair1)
    
    return training_data


# ============================================================
# EXPORT FUNCTIONS
# ============================================================

def export_rag_chunks(chunks: List[Dict], output_path: str = "rag_chunks.jsonl"):
    """Export RAG chunks in JSONL format for vector DB ingestion."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    print(f"  Exported {len(chunks)} RAG chunks to {output_path}")


def export_priority_chunks(chunks: List[Dict], output_path: str = "priority_chunks.jsonl"):
    """Export only priority (high-exam-weight) chunks."""
    priority = [c for c in chunks if c["is_priority"]]
    with open(output_path, 'w', encoding='utf-8') as f:
        for chunk in priority:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    print(f"  Exported {len(priority)} priority chunks to {output_path}")


def export_training_data(training_pairs: List[Dict], output_path: str = "training_data.jsonl"):
    """Export training data in JSONL format for fine-tuning."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for pair in training_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + '\n')
    print(f"  Exported {len(training_pairs)} training pairs to {output_path}")


def export_law_text_corpus(all_laws: Dict, output_path: str = "law_corpus.txt"):
    """Export full law text as a plain text corpus for embedding/training."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for law_key, law_data in all_laws.items():
            config = law_data["config"]
            f.write(f"\n{'='*80}\n")
            f.write(f"{config['title_en']} ({config['title_bn']})\n")
            f.write(f"Act No. {config['act_no']}\n")
            f.write(f"{'='*80}\n\n")
            
            for section in law_data["en"]["sections"]:
                f.write(f"\n--- Section: {section['title']} ---\n")
                f.write(section["content"])
                f.write("\n")
    
    file_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Exported law corpus to {output_path} ({file_size:.1f} MB)")


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    print("=" * 70)
    print("  Bangladesh Bar Council MCQ Generator - Data Preparation")
    print("  Laws: 6 | Languages: EN + BN | Source: bdlaws.minlaw.gov.bd")
    print("=" * 70)
    
    # Load all laws
    print("\n📚 Loading law data...")
    all_laws = load_all_laws()
    
    if not all_laws:
        print("ERROR: No law data found. Check DATA_DIR path.")
        return
    
    # Prepare RAG chunks
    print("\n🔧 Preparing RAG chunks...")
    chunks = prepare_rag_chunks(all_laws)
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Priority chunks: {sum(1 for c in chunks if c['is_priority'])}")
    
    # Export files
    print("\n📤 Exporting files...")
    export_rag_chunks(chunks)
    export_priority_chunks(chunks)
    export_law_text_corpus(all_laws)
    
    # Prepare training data
    print("\n🎓 Preparing training data...")
    training_pairs = prepare_training_pairs(chunks)
    export_training_data(training_pairs)
    
    # Summary
    print("\n" + "=" * 70)
    print("  ✅ DATA PREPARATION COMPLETE")
    print("=" * 70)
    print(f"\n  Files generated:")
    print(f"    • rag_chunks.jsonl      - Full RAG database ({len(chunks)} chunks)")
    print(f"    • priority_chunks.jsonl  - Priority sections for focused training")
    print(f"    • training_data.jsonl    - Fine-tuning instruction pairs")
    print(f"    • law_corpus.txt         - Plain text corpus for embeddings")
    print(f"\n  Next steps:")
    print(f"    1. Upload to Colab")
    print(f"    2. Create embeddings (OpenAI/Sentence-Transformers)")
    print(f"    3. Set up vector store (ChromaDB/FAISS/Pinecone)")
    print(f"    4. Connect to LLM with system prompt")
    print(f"    5. Generate MCQs!")


if __name__ == "__main__":
    main()
