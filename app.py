"""
🇧🇩 Bangladesh Bar Council MCQ Generator
=========================================
Free Streamlit app for generating Bar Council exam MCQs
using RAG from authentic bdlaws.minlaw.gov.bd data.
"""

import streamlit as st
import json
import os
import random
import re
from pathlib import Path

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="বার কাউন্সিল MCQ জেনারেটর",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# DATA LOADING
# ============================================================

DATA_DIR = Path("data/target_laws")

LAW_INFO = {
    "penal_code": {
        "en_file": "penal_code_en.json",
        "bn_file": "penal_code_bn.json",
        "title_bn": "দণ্ডবিধি, ১৮৬০",
        "title_en": "The Penal Code, 1860",
        "icon": "⚔️",
        "weight": 15,
    },
    "crpc": {
        "en_file": "crpc_en.json",
        "bn_file": "crpc_bn.json",
        "title_bn": "ফৌজদারি কার্যবিধি, ১৮৯৮",
        "title_en": "Code of Criminal Procedure, 1898",
        "icon": "🔒",
        "weight": 25,
    },
    "cpc": {
        "en_file": "cpc_en.json",
        "bn_file": "cpc_bn.json",
        "title_bn": "দেওয়ানি কার্যবিধি, ১৯০৮",
        "title_en": "Code of Civil Procedure, 1908",
        "icon": "📋",
        "weight": 25,
    },
    "evidence_act": {
        "en_file": "evidence_act_en.json",
        "bn_file": "evidence_act_bn.json",
        "title_bn": "সাক্ষ্য আইন, ১৮৭২",
        "title_en": "The Evidence Act, 1872",
        "icon": "🔍",
        "weight": 15,
    },
    "limitation_act": {
        "en_file": "limitation_act_en.json",
        "bn_file": "limitation_act_bn.json",
        "title_bn": "তামাদি আইন, ১৯০৮",
        "title_en": "The Limitation Act, 1908",
        "icon": "⏰",
        "weight": 8,
    },
    "specific_relief": {
        "en_file": "specific_relief_en.json",
        "bn_file": "specific_relief_bn.json",
        "title_bn": "সুনির্দিষ্ট প্রতিকার আইন, ১৮৭৭",
        "title_en": "The Specific Relief Act, 1877",
        "icon": "🛡️",
        "weight": 7,
    },
}


@st.cache_data
def load_all_laws():
    """Load all law data from JSON files."""
    laws = {}
    for key, info in LAW_INFO.items():
        en_path = DATA_DIR / info["en_file"]
        bn_path = DATA_DIR / info["bn_file"]
        
        if en_path.exists() and bn_path.exists():
            with open(en_path, 'r', encoding='utf-8') as f:
                en_data = json.load(f)
            with open(bn_path, 'r', encoding='utf-8') as f:
                bn_data = json.load(f)
            laws[key] = {"en": en_data, "bn": bn_data}
    return laws


@st.cache_data
def get_section_index(laws):
    """Build a searchable index of all sections."""
    index = []
    for law_key, law_data in laws.items():
        for section in law_data["en"]["sections"]:
            index.append({
                "law_key": law_key,
                "law_title": LAW_INFO[law_key]["title_bn"],
                "section_id": section["section_id"],
                "title": section["title"],
                "content": section["content"],
            })
    return index


# ============================================================
# MCQ GENERATION (Offline - No API needed)
# ============================================================

def search_sections(laws, query, law_filter=None, max_results=10):
    """Simple keyword search across law sections."""
    results = []
    query_lower = query.lower()
    query_words = query_lower.split()
    
    for law_key, law_data in laws.items():
        if law_filter and law_key != law_filter:
            continue
        
        for section in law_data["en"]["sections"]:
            content = section.get("content", "").lower()
            title = section.get("title", "").lower()
            
            # Score based on keyword matches
            score = 0
            for word in query_words:
                if word in title:
                    score += 3
                if word in content:
                    score += 1
            
            if score > 0:
                results.append({
                    "law_key": law_key,
                    "law_title": LAW_INFO[law_key]["title_bn"],
                    "section_id": section["section_id"],
                    "title": section["title"],
                    "content": section["content"],
                    "score": score,
                })
    
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_results]


def get_random_sections(laws, law_key=None, n=5):
    """Get random sections for MCQ generation."""
    all_sections = []
    for key, law_data in laws.items():
        if law_key and key != law_key:
            continue
        for section in law_data["en"]["sections"]:
            if section.get("has_content") and len(section.get("content", "")) > 50:
                all_sections.append({
                    "law_key": key,
                    "law_title": LAW_INFO[key]["title_bn"],
                    **section,
                })
    
    return random.sample(all_sections, min(n, len(all_sections)))


# ============================================================
# UI COMPONENTS
# ============================================================

def render_sidebar(laws):
    """Render the sidebar with law statistics and filters."""
    st.sidebar.markdown("## ⚖️ আইন নির্বাচন")
    
    # Law statistics
    total_sections = 0
    for key, info in LAW_INFO.items():
        if key in laws:
            n = len(laws[key]["en"]["sections"])
            total_sections += n
            st.sidebar.markdown(f"{info['icon']} **{info['title_bn']}** — {n} ধারা")
    
    st.sidebar.markdown(f"\n---\n**মোট ধারা:** {total_sections}")
    st.sidebar.markdown(f"**উৎস:** [bdlaws.minlaw.gov.bd](http://bdlaws.minlaw.gov.bd)")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 পরীক্ষার ওজন বিন্যাস")
    for key, info in LAW_INFO.items():
        st.sidebar.progress(info["weight"] / 25, text=f"{info['title_bn']}: {info['weight']}%")
    
    return None


def render_section_browser(laws):
    """Section browser tab."""
    st.markdown("### 📖 আইনের ধারা ব্রাউজার")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        selected_law = st.selectbox(
            "আইন নির্বাচন করুন",
            options=list(LAW_INFO.keys()),
            format_func=lambda x: f"{LAW_INFO[x]['icon']} {LAW_INFO[x]['title_bn']}",
        )
        
        if selected_law and selected_law in laws:
            sections = laws[selected_law]["en"]["sections"]
            section_titles = [f"{s['title'][:60]}" for s in sections]
            
            selected_idx = st.selectbox(
                f"ধারা নির্বাচন ({len(sections)} টি)",
                options=range(len(sections)),
                format_func=lambda i: section_titles[i],
            )
    
    with col2:
        if selected_law and selected_law in laws:
            section = laws[selected_law]["en"]["sections"][selected_idx]
            bn_sections = laws[selected_law]["bn"]["sections"]
            bn_section = bn_sections[selected_idx] if selected_idx < len(bn_sections) else None
            
            st.markdown(f"**{LAW_INFO[selected_law]['title_en']}**")
            st.markdown(f"#### {section['title']}")
            
            tab_en, tab_bn = st.tabs(["🇬🇧 English", "🇧🇩 বাংলা"])
            
            with tab_en:
                st.text_area("English Text", section["content"], height=300, disabled=True)
            
            with tab_bn:
                if bn_section:
                    st.text_area("Bengali Text", bn_section["content"], height=300, disabled=True)


def render_search(laws):
    """Search tab."""
    st.markdown("### 🔍 আইন অনুসন্ধান")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("অনুসন্ধান করুন (English keywords)", placeholder="e.g., bail, murder, confession, limitation")
    with col2:
        law_filter = st.selectbox(
            "আইন ফিল্টার",
            options=[None] + list(LAW_INFO.keys()),
            format_func=lambda x: "সকল আইন" if x is None else LAW_INFO[x]["title_bn"],
        )
    
    if query:
        results = search_sections(laws, query, law_filter=law_filter)
        
        if results:
            st.success(f"✅ {len(results)} টি ফলাফল পাওয়া গেছে")
            
            for i, result in enumerate(results):
                with st.expander(f"**{result['law_title']}** — {result['title'][:60]}", expanded=(i == 0)):
                    st.markdown(f"**Section ID:** {result['section_id']}")
                    st.text_area(f"Content_{i}", result["content"], height=200, disabled=True, key=f"search_{i}")
        else:
            st.warning("কোনো ফলাফল পাওয়া যায়নি। অন্য keyword ব্যবহার করুন।")


def render_mcq_generator(laws):
    """MCQ Generator tab - generates context for LLM-based MCQ creation."""
    st.markdown("### 📝 MCQ জেনারেটর")
    
    st.info("💡 এই টুলটি আপনাকে MCQ তৈরির জন্য প্রাসঙ্গিক ধারা প্রদান করে। আপনি এই context ব্যবহার করে ChatGPT/Gemini-তে MCQ তৈরি করতে পারেন।")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        mcq_law = st.selectbox(
            "আইন",
            options=list(LAW_INFO.keys()),
            format_func=lambda x: f"{LAW_INFO[x]['icon']} {LAW_INFO[x]['title_bn']}",
            key="mcq_law",
        )
    
    with col2:
        mcq_topic = st.text_input("বিষয় (Topic)", placeholder="e.g., bail, confession, res judicata")
    
    with col3:
        mcq_difficulty = st.selectbox("কঠিনতা", ["সহজ (Easy)", "মাঝারি (Medium)", "কঠিন (Hard)"])
    
    n_questions = st.slider("প্রশ্ন সংখ্যা", 1, 20, 5)
    
    if st.button("🎯 MCQ Context তৈরি করুন", type="primary"):
        if mcq_topic:
            results = search_sections(laws, mcq_topic, law_filter=mcq_law, max_results=8)
        else:
            results = [{"content": s["content"], "title": s["title"], "law_title": LAW_INFO[mcq_law]["title_bn"]} 
                      for s in get_random_sections(laws, law_key=mcq_law, n=8)]
        
        if results:
            # Build the prompt
            context_text = "\n\n---\n\n".join([
                f"[{r.get('law_title', '')}] {r['title']}\n{r['content']}" 
                for r in results
            ])
            
            difficulty_map = {
                "সহজ (Easy)": "easy",
                "মাঝারি (Medium)": "medium", 
                "কঠিন (Hard)": "hard",
            }
            
            prompt = f"""You are a Bangladesh Bar Council MCQ examiner. Generate {n_questions} MCQs in Bengali.

RULES:
- Use ONLY the law sections provided below
- Each MCQ must have 4 options (ক, খ, গ, ঘ)
- Provide correct answer and section-based explanation
- Difficulty: {difficulty_map.get(mcq_difficulty, 'medium')}
- Use professional Bengali legal terminology
- NEVER invent sections

FORMAT for each question:
### প্রশ্ন [number]:
(Bengali question)

ক. (option)
খ. (option)
গ. (option)
ঘ. (option)

সঠিক উত্তর: (letter)
ব্যাখ্যা: (section reference + explanation)

---

LAW SECTIONS (CONTEXT):

{context_text}

Generate {n_questions} MCQs now:"""
            
            st.markdown("---")
            st.markdown("#### 📋 Generated Prompt (Copy to ChatGPT/Gemini)")
            st.text_area(
                "Copy this prompt to your AI assistant",
                prompt,
                height=400,
                key="generated_prompt",
            )
            
            # Copy button
            st.markdown("**ব্যবহার পদ্ধতি:**")
            st.markdown("""
1. উপরের prompt কপি করুন
2. [ChatGPT](https://chat.openai.com) বা [Gemini](https://gemini.google.com) এ পেস্ট করুন
3. AI আপনাকে সঠিক MCQ তৈরি করে দেবে
            """)
        else:
            st.warning("প্রাসঙ্গিক ধারা পাওয়া যায়নি। অন্য topic ব্যবহার করুন।")


def render_practice_mode(laws):
    """Practice mode - show random sections for self-study."""
    st.markdown("### 📚 অনুশীলন মোড")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        practice_law = st.selectbox(
            "আইন",
            options=[None] + list(LAW_INFO.keys()),
            format_func=lambda x: "সকল আইন (Random)" if x is None else LAW_INFO[x]["title_bn"],
            key="practice_law",
        )
    with col2:
        n_sections = st.slider("ধারা সংখ্যা", 1, 10, 3, key="practice_n")
    
    if st.button("🔄 নতুন ধারা দেখান", key="practice_btn"):
        sections = get_random_sections(laws, law_key=practice_law, n=n_sections)
        
        for i, section in enumerate(sections):
            with st.expander(f"**{section['law_title']}** — {section['title'][:50]}", expanded=True):
                st.markdown(section["content"])


def render_api_mode(laws):
    """API-connected MCQ generation (requires API key)."""
    st.markdown("### 🤖 AI MCQ জেনারেটর (API)")
    
    st.warning("⚠️ এই ফিচারটি ব্যবহার করতে OpenAI বা Google Gemini API key প্রয়োজন।")
    
    api_provider = st.radio("AI Provider", ["OpenAI (GPT-4o)", "Google Gemini (Free)"], horizontal=True)
    api_key = st.text_input("API Key", type="password", placeholder="আপনার API key দিন")
    
    if not api_key:
        st.info("💡 বিনামূল্যে ব্যবহার করতে Google Gemini API key ব্যবহার করুন: [Get Free Key](https://aistudio.google.com/apikey)")
        return
    
    col1, col2, col3 = st.columns(3)
    with col1:
        api_law = st.selectbox(
            "আইন",
            options=list(LAW_INFO.keys()),
            format_func=lambda x: LAW_INFO[x]["title_bn"],
            key="api_law",
        )
    with col2:
        api_topic = st.text_input("বিষয়", key="api_topic", placeholder="bail, murder, etc.")
    with col3:
        api_n = st.number_input("প্রশ্ন সংখ্যা", 1, 10, 5, key="api_n")
    
    if st.button("⚡ MCQ তৈরি করুন", type="primary", key="api_generate"):
        with st.spinner("MCQ তৈরি হচ্ছে..."):
            # Get context
            if api_topic:
                results = search_sections(laws, api_topic, law_filter=api_law, max_results=8)
            else:
                results = [{"content": s["content"], "title": s["title"]} 
                          for s in get_random_sections(laws, law_key=api_law, n=8)]
            
            context = "\n\n".join([f"{r['title']}\n{r['content']}" for r in results])
            
            system_msg = """You are a Bangladesh Bar Council MCQ examiner. Generate MCQs in Bengali.
Rules: Use ONLY provided sections. 4 options (ক,খ,গ,ঘ). Provide answer + explanation with section reference."""
            
            user_msg = f"""Generate {api_n} Bar Council MCQs from these sections:

{context}

Output in Bengali with proper legal terminology."""
            
            try:
                if "OpenAI" in api_provider:
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key)
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": user_msg},
                        ],
                        temperature=0.7,
                    )
                    output = response.choices[0].message.content
                else:
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(f"{system_msg}\n\n{user_msg}")
                    output = response.text
                
                st.markdown("---")
                st.markdown("### 📝 Generated MCQs")
                st.markdown(output)
                
            except Exception as e:
                st.error(f"Error: {e}")


# ============================================================
# MAIN APP
# ============================================================

def main():
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h1>⚖️ বাংলাদেশ বার কাউন্সিল MCQ জেনারেটর</h1>
        <p style="font-size: 1.1rem; color: #666;">
            Bangladesh Bar Council Advocates' Enrolment Examination Preparation
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    laws = load_all_laws()
    
    if not laws:
        st.error("❌ আইনের ডেটা লোড করা যায়নি। data/target_laws/ ফোল্ডার চেক করুন।")
        return
    
    # Sidebar
    render_sidebar(laws)
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 MCQ জেনারেটর",
        "🤖 AI MCQ (API)",
        "📖 ধারা ব্রাউজার",
        "🔍 অনুসন্ধান",
        "📚 অনুশীলন",
    ])
    
    with tab1:
        render_mcq_generator(laws)
    
    with tab2:
        render_api_mode(laws)
    
    with tab3:
        render_section_browser(laws)
    
    with tab4:
        render_search(laws)
    
    with tab5:
        render_practice_mode(laws)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888; font-size: 0.85rem;">
        <p>📚 উৎস: Ministry of Law, Justice and Parliamentary Affairs, Bangladesh | 
        <a href="http://bdlaws.minlaw.gov.bd">bdlaws.minlaw.gov.bd</a></p>
        <p>⚠️ এই অ্যাপটি শুধুমাত্র শিক্ষামূলক উদ্দেশ্যে। পরীক্ষার প্রস্তুতির জন্য মূল আইন পড়ুন।</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
