# Teacher Command Center — Development Contract

## 1. Locked Environment Baselines
* **Python Runtime:** 3.12.10 (Managed exclusively via \uv\)
* **Node Runtime:** 22.23.3 (Managed exclusively via \nm\ & \pnpm\)
* **API Versioning:** \/api/v1\
* **Database:** PostgreSQL 16 + pgvector
* **Cache & Broker:** Redis 7.x
* **Object Store:** MinIO (Local S3 API)

## 2. Port Allocations
* Next.js (Frontend): \3000\
* FastAPI (Backend): \8000\
* PostgreSQL: \5432\
* Redis: \6379\
* MinIO API: \9000\
* MinIO Web Console: \9001\

## 3. Directory Ownership
* **Backend Owner:** Exclusive control over \ackend/\, \knowledge/\, \evaluation/\, \infrastructure/\, and root infrastructure files.
* **Frontend Owner:** Exclusive control over \rontend/\ and UI mock layers.
* **Shared Communication:** Cross-boundary interactions occur strictly via OpenAPI schemas (\/api/v1\).

## 4. Strict Non-Negotiable Rules
1. Never commit \.env\, \.venv/\, or \
ode_modules/\.
2. Never install packages without committing the corresponding lockfile (\uv.lock\ or \pnpm-lock.yaml\).
3. Database changes must happen exclusively via Alembic migrations.
4. The frontend must never query LLM providers or databases directly; all calls go through FastAPI.
5. All feature development occurs on feature branches merged into \develop\ via PR. Never commit directly to \main\.
