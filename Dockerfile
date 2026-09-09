FROM devops-hq-base:1.0

WORKDIR /app

COPY apps/api/app ./app
COPY apps/api/pytest.ini ./pytest.ini
COPY apps/api/tests/__init__.py ./tests/__init__.py
COPY apps/api/tests/test_health.py ./tests/test_health.py

EXPOSE 8000

ENV APP_ENV=development

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
