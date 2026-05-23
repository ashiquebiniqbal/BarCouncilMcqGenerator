# ⚖️ Bangladesh Bar Council MCQ Generator

A free, open-source MCQ generation tool for the Bangladesh Bar Council Advocates' Enrolment Examination.

## 🇧🇩 Laws Covered

| # | Law | Sections | Exam Weight |
|---|-----|----------|-------------|
| 1 | দণ্ডবিধি (Penal Code, 1860) | 583 | 15% |
| 2 | ফৌজদারি কার্যবিধি (CrPC, 1898) | 594 | 25% |
| 3 | দেওয়ানি কার্যবিধি (CPC, 1908) | 169 | 25% |
| 4 | সাক্ষ্য আইন (Evidence Act, 1872) | 202 | 15% |
| 5 | তামাদি আইন (Limitation Act, 1908) | 30 | 8% |
| 6 | সুনির্দিষ্ট প্রতিকার আইন (Specific Relief, 1877) | 56 | 7% |

**Total: 3,268 RAG chunks (EN + BN)**

## 📚 Data Source

All law text extracted from the official **Ministry of Law, Justice and Parliamentary Affairs, Bangladesh** website:
- [bdlaws.minlaw.gov.bd](http://bdlaws.minlaw.gov.bd)

## 🚀 Live App

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://bdlaws-mcq.streamlit.app)

## 🛠️ Local Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📁 Project Structure

```
bdlaws-6laws-rag/
├── app.py                          # Streamlit web app
├── requirements.txt                # Python dependencies
├── scrape_bdlaws.py               # Data scraper (re-runnable)
├── colab_mcq_rag_setup.py         # Colab RAG setup
├── bar_council_mcq_system_prompt.md # System prompt for GPT
├── Bangladesh_Bar_Council_MCQ_RAG.ipynb # Colab notebook
├── data/
│   └── target_laws/
│       ├── penal_code_en.json
│       ├── penal_code_bn.json
│       ├── crpc_en.json
│       ├── crpc_bn.json
│       ├── cpc_en.json
│       ├── cpc_bn.json
│       ├── evidence_act_en.json
│       ├── evidence_act_bn.json
│       ├── limitation_act_en.json
│       ├── limitation_act_bn.json
│       ├── specific_relief_en.json
│       ├── specific_relief_bn.json
│       ├── all_laws_rag.json
│       └── summary.json
└── .streamlit/
    └── config.toml
```

## ⚠️ Disclaimer

This tool is for educational purposes only. Always refer to the original Acts for legal accuracy.
