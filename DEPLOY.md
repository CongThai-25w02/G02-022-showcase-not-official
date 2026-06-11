# Deploy Guide — AI20K-162 Task Planner

## Local (Docker Compose)

```bash
cp .env.example .env          # fill in GEMINI_API_KEY
docker compose up --build
# => http://localhost:8000
# => /health returns {"ok": true}
```

## Render (1-click deploy)

1. Push repo to GitHub (public or private).
2. Go to https://render.com → "New" → "Web Service" → connect repo.
3. Render auto-detects `render.yaml`.
4. In **Environment** tab, set secrets that are **not** in render.yaml:
   - `GEMINI_API_KEY` — from https://aistudio.google.com/apikey
   - `LANGCHAIN_API_KEY` — from https://smith.langchain.com (for tracing)
5. Click **Deploy**.

## Railway (alternative)

```bash
railway login
railway init
railway up
# Set env vars in Railway dashboard (same list as above)
```

## Environment Variables

| Variable | Required | Notes |
|----------|----------|-------|
| `GEMINI_API_KEY` | Yes | Google AI Studio free key |
| `LANGCHAIN_API_KEY` | No | LangSmith tracing (deliverable #4) |
| `LANGCHAIN_PROJECT` | No | default: `ai20k-162-agent` |
| `LANGCHAIN_TRACING_V2` | No | set `true` to enable tracing |
| `APP_ENV` | No | `production` in prod |
| `MODEL_NAME` | No | default: `gemini-2.0-flash` |
| `MAX_STEPS` | No | default: 40 |
| `MAX_REPLANS` | No | default: 5 |

**NEVER commit `.env` or any file containing real API keys.**
