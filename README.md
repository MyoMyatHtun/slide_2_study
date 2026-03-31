# Slide2Study

Slide2Study is a full-stack app that extracts text from lecture PDFs and generates study summaries.

## Hybrid Deployment (Railway + Hugging Face)

This project is configured for a hybrid architecture:

1. Railway hosts the app (FastAPI backend + React frontend).
2. Hugging Face hosts the summarization model (`dxskywalker/s2s_summarizer`).
3. FastAPI calls Hugging Face Inference API using `HF_TOKEN`.

This avoids deploying a 1.5 GB model directly on low-memory free-tier hosts.

## Local Development

### Frontend

```bash
npm install
npm run dev
```

Optional frontend env (`.env` in project root):

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend environment variables:

```env
HF_TOKEN=your_huggingface_token
HF_MODEL_ID=dxskywalker/s2s_summarizer
HF_TIMEOUT_SECONDS=90
CORS_ORIGINS=http://localhost:5173
```

Health check endpoint:

```txt
GET /health
```

## Railway Deployment

Create two Railway services (recommended):

1. `slide2study-backend` (root directory: `backend`)
2. `slide2study-frontend` (root directory: project root)

### Backend service settings

1. Root directory: `backend`
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Variables:
   - `HF_TOKEN`
   - `HF_MODEL_ID=dxskywalker/s2s_summarizer`
   - `HF_TIMEOUT_SECONDS=90`
   - `CORS_ORIGINS=https://<your-frontend-domain>`

### Frontend service settings

1. Build command: `npm ci && npm run build`
2. Start command: `npm run preview -- --host 0.0.0.0 --port $PORT`
3. Variable:
   - `VITE_API_BASE_URL=https://<your-backend-domain>`

## Hugging Face Model Upload

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://hf.co/cli/install.ps1 | iex"
hf auth login
hf upload dxskywalker/s2s_summarizer .
```
