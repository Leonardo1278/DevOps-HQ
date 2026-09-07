# DevOps-HQ

Repositorio académico (Fase 1 — Integración Continua).

Contiene solo el backend FastAPI de LEO HQ. El producto completo (`leoUniverse`) no se publica aquí.

- App: `apps/api`
- Health: `GET /health` (no requiere PostgreSQL)
- Tests de CI: `pytest tests/test_health.py` desde `apps/api`

No commitear `.env` ni secretos.
