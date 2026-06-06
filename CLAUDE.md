# 房价预测系统 (House Price Prediction System)

> Full-stack web app with data ingestion, XGBoost-based ML prediction, and interactive visualization.

## Quick Facts

- **Stack**: Django 4.2, DRF, PostgreSQL 14, XGBoost, Scikit-learn | Vue 3, Vite 8, TypeScript, Element Plus, ECharts 6, Pinia 3
- **Backend Run**: `cd backend && uv run python manage.py runserver`
- **Frontend Run**: `cd frontend && npm run dev`
- **ML Train**: `cd backend && uv run python ml/train.py`
- **Lint (Backend)**: `cd backend && uv run python -m flake8` (if configured)
- **Lint (Frontend)**: `cd frontend && npx vue-tsc --noEmit`
- **Build**: `cd frontend && npm run build`
- **Test**: `cd backend && uv run python manage.py test`

## Key Directories

- `backend/config/` — Django settings (split dev/prod)
- `backend/users/` — Custom user model + JWT auth
- `backend/houses/` — House data model + CRUD API
- `backend/prediction/` — Prediction API, model service, SHAP explainability, versioning
- `backend/ml/` — Feature engineering, training script, model persistence
- `backend/crawler/` — Data crawler module
- `frontend/src/api/` — Axios wrapper + API methods (index.ts)
- `frontend/src/views/` — Page-level views (Home, Predict, Charts, Map, Houses, Login, Profile, EnterpriseDashboard)
- `frontend/src/store/` — Pinia state management
- `frontend/src/utils/` — AMap init, Axios instance
- `docs/` — Task specs and documentation

## Code Style

- Backend: PEP 8, use `snake_case` for variables/functions, `PascalCase` for classes
- Frontend: Vue style guide, TypeScript strict, `<script setup>` + Composition API
- No `any` types in TypeScript — use proper interfaces or `unknown`
- Use early returns, avoid deeply nested conditionals
- Prefer composition over inheritance

## Git Conventions

- **Branch naming**: `{type}/{description}` (e.g., `feat/predict-page`, `fix/cors-error`)
- **Commit format**: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`)
- **PR titles**: Same as commit format

## Critical Rules

### Task Execution
- Tasks T001→T026 MUST be completed sequentially — each is a prerequisite for the next
- Never skip steps; fix failures before continuing
- See `docs/TASKS.md` for the full task breakdown

### Python Environment
- All Python operations use `uv` — never `pip`, `venv`, or bare `python`
- Install: `uv sync` or `uv pip install <package>`
- Run: `uv run python manage.py <command>`
- Train: `uv run python ml/train.py`

### Code Search
- Always use `rg` (ripgrep) for code search in Bash — never `grep` or `find` for searching file contents
- Example: `rg "class House" backend/` instead of `grep -r "class House" backend/`
- The built-in Grep tool already uses ripgrep internally

### Environment Variables
- NEVER hardcode API keys or secrets in source code
- All keys must come from env files (`backend/.env`, `frontend/.env`)
- Frontend env vars require `VITE_` prefix (e.g., `VITE_AMAP_KEY`, `VITE_API_BASE_URL`)
- Backend reads via `os.environ.get()` with `python-dotenv`
- Never commit `.env` files — only `.env.example`
- NEVER read `.env` files — they contain secrets; use `.env.example` for reference

### Error Handling
- NEVER swallow errors silently
- Backend: raise proper DRF exceptions with user-friendly messages
- Frontend: always show ElMessage feedback on errors
- Every API call needs error handling

### API Design
- All endpoints use trailing slashes (e.g., `/api/prediction/predict/`)
- Protected endpoints require JWT authentication
- Pagination on all list endpoints (default 20 per page)

### ML Pipeline
- Feature engineering (`ml/features.py`) → clean DataFrame with no nulls
- Training (`ml/train.py`) → XGBoost with cross-validation
- Model persistence → joblib to `ml/models/house_price.pkl`
- Model loads at app startup via `prediction/service.py`
- Model versioning via `prediction/versioning.py`

## API Endpoints

- Auth: `POST /api/auth/register|login|logout|refresh`, `GET /api/auth/me` (JWT via simplejwt)
- Houses: `GET/POST /api/houses/`, `GET/PUT/DELETE /api/houses/{id}/`
- Prediction:
  - `POST /api/prediction/predict/` — `{area, rooms, year, district}` → `{predicted_price, confidence, feature_importance}`
  - `GET /api/prediction/model-info/` — current model metadata
  - `POST /api/prediction/explain/` — SHAP-based prediction explanation
  - `GET /api/prediction/versions/` — model version list
  - `GET /api/prediction/versions/current/` — current model version
  - `POST /api/prediction/versions/rollback/` — rollback to a previous version

## Common Commands

```bash
# Backend
cd backend
uv sync                                    # Install dependencies
uv run python manage.py migrate            # Run migrations
uv run python manage.py runserver          # Start dev server
uv run python manage.py createsuperuser    # Create admin user
uv run python ml/import_data.py            # Import CSV data into PostgreSQL
uv run python ml/train.py                  # Train XGBoost model → ml/models/

# Frontend
cd frontend
npm install
npm run dev                   # Vite dev server with HMR
npm run build                 # Production build
npx vue-tsc --noEmit          # Type check

# Docker
docker-compose up -d          # Start all services
docker-compose logs -f        # View logs
```

## Architecture Decisions

- **Django settings split** — `config/settings/` has separate dev (SQLite) and production (PostgreSQL) configs
- **User model** — extends `AbstractUser` with `phone`, `avatar`, `created_at`, `updated_at`
- **Frontend API layer** — Axios instance in `src/api/index.ts` auto-attaches JWT token; response interceptor checks `res.code !== 200` and shows ElMessage
- **Map integration** — AMap (高德地图) API for property markers and heatmap; key via `VITE_AMAP_KEY`
