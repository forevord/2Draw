# 2Draw (PaintSnap)

AI-powered paint-by-number generator. Upload a photo → get a segmented canvas, matched paints, and a printable PDF guide.

## Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python 3.11+), uv
- **Database**: Supabase (PostgreSQL)
- **Storage**: Cloudflare R2
- **Payments**: Stripe
- **AI Pipeline**: LangGraph multi-agent
- **Observability**: AgentOps

## Project Structure

```
2Draw/
├── frontend/          # Next.js 14 app
├── backend/           # FastAPI app
├── supabase/          # DB migrations
└── docs/              # Architecture & specs
```

## Issues Board

All 20 issues (PS-01 → PS-20) are tracked in Vibe Kanban.

## Setup

### Prerequisites

- Node.js 20+, npm
- Python 3.11+, [uv](https://docs.astral.sh/uv/) (`pip install uv`)
- A [Supabase](https://supabase.com) project (free tier works)

### 1. Environment Variables

```bash
cp .env.example .env.local      # frontend reads NEXT_PUBLIC_* vars
cp .env.example backend/.env    # backend reads SUPABASE_* vars
```

Fill in real values from your Supabase project settings, Stripe dashboard, etc.

### 2. Database Migration

Run the initial schema in your Supabase SQL editor:

```
supabase/migrations/0001_initial_schema.sql
```

This creates the `jobs` table with Row Level Security enabled.

### 3. Frontend

```bash
cd frontend
npm ci
npm run dev       # http://localhost:3000
```

### 4. Backend

```bash
cd backend
uv venv
uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload   # http://localhost:8000
```

Health check: `curl http://localhost:8000/api/v1/health` → `{"status":"ok"}`

### 5. Tests

```bash
# Frontend
cd frontend && npm test

# Backend
cd backend && uv run pytest -v
```

### Note on uv.lock

`uv.lock` is excluded from git in this scaffold for portability. Once the team is settled on a Python version, commit `uv.lock` for reproducible CI installs (remove it from `.gitignore`).
