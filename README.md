# KrishiSetu (working title) — SIH26033

AI-assisted direct agricultural supply-chain coordination platform. **Status: documentation complete; no code written yet** (everything below marked PLANNED until built — see `Memory.md`).

## 1. Project overview

One loop: **PREDICT → MATCH → MOVE → SELL → ANALYSE.** A farmer/FPO lists produce and sees demand intelligence; a buyer's requirement is matched with an explained, scored allocation; confirmed orders are consolidated into optimized routes; every order shows a transparent price breakdown; analytics summarise the chain. Not a generic e-commerce app.

## 2. SIH problem statement

- **ID:** SIH26033 — *Multiple intermediaries reduce farmers earnings and increase consumer prices.*
- **Creator:** Sarim Moin, Ministry of Consumer Affairs, Food & Public Distribution; Ministry of Education's Innovation Cell (MIC). Bucket: Agriculture, FoodTech & Rural Development. Category: Software.
- **Expected solution:** digital marketplace connecting farmers/FPOs with consumers and bulk buyers, logistics support, AI demand forecasting, AI route optimization.
- **Expected benefits:** better farmer prices, lower consumer prices, reduced supply-chain inefficiencies.

## 3. Key features (all PLANNED)

Producer listings with demand forecast panel · buyer requirements · marketplace with landed-price estimates · 7-day LightGBM demand forecast with 80% interval and fallback · explainable matching with partial/multi-source allocation · logistics cost estimates · OR-Tools consolidated route plans with baseline comparison · price transparency waterfall with disclosed assumptions · analytics dashboard.

## 4. Architecture summary

Modular monolith: React/TypeScript SPA ⇄ FastAPI (`/api/v1`) ⇄ SQLite (Postgres-compatible). ML in `backend/ml`, optimization via OR-Tools. One Docker image serves API + SPA. Details: `docs/Architecture.md`.

## 5. Tech stack

React 18, Vite, TypeScript, Tailwind, React Router, TanStack Query, Recharts, Leaflet · FastAPI, SQLAlchemy 2, Pydantic v2, PyJWT, bcrypt · pandas, scikit-learn, LightGBM · OR-Tools · pytest, Vitest. (Pin exact versions at Phase 0.)

## 6. Setup (target commands — verify at Phase 0)

Prerequisites: Python 3.11, Node.js LTS, Git.

```bash
# backend
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
python -m scripts.setup_demo       # creates DB, synthetic data, trains model (or --no-retrain), seeds demo data
uvicorn app.main:app --reload --port 8000

# frontend (second terminal)
cd frontend
npm install
cp .env.example .env
npm run dev                         # http://localhost:5173 (proxies /api to :8000)
```

## 7. Environment variables

Backend (`backend/.env`): `APP_ENV, DEMO_MODE, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, DATABASE_URL, CORS_ORIGINS, APP_TIMEZONE, ROUTING_PROVIDER, OSRM_BASE_URL, OSRM_TIMEOUT_S, ROAD_CIRCUITY_FACTOR, SOLVER_TIME_LIMIT_S, MODEL_DIR, PRICE_SOURCE, AGMARKNET_SNAPSHOT_PATH, DATA_GOV_IN_API_KEY, LOG_LEVEL`. Frontend (`frontend/.env`): `VITE_API_BASE_URL, VITE_DEMO_MODE, VITE_MAP_TILE_URL, VITE_MAP_ATTRIBUTION`. Defaults and meanings: `docs/Architecture.md §17`. Never commit `.env`.

## 8. Run commands

| Task | Command |
|---|---|
| API dev | `uvicorn app.main:app --reload --port 8000` (in `backend/`) |
| Frontend dev | `npm run dev` (in `frontend/`) |
| Backend tests | `pytest -q` |
| Lint | `ruff check .` |
| Frontend build / tests | `npm run build` / `npm run test` |
| Reset demo data | `python -m scripts.setup_demo --no-retrain` or Operator menu → Reset demo data |
| Retrain model | `python -m ml.train` |

## 9. Project structure

```
README.md  Memory.md  AGENTS.md  Dockerfile
docs/      PRD Research Architecture Data ML Rules Phases Design API Testing Demo Execution (.md)
backend/   app/{core,db,schemas,modules/*}  ml/  config/  data/  scripts/  tests/
frontend/  src/{api,components,pages,lib,styles}
```
Full tree: `docs/Architecture.md §3`.

## 10. ML setup

Synthetic demand history (`ml/generate_data.py`, config `backend/config/generator.yaml`) → `ml/train.py` (baselines, LightGBM point/q10/q90, time split, deployment gate) → `backend/ml/artifacts/` + `model_card.json`. **All metrics are on synthetic data and validate the pipeline only.** Details: `docs/ML.md`.

## 11. Data setup

Demo entities and prices are synthetic and flagged (`is_demo`, `is_synthetic`). Optional real prices: download an Agmarknet snapshot from data.gov.in (API key and availability must be verified), place at `backend/data/raw/agmarknet_snapshot.csv`, run `scripts/ingest_agmarknet.py` (NICE, PLANNED), set `PRICE_SOURCE=agmarknet_snapshot`. Details and provenance: `docs/Data.md`.

## 12. API setup

Base path `/api/v1`; interactive docs at `/docs` (FastAPI) once built; contracts in `docs/API.md` (42 endpoints). Demo personas log in via `POST /auth/demo-login` when `DEMO_MODE=true`.

## 13. Testing

`pytest -q` (backend), `npm run test` and `npm run build` (frontend). Acceptance criteria and the append-only execution log: `docs/Testing.md`. No test has been run yet.

## 14. Deployment

Primary: run locally for the demo. Backup: single Docker image (Node build → Python runtime with `libgomp1`), startup runs `python -m scripts.setup_demo --no-retrain`. Free hosting may sleep and lose SQLite on restart; seed is deterministic. See `docs/Architecture.md §15`.

## 15. Limitations

Synthetic demand and prices by default; no payments; no live tracking (manual shipment status); estimated distances unless OSRM enabled; one demo region and five crops; modelled price scenario depends on disclosed assumptions; existing platforms (eNAM, Ninjacart, DeHaat) already cover parts of this space — no uniqueness claim. See `docs/Research.md`.

## 16. Documentation

| Doc | Purpose |
|---|---|
| [PRD](docs/PRD.md) | Requirements and scope |
| [Research](docs/Research.md) | Evidence, competitors, sources |
| [Architecture](docs/Architecture.md) | Stack, modules, deployment |
| [Data](docs/Data.md) | Datasets, schema, seed |
| [ML](docs/ML.md) | Forecast, matching, routing, pricing formulas |
| [Rules](docs/Rules.md) | Project and AI-coding rules |
| [Phases](docs/Phases.md) | Roadmap and 3-day feasibility audit |
| [Design](docs/Design.md) | UI/UX specification |
| [API](docs/API.md) | Endpoint contracts |
| [Testing](docs/Testing.md) | Acceptance criteria and log |
| [Demo](docs/Demo.md) | Judge demo script |
| [Execution](docs/Execution.md) | Developer playbook |
| [Memory](Memory.md) | Permanent project state |
