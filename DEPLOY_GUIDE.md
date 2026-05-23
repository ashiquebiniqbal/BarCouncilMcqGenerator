# 🚀 Free Deployment Guide — Step by Step

## Option 1: Streamlit Community Cloud (RECOMMENDED — 100% Free)

### Step 1: Create GitHub Account (if you don't have one)
1. Go to [github.com](https://github.com)
2. Click "Sign up"
3. Create your account

### Step 2: Create a New Repository
1. Go to [github.com/new](https://github.com/new)
2. Repository name: `bdlaws-bar-council-mcq`
3. Set to **Public**
4. Click "Create repository"

### Step 3: Upload Your Files
Upload these files to the repository:

```
bdlaws-bar-council-mcq/
├── app.py                    ← Main app file
├── requirements.txt          ← Dependencies
├── .streamlit/
│   └── config.toml          ← Theme config
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
└── README.md
```

**How to upload via GitHub web:**
1. In your repo, click "Add file" → "Upload files"
2. Drag and drop all files
3. For folders, you may need to use Git CLI (see below)

**How to upload via Git CLI:**
```bash
cd c:\Users\anand\Downloads\bdlaws-6laws-rag
git init
git add app.py requirements.txt README.md .streamlit/ data/target_laws/
git commit -m "Initial commit: Bar Council MCQ Generator"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/bdlaws-bar-council-mcq.git
git push -u origin main
```

### Step 4: Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "Sign in with GitHub"
3. Click "New app"
4. Select your repository: `bdlaws-bar-council-mcq`
5. Branch: `main`
6. Main file path: `app.py`
7. Click "Deploy!"

### Step 5: Your App is Live! 🎉
- Your app URL will be: `https://YOUR_APP_NAME.streamlit.app`
- It auto-updates when you push changes to GitHub
- Free forever, no credit card needed

---

## Option 2: Hugging Face Spaces (Also Free)

### Step 1: Create Hugging Face Account
1. Go to [huggingface.co](https://huggingface.co)
2. Sign up

### Step 2: Create a Space
1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Space name: `bdlaws-mcq`
3. SDK: **Streamlit**
4. Click "Create Space"

### Step 3: Upload Files
Upload the same files as above using the web interface or Git.

### Step 4: Done!
Your app will be at: `https://huggingface.co/spaces/YOUR_USERNAME/bdlaws-mcq`

---

## Option 3: Google Cloud Run (Free Tier)

For more advanced deployment with custom domain:

1. Install [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)
2. Create a `Dockerfile`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

3. Deploy:
```bash
gcloud run deploy bdlaws-mcq --source . --allow-unauthenticated
```

---

## Option 4: Render.com (Free Tier)

1. Go to [render.com](https://render.com)
2. Connect GitHub repo
3. Create "Web Service"
4. Build command: `pip install -r requirements.txt`
5. Start command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

---

## 🏆 Recommendation

**Use Streamlit Community Cloud** — it's:
- ✅ 100% free
- ✅ No credit card
- ✅ Auto-deploys from GitHub
- ✅ Custom subdomain (yourapp.streamlit.app)
- ✅ HTTPS included
- ✅ Supports Python 3.12
- ✅ 1GB RAM (enough for this app)

---

## 🔧 Local Testing

Before deploying, test locally:

```bash
cd c:\Users\anand\Downloads\bdlaws-6laws-rag
streamlit run app.py
```

This opens the app at `http://localhost:8501`
