"""
⚖️ Bangladesh Bar Council MCQ Generator
Full-featured app with AI MCQ generation, law browsing, analysis.
"""
import streamlit as st
import json
import os
import random
import re
from pathlib import Path

st.set_page_config(
    page_title="বার কাউন্সিল MCQ জেনারেটর",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path("data/target_laws")

LAW_INFO = {
    "penal_code": {"en_file": "penal_code_en.json", "bn_file": "penal_code_bn.json",
        "title_bn": "দণ্ডবিধি, ১৮৬০", "title_en": "The Penal Code, 1860", "icon": "⚔️", "weight": 15},
    "crpc": {"en_file": "crpc_en.json", "bn_file": "crpc_bn.json",
        "title_bn": "ফৌজদারি কার্যবিধি, ১৮৯৮", "title_en": "Code of Criminal Procedure, 1898", "icon": "🔒", "weight": 25},
    "cpc": {"en_file": "cpc_en.json", "bn_file": "cpc_bn.json",
        "title_bn": "দেওয়ানি কার্যবিধি, ১৯০৮", "title_en": "Code of Civil Procedure, 1908", "icon": "📋", "weight": 25},
    "evidence_act": {"en_file": "evidence_act_en.json", "bn_file": "evidence_act_bn.json",
        "title_bn": "সাক্ষ্য আইন, ১৮৭২", "title_en": "The Evidence Act, 1872", "icon": "🔍", "weight": 15},
    "limitation_act": {"en_file": "limitation_act_en.json", "bn_file": "limitation_act_bn.json",
        "title_bn": "তামাদি আইন, ১৯০৮", "title_en": "The Limitation Act, 1908", "icon": "⏰", "weight": 8},
    "specific_relief": {"en_file": "specific_relief_en.json", "bn_file": "specific_relief_bn.json",
        "title_bn": "সুনির্দিষ্ট প্রতিকার আইন, ১৮৭৭", "title_en": "The Specific Relief Act, 1877", "icon": "🛡️", "weight": 7},
    "bar_council": {"en_file": "bar_council_order_en.json", "bn_file": "bar_council_order_bn.json",
        "title_bn": "বার কাউন্সিল আদেশ, ১৯৭২", "title_en": "Legal Practitioners & Bar Council Order, 1972", "icon": "🏛️", "weight": 5},
}

@st.cache_data
def load_all_laws():
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

def search_sections(laws, query, law_filter=None, max_results=10):
    results = []
    query_lower = query.lower()
    query_words = [w for w in query_lower.split() if len(w) > 2]
    for law_key, law_data in laws.items():
        if law_filter and law_key != law_filter:
            continue
        for i, section in enumerate(law_data["en"]["sections"]):
            content = section.get("content", "").lower()
            title = section.get("title", "").lower()
            score = 0
            for word in query_words:
                if word in title: score += 3
                if word in content: score += 1
            if score > 0:
                bn_section = law_data["bn"]["sections"][i] if i < len(law_data["bn"]["sections"]) else {}
                results.append({
                    "law_key": law_key, "law_title": LAW_INFO[law_key]["title_bn"],
                    "title": section["title"], "content_en": section["content"],
                    "content_bn": bn_section.get("content", ""), "score": score,
                })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_results]

def get_random_sections(laws, law_key=None, n=5):
    all_sections = []
    for key, law_data in laws.items():
        if law_key and key != law_key:
            continue
        for i, section in enumerate(law_data["en"]["sections"]):
            if section.get("has_content") and len(section.get("content", "")) > 50:
                bn_sec = law_data["bn"]["sections"][i] if i < len(law_data["bn"]["sections"]) else {}
                all_sections.append({"law_key": key, "law_title": LAW_INFO[key]["title_bn"],
                    "title": section["title"], "content_en": section["content"],
                    "content_bn": bn_sec.get("content", "")})
    return random.sample(all_sections, min(n, len(all_sections)))

def get_ai_client():
    """Get AI client based on selected provider."""
    provider = st.session_state.get("ai_provider", "Gemini")
    api_key = st.session_state.get("ai_api_key", "AIzaSyCFSO1tskcFeaAafCDKkpvADjey2Or04CQ")
    model_name = st.session_state.get("ai_model", "gemini-2.0-flash")
    
    cache_key = f"ai_client_{provider}_{api_key[:8]}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    
    try:
        if provider == "Gemini":
            from google import genai
            client = genai.Client(api_key=api_key)
            st.session_state[cache_key] = ("gemini", client, model_name)
            return ("gemini", client, model_name)
        
        elif provider == "OpenAI / GPT":
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            st.session_state[cache_key] = ("openai", client, model_name)
            return ("openai", client, model_name)
        
        elif provider == "Claude (Anthropic)":
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            st.session_state[cache_key] = ("claude", client, model_name)
            return ("claude", client, model_name)
        
        elif provider == "OpenRouter (Any Model)":
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
            st.session_state[cache_key] = ("openrouter", client, model_name)
            return ("openrouter", client, model_name)
        
        elif provider == "Custom (OpenAI-compatible)":
            from openai import OpenAI
            base_url = st.session_state.get("ai_base_url", "http://localhost:11434/v1")
            client = OpenAI(api_key=api_key or "none", base_url=base_url)
            st.session_state[cache_key] = ("custom", client, model_name)
            return ("custom", client, model_name)
    
    except Exception as e:
        st.session_state["ai_error"] = str(e)
        return None
    return None

def ai_generate(prompt, system_instruction=""):
    """Generate text using the configured AI provider."""
    result = get_ai_client()
    if not result:
        return None
    
    provider_type, client, model_name = result
    full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
    
    try:
        if provider_type == "gemini":
            from google.genai import types
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=4096),
            )
            return response.text
        
        elif provider_type in ("openai", "openrouter", "custom"):
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(
                model=model_name, messages=messages, temperature=0.7, max_tokens=4096,
            )
            return response.choices[0].message.content
        
        elif provider_type == "claude":
            response = client.messages.create(
                model=model_name, max_tokens=4096, temperature=0.7,
                system=system_instruction or "",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
    
    except Exception as e:
        return f"❌ Error: {e}"

SYSTEM_PROMPT = """You are a Bangladesh Bar Council legal examiner AI. You generate MCQs in Bengali for the Advocates' Enrolment Examination.

RULES:
- Generate MCQs ONLY from the law sections provided in context
- Use professional Bengali legal terminology
- Each MCQ: 4 options (ক, খ, গ, ঘ), correct answer, section-based explanation
- NEVER invent sections or legal principles
- Test technical understanding, exceptions, procedural knowledge

FORMAT:
### প্রশ্ন [N]:
(Bengali question)

ক. (option)
খ. (option)
গ. (option)
ঘ. (option)

**সঠিক উত্তর:** (letter)
**ব্যাখ্যা:** (section reference + explanation in Bengali)
"""

# ============================================================
# UI PAGES
# ============================================================

def page_mcq_generator(laws):
    st.markdown("## 📝 AI MCQ জেনারেটর")
    col1, col2, col3 = st.columns(3)
    with col1:
        law_key = st.selectbox("আইন নির্বাচন", list(LAW_INFO.keys()),
            format_func=lambda x: f"{LAW_INFO[x]['icon']} {LAW_INFO[x]['title_bn']}", key="mcq_law")
    with col2:
        topic = st.text_input("বিষয় (Topic)", placeholder="bail, murder, confession, limitation...")
    with col3:
        n_q = st.slider("প্রশ্ন সংখ্যা", 1, 15, 5)
    
    difficulty = st.radio("কঠিনতা", ["সহজ", "মাঝারি", "কঠিন"], horizontal=True)
    
    if st.button("⚡ MCQ তৈরি করুন", type="primary"):
        with st.spinner("AI MCQ তৈরি করছে..."):
            if topic:
                results = search_sections(laws, topic, law_filter=law_key, max_results=8)
            else:
                results = get_random_sections(laws, law_key=law_key, n=8)
            
            context = "\n\n---\n\n".join([
                f"[{r.get('law_title','')}] {r['title']}\n{r['content_en']}" for r in results
            ])
            
            prompt = f"""Based on these authentic Bangladesh law sections, generate {n_q} Bar Council MCQs.
Difficulty: {difficulty}
Topic: {topic or 'General'}

LAW SECTIONS:
{context}

Generate {n_q} MCQs in Bengali now:"""
            
            output = ai_generate(prompt, SYSTEM_PROMPT)
            if output:
                st.markdown("---")
                st.markdown("### 📋 Generated MCQs")
                st.markdown(output)
                st.download_button("📥 Download MCQs", output, file_name="mcqs.md", mime="text/markdown")
            else:
                st.error("AI সংযোগ নেই। Sidebar-এ API key দিন।")

def page_law_browser(laws):
    st.markdown("## 📖 আইনের ধারা ব্রাউজার")
    st.caption("⚠️ এই আইনগুলো ব্রিটিশ আমলে ইংরেজিতে প্রণীত। bdlaws-এ বাংলা অনুবাদ নেই। AI দিয়ে বাংলা ব্যাখ্যা পাবেন।")
    col1, col2 = st.columns([1, 2])
    with col1:
        law_key = st.selectbox("আইন", list(LAW_INFO.keys()),
            format_func=lambda x: f"{LAW_INFO[x]['icon']} {LAW_INFO[x]['title_bn']}", key="browse_law")
        if law_key in laws:
            sections_en = laws[law_key]["en"]["sections"]
            titles = [f"{i+1}. {s['title'][:55]}" for i, s in enumerate(sections_en)]
            idx = st.selectbox(f"ধারা ({len(sections_en)} টি)", range(len(sections_en)),
                format_func=lambda i: titles[i], key="browse_sec")
    with col2:
        if law_key in laws:
            sec_en = sections_en[idx]
            st.markdown(f"**{LAW_INFO[law_key]['title_en']}** | {LAW_INFO[law_key]['title_bn']}")
            st.markdown(f"### {sec_en['title']}")
            tab_en, tab_bn, tab_ai = st.tabs(["📜 মূল আইন (English)", "🇧🇩 বাংলা অনুবাদ (AI)", "🤖 বিশ্লেষণ"])
            with tab_en:
                st.markdown(sec_en["content"])
            with tab_bn:
                if st.button("🇧🇩 বাংলায় অনুবাদ করুন", key=f"translate_{idx}"):
                    with st.spinner("অনুবাদ হচ্ছে..."):
                        prompt = f"""Translate this Bangladesh law section into Bengali (বাংলা).
Keep legal terminology accurate. This is from {LAW_INFO[law_key]['title_en']}.

Section: {sec_en['title']}
{sec_en['content']}

Provide full Bengali translation:"""
                        output = ai_generate(prompt)
                        if output:
                            st.markdown(output)
                        else:
                            st.error("AI সংযোগ নেই।")
            with tab_ai:
                if st.button("📖 সহজ বাংলায় ব্যাখ্যা", key=f"explain_{idx}"):
                    with st.spinner("ব্যাখ্যা তৈরি হচ্ছে..."):
                        prompt = f"""Explain this Bangladesh law section in simple Bengali for a Bar Council exam student.
Include: key points, practical application, common exam questions from this section, and any important exceptions.

Section: {sec_en['title']}
Law: {LAW_INFO[law_key]['title_en']}

Full text:
{sec_en['content']}

Explain in simple Bengali:"""
                        output = ai_generate(prompt)
                        if output:
                            st.markdown(output)
                        else:
                            st.error("AI সংযোগ নেই।")

def page_search(laws):
    st.markdown("## 🔍 আইন অনুসন্ধান")
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("অনুসন্ধান (English keywords)", placeholder="bail, confession, limitation, murder, injunction...")
    with col2:
        law_filter = st.selectbox("ফিল্টার", [None] + list(LAW_INFO.keys()),
            format_func=lambda x: "সকল আইন" if x is None else LAW_INFO[x]["title_bn"], key="search_filter")
    if query:
        results = search_sections(laws, query, law_filter=law_filter, max_results=15)
        if results:
            st.success(f"✅ {len(results)} টি ফলাফল")
            for i, r in enumerate(results):
                with st.expander(f"**{r['law_title']}** — {r['title'][:60]}", expanded=(i < 2)):
                    st.markdown(r["content_en"])
        else:
            st.warning("কোনো ফলাফল পাওয়া যায়নি।")

def page_analyze(laws):
    st.markdown("## 🧠 আইন বিশ্লেষণ (AI)")
    st.markdown("যেকোনো আইনি প্রশ্ন জিজ্ঞাসা করুন — AI উত্তর দেবে আইনের ধারা উল্লেখ করে।")
    
    question = st.text_area("আপনার প্রশ্ন লিখুন", placeholder="যেমন: জামিনের শর্তাবলী কী? ধারা ৩০২ এর শাস্তি কত?", height=100)
    
    if st.button("🧠 বিশ্লেষণ করুন", type="primary"):
        if not question:
            st.warning("প্রশ্ন লিখুন")
            return
        with st.spinner("বিশ্লেষণ চলছে..."):
            # Find relevant sections
            results = search_sections(laws, question, max_results=10)
            context = "\n\n".join([f"[{r['law_title']}] {r['title']}\n{r['content_en']}" for r in results[:8]])
            
            prompt = f"""You are a Bangladesh law expert. Answer this legal question using ONLY the provided law sections.
Answer in Bengali. Cite specific sections.

Question: {question}

Relevant Law Sections:
{context}

Provide a detailed answer in Bengali with section references:"""
            
            output = ai_generate(prompt)
            if output:
                st.markdown("### উত্তর:")
                st.markdown(output)
                with st.expander("📚 প্রাসঙ্গিক ধারাসমূহ"):
                    for r in results[:5]:
                        st.markdown(f"**{r['law_title']}** — {r['title']}")
            else:
                st.error("AI সংযোগ নেই।")

def page_compare(laws):
    st.markdown("## ⚖️ ধারা তুলনা")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ধারা ১")
        law1 = st.selectbox("আইন ১", list(LAW_INFO.keys()),
            format_func=lambda x: LAW_INFO[x]["title_bn"], key="cmp_law1")
        if law1 in laws:
            secs1 = laws[law1]["en"]["sections"]
            idx1 = st.selectbox("ধারা", range(len(secs1)),
                format_func=lambda i: secs1[i]["title"][:50], key="cmp_sec1")
            st.markdown(secs1[idx1]["content"])
    with col2:
        st.markdown("### ধারা ২")
        law2 = st.selectbox("আইন ২", list(LAW_INFO.keys()),
            format_func=lambda x: LAW_INFO[x]["title_bn"], key="cmp_law2")
        if law2 in laws:
            secs2 = laws[law2]["en"]["sections"]
            idx2 = st.selectbox("ধারা", range(len(secs2)),
                format_func=lambda i: secs2[i]["title"][:50], key="cmp_sec2")
            st.markdown(secs2[idx2]["content"])
    
    if st.button("🤖 AI তুলনা করুন"):
        with st.spinner("তুলনা করা হচ্ছে..."):
            s1 = laws[law1]["en"]["sections"][idx1]
            s2 = laws[law2]["en"]["sections"][idx2]
            prompt = f"""Compare these two Bangladesh law sections. Explain similarities, differences, and when each applies.
Answer in Bengali for Bar Council exam preparation.

Section 1: [{LAW_INFO[law1]['title_en']}] {s1['title']}
{s1['content']}

Section 2: [{LAW_INFO[law2]['title_en']}] {s2['title']}
{s2['content']}

Compare in Bengali:"""
            output = ai_generate(prompt)
            if output:
                st.markdown("### তুলনামূলক বিশ্লেষণ:")
                st.markdown(output)

def page_practice(laws):
    st.markdown("## 📚 অনুশীলন মোড")
    col1, col2 = st.columns(2)
    with col1:
        p_law = st.selectbox("আইন", [None] + list(LAW_INFO.keys()),
            format_func=lambda x: "সকল আইন" if x is None else LAW_INFO[x]["title_bn"], key="prac_law")
    with col2:
        n = st.slider("ধারা সংখ্যা", 1, 10, 3)
    if st.button("🔄 নতুন ধারা", key="prac_btn"):
        sections = get_random_sections(laws, law_key=p_law, n=n)
        for i, s in enumerate(sections):
            with st.expander(f"**{s['law_title']}** — {s['title'][:50]}", expanded=True):
                st.markdown(s["content_en"])

# ============================================================
# MAIN
# ============================================================

def main():
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚖️ বার কাউন্সিল MCQ")
        st.markdown("---")
        
        # AI Settings
        st.markdown("### 🔑 AI Settings")
        
        PROVIDERS = ["Gemini", "OpenAI / GPT", "Claude (Anthropic)", "OpenRouter (Any Model)", "Custom (OpenAI-compatible)"]
        DEFAULT_MODELS = {
            "Gemini": "gemini-2.0-flash",
            "OpenAI / GPT": "gpt-4o-mini",
            "Claude (Anthropic)": "claude-sonnet-4-20250514",
            "OpenRouter (Any Model)": "google/gemini-2.0-flash-exp:free",
            "Custom (OpenAI-compatible)": "llama3",
        }
        
        provider = st.selectbox("AI Provider", PROVIDERS, 
            index=PROVIDERS.index(st.session_state.get("ai_provider", "Gemini")),
            key="provider_select")
        st.session_state["ai_provider"] = provider
        
        # API Key
        default_key = "AIzaSyCFSO1tskcFeaAafCDKkpvADjey2Or04CQ" if provider == "Gemini" else ""
        api_key = st.text_input("API Key", type="password", 
            value=st.session_state.get("ai_api_key", default_key),
            key="key_input")
        st.session_state["ai_api_key"] = api_key
        
        # Model name
        model = st.text_input("Model", value=st.session_state.get("ai_model", DEFAULT_MODELS.get(provider, "")),
            key="model_input")
        st.session_state["ai_model"] = model
        
        # Custom base URL for self-hosted
        if provider == "Custom (OpenAI-compatible)":
            base_url = st.text_input("Base URL", 
                value=st.session_state.get("ai_base_url", "http://localhost:11434/v1"),
                key="base_url_input")
            st.session_state["ai_base_url"] = base_url
        
        # Clear cache on settings change
        if st.button("🔄 Connect", key="connect_btn"):
            for k in list(st.session_state.keys()):
                if k.startswith("ai_client_"):
                    del st.session_state[k]
            st.rerun()
        
        # Status
        result = get_ai_client()
        if result:
            st.success(f"✅ {provider} সংযুক্ত")
            st.caption(f"Model: {model}")
        else:
            err = st.session_state.get("ai_error", "")
            if err:
                st.error(f"❌ {err}")
            else:
                st.info("🔄 Connect ক্লিক করুন")
        
        st.markdown("---")
        st.markdown("### 📊 আইন সমূহ")
        laws = load_all_laws()
        total = 0
        for key, info in LAW_INFO.items():
            if key in laws:
                n = len(laws[key]["en"]["sections"])
                total += n
                st.markdown(f"{info['icon']} **{info['title_bn']}** — {n}")
        st.markdown(f"**মোট:** {total} ধারা")
        st.markdown("---")
        st.caption("উৎস: [bdlaws.minlaw.gov.bd](http://bdlaws.minlaw.gov.bd)")
    
    # Header
    st.markdown("""<div style="text-align:center;padding:0.5rem 0">
        <h1>⚖️ বাংলাদেশ বার কাউন্সিল MCQ জেনারেটর</h1>
        <p>Advocates' Enrolment Examination Preparation — 7 Laws | EN + BN | AI-Powered</p>
    </div>""", unsafe_allow_html=True)
    
    if not laws:
        st.error("❌ ডেটা লোড হয়নি।")
        return
    
    # Navigation
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📝 MCQ জেনারেটর", "📖 ধারা ব্রাউজার", "🔍 অনুসন্ধান",
        "🧠 আইন বিশ্লেষণ", "⚖️ তুলনা", "📚 অনুশীলন"
    ])
    
    with tab1: page_mcq_generator(laws)
    with tab2: page_law_browser(laws)
    with tab3: page_search(laws)
    with tab4: page_analyze(laws)
    with tab5: page_compare(laws)
    with tab6: page_practice(laws)
    
    st.markdown("---")
    st.caption("⚠️ শুধুমাত্র শিক্ষামূলক উদ্দেশ্যে। পরীক্ষার প্রস্তুতির জন্য মূল আইন পড়ুন।")

if __name__ == "__main__":
    main()
