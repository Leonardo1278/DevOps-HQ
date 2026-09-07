# DevOps-HQ

Repositorio académico (Fase 1 — Integración Continua).

Contiene solo el backend FastAPI de LEO HQ. El producto completo (`leoUniverse`) no se publica aquí.

- App: `apps/api`
- Health: `GET /health` (no requiere PostgreSQL)
- Tests de CI: `pytest tests/test_health.py` desde `apps/api`
- Pipeline: `Jenkinsfile` en la raíz (Script Path: `Jenkinsfile`)
- Rama del job: `main`
- No usa PostgreSQL, S3, Cognito ni OpenAI

No commitear `.env` ni secretos.
