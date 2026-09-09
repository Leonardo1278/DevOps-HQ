# DevOps-HQ

**Fase 1 — Integración continua**  
Escuela Bancaria y Comercial (EBC) · Leonardo Cueto  
Repositorio: [Leonardo1278/DevOps-HQ](https://github.com/Leonardo1278/DevOps-HQ) · rama `main`

---

## Video de evidencia (cualquiera con el vínculo)

El video **no está en este repo** (pesa ~87 MB y rompería el checkout de Jenkins).

**Carpeta de evidencias (Drive, acceso con el vínculo):**

### https://drive.google.com/drive/folders/15YBh3UyllQR5nsIlMRSkGaKOSePxA5Sk?usp=sharing

Ahí está `video_fase1` y las capturas: un `git push` a `main` crea un build en Jenkins **sin** pulsar *Construir ahora*.

---

## Qué es esto

Extracto académico del backend **FastAPI** de LEO HQ. Sirve para demostrar CI con **GitHub + Jenkins + AWS EC2**.

No es el producto completo (`leoUniverse`). Aquí no hay frontend, Postgres, S3, Cognito ni OpenAI.

| Pieza | Detalle |
|---|---|
| App | `apps/api` |
| Health (sin DB) | `GET /health` → `status`, `env`, `service` |
| Test de CI | `pytest tests/test_health.py` |
| Pipeline | `Jenkinsfile` en la raíz (Script Path: `Jenkinsfile`) |
| Job Jenkins | `devops-hq-ci` |
| Trigger | webhook de GitHub (`/github-webhook/`) |

## Qué hace el pipeline

1. Checkout de `main`
2. Detecta `python3.11` o `python3`
3. Crea un virtualenv en `apps/api`
4. Instala `requirements-dev.txt`
5. Corre solo el health check (la suite completa necesita PostgreSQL)
6. Importa `app.main` para validar FastAPI
7. Borra el virtualenv

## Cómo probar el health en local

```bash
cd apps/api
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest tests/test_health.py -q
```

```bash
uvicorn app.main:app --reload --port 8000
# otro terminal
curl http://127.0.0.1:8000/health
```

## Infra (práctica)

- Región AWS: `us-east-1`
- Instancia: `devops-hq-jenkins` (`t3.small`, Ubuntu)
- Jenkins LTS 2.568.3 en el puerto `8080`
- Definition: *Pipeline script from SCM* → Git → `*/main` → `Jenkinsfile`

La IP pública cambia si se apaga y enciende la EC2; hay que actualizar el webhook.

## Seguridad

No commitear `.env`, tokens, `.pem` ni el video. Este `.gitignore` ya excluye secretos y virtualenvs.

Fases 2 y 3 del curso (Docker, Terraform) no forman parte de este entregable.
