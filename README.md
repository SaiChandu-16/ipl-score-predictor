# 🏏 IPL Score Predictor

Predict IPL innings scores using Playing 12, pitch report, and toss result.
Hosted entirely for **free** using Streamlit Cloud, Render, Supabase, and Hugging Face.

---

## 📁 Project Structure

```
ipl-score-predictor/
│
├── backend/                    ← FastAPI backend (deployed on Render)
│   ├── main.py                 ← App entry point
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── routers/
│       │   ├── predict.py      ← POST /predict
│       │   ├── feedback.py     ← POST /feedback
│       │   └── history.py      ← GET /history
│       ├── models/
│       │   └── schemas.py      ← Pydantic request/response models
│       └── services/
│           ├── model_service.py ← Load model, run predictions
│           └── db_service.py   ← Supabase read/write
│
├── frontend/                   ← Streamlit app (deployed on Streamlit Cloud)
│   ├── app.py
│   └── requirements.txt
│
├── training/                   ← Model training scripts (run locally)
│   ├── prepare_data.py         ← Parse Cricsheet data → CSV
│   ├── train.py                ← Initial training
│   ├── retrain.py              ← Automated retraining (via GitHub Actions)
│   ├── push_model.py           ← Upload model to Hugging Face
│   └── requirements.txt
│
├── database/
│   └── schema.sql              ← Run this in Supabase SQL editor
│
├── .github/workflows/
│   ├── retrain.yml             ← Weekly retraining pipeline
│   ├── deploy.yml              ← Auto-deploy backend on push
│   └── keep_alive.yml          ← Ping API to prevent Render spin-down
│
├── render.yaml                 ← Render deployment config
└── README.md
```

---

## 🚀 Setup Guide (Step by Step)

### Step 1 — Supabase (Database)
1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to **SQL Editor** → paste contents of `database/schema.sql` → Run
4. Copy your **Project URL** and **anon key** from Settings → API

### Step 2 — Train Your First Model (locally)
```bash
# Install training deps
pip install -r training/requirements.txt

# Download IPL data from cricsheet.org/downloads/ipl_csv2.zip
# Unzip into data/raw/

# Prepare dataset
python training/prepare_data.py

# Train model
python training/train.py --data data/ipl_matches.csv

# Push to Hugging Face
# First create a free account at huggingface.co and get a write token
HF_TOKEN=your_token HF_REPO_ID=username/ipl-score-predictor \
    python training/push_model.py
```

### Step 3 — Backend on Render
1. Create a free account at [render.com](https://render.com)
2. New → Web Service → Connect your GitHub repo
3. Render auto-detects `render.yaml`
4. Add environment variables in Render dashboard:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   HF_REPO_ID=username/ipl-score-predictor
   HF_TOKEN=your-hf-token
   ```
5. Copy the **Deploy Hook URL** from Settings → for GitHub Actions
6. Your API will be live at `https://ipl-score-predictor-api.onrender.com`

### Step 4 — Frontend on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repo
3. Set main file: `frontend/app.py`
4. Add secret in dashboard:
   ```toml
   API_URL = "https://ipl-score-predictor-api.onrender.com"
   ```
5. Your app goes live at `your-app.streamlit.app` 🎉

### Step 5 — GitHub Actions Secrets
Add these in your repo → Settings → Secrets → Actions:
```
SUPABASE_URL
SUPABASE_KEY
HF_REPO_ID
HF_TOKEN
RENDER_DEPLOY_HOOK_URL
API_URL
```

---

## 🔁 Retraining Loop

```
User predicts → stored in Supabase
      ↓
Match ends → user submits actual score via app
      ↓
Every Monday (GitHub Actions) → retrain.py runs
      ↓
New model evaluated — only deployed if MAE improves
      ↓
Model pushed to Hugging Face → Render redeploys API
```

---

## 💰 Cost Breakdown

| Service          | Cost         |
|------------------|--------------|
| Streamlit Cloud  | Free forever |
| Render (web svc) | Free tier    |
| Supabase         | Free (500MB) |
| Hugging Face Hub | Free         |
| GitHub Actions   | Free (2000 min/mo) |
| **Total**        | **$0/month** |

---

## 📈 Roadmap

- [ ] Player embeddings (XGBoost → Neural Network)
- [ ] 2nd innings predictor (chase predictor)
- [ ] Live score update integration
- [ ] Season-aware drift detection with Evidently AI
- [ ] User accounts with prediction leaderboard
