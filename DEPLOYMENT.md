# Deployment Guide — Multi-Agent AI Platform Backend

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Runtime |
| Docker | 24+ | Container build |
| Railway CLI | latest | Deployment |
| Git | any | Version control |

---

## Step 1 — Collect API Keys (Manual)

You must create accounts and generate keys for each service before deploying.

### OpenRouter (REQUIRED — Central LLM Gateway)
1. Go to https://openrouter.ai/keys
2. Create a new API key
3. Add credits (minimum $5 recommended for testing)
4. Save as `OPENROUTER_API_KEY`

### Supabase (REQUIRED — Auth + Database)
1. Go to https://supabase.com → New project
2. Settings → API → copy:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_ANON_KEY`
   - `service_role` key → `SUPABASE_SERVICE_ROLE_KEY`
   - Settings → API → JWT Secret → `SUPABASE_JWT_SECRET`
3. In Supabase SQL Editor, run `supabase_schema.sql` (in this repo)

### E2B (REQUIRED — Code Sandbox)
1. Go to https://e2b.dev → Sign up
2. Dashboard → API Keys → Create key
3. Save as `E2B_API_KEY`

### Composio (REQUIRED for tool integrations)
1. Go to https://app.composio.dev → Sign up
2. Settings → API Keys → copy key → `COMPOSIO_API_KEY`
3. Connect GitHub: Integrations → GitHub → Connect Account
4. Connect Gmail: Integrations → Gmail → Connect Account

---

## Step 2 — Local Development

```bash
# Clone and enter the directory
cd backend/

# Create virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and fill in all API keys

# Run locally
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs for the Swagger UI (development only).

---

## Step 3 — Deploy to Railway

### 3a — Install Railway CLI
```bash
npm install -g @railway/cli
railway login
```

### 3b — Create project
```bash
# From the backend/ directory
railway init
# Choose: "Empty project" when prompted
```

### 3c — Set environment variables on Railway
```bash
railway variables set OPENROUTER_API_KEY=sk-or-v1-...
railway variables set SUPABASE_URL=https://xxx.supabase.co
railway variables set SUPABASE_ANON_KEY=eyJ...
railway variables set SUPABASE_SERVICE_ROLE_KEY=eyJ...
railway variables set SUPABASE_JWT_SECRET=your-secret
railway variables set E2B_API_KEY=e2b_...
railway variables set COMPOSIO_API_KEY=xxx
railway variables set APP_ENV=production
railway variables set APP_SECRET_KEY=$(openssl rand -hex 32)
railway variables set ALLOWED_ORIGINS=https://your-frontend.vercel.app
railway variables set RATE_LIMIT_PER_MINUTE=20
```

### 3d — Deploy
```bash
railway up
```

Railway will:
1. Detect the `Dockerfile`
2. Build the container
3. Deploy and assign a public URL
4. Run the health check at `/health`

### 3e — Get your public URL
```bash
railway domain
```

---

## Step 4 — Connect Frontend

In your Vercel/Netlify frontend:
1. Set `NEXT_PUBLIC_API_URL` (or equivalent) to your Railway URL
2. All API calls go through this base URL

---

## API Reference

### Authentication
```
POST /auth/signup
Body: { "email": "user@example.com", "password": "SecurePass1" }

POST /auth/login
Body: { "email": "user@example.com", "password": "SecurePass1" }
Response: { "access_token": "...", "refresh_token": "..." }
```

### Task Execution (requires Bearer token)
```
POST /run-task
Authorization: Bearer <access_token>
Body: { "task": "Analyse the market for AI tools in India" }
Response: { "task_id": "uuid", "status": "queued" }

GET /agent-status/{task_id}
Authorization: Bearer <access_token>
Response: { "status": "completed", "result": "..." }
```

### Health Check
```
GET /health
Response: { "status": "ok", "version": "1.0.0" }
```

---

## Architecture Overview

```
Frontend (Vercel/Netlify)
        │
        ▼
FastAPI Backend (Railway)
        │
        ├── /auth/*  ──────────────────▶  Supabase Auth
        │
        ├── /run-task ────────────────▶  CrewAI Crew
        │                                   │
        │                                   ├── Architect Agent
        │                                   ├── Analyst Agent
        │                                   ├── Engineer Agent ──▶ E2B Sandbox
        │                                   └── Writer Agent
        │                                   │
        │                         All LLM calls via OpenRouter
        │                         (Claude, LLaMA, Nemotron, etc.)
        │
        ├── /agent-status/* ──────────▶  In-memory task store
        │
        └── Composio Tools (GitHub, Gmail, etc.)
```

---

## Production Checklist

- [ ] All 5 API keys configured in Railway variables
- [ ] `supabase_schema.sql` executed in Supabase
- [ ] `APP_ENV=production` set (disables /docs endpoint)
- [ ] `APP_SECRET_KEY` is a random 64-char string
- [ ] `ALLOWED_ORIGINS` contains only your frontend domain
- [ ] Supabase email confirmations configured
- [ ] OpenRouter account has sufficient credits
- [ ] Composio GitHub and Gmail connections active
- [ ] E2B account active with valid key
- [ ] Health check returning 200 on Railway
