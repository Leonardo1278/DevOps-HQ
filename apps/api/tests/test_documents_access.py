import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_url_document_and_credential_ref_never_store_secrets() -> None:
    suffix = uuid.uuid4().hex[:8]
    project = client.post("/api/v1/projects", json={"name": f"Files {suffix}"}).json()
    project_id = project["id"]

    created = client.post(
        "/api/v1/documents",
        json={
            "title": f"Brief {suffix}",
            "project_id": project_id,
            "source_type": "URL",
            "source_url": "https://example.com/brief.pdf",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["source_type"] == "URL"
    assert body["storage_key"] is None
    assert "password" not in body

    opened = client.get(f"/api/v1/documents/{body['id']}/url")
    assert opened.status_code == 200
    assert opened.json()["url"] == "https://example.com/brief.pdf"

    listed = client.get("/api/v1/documents", params={"project_id": project_id})
    assert listed.json()["total"] >= 1

    missing_url = client.post(
        "/api/v1/documents",
        json={"title": "x", "source_type": "URL"},
    )
    assert missing_url.status_code == 400

    secret = client.post(
        "/api/v1/credentials",
        json={
            "name": f"RDS {suffix}",
            "kind": "DATABASE",
            "secret_ref": f"arn:aws:secretsmanager:us-east-1:123:secret:leo/{suffix}",
            "project_id": project_id,
            "notes": "Solo el ARN",
        },
    )
    assert secret.status_code == 201, secret.text
    cred = secret.json()
    assert cred["secret_ref"].startswith("arn:aws:secretsmanager")
    assert "password" not in cred
    assert cred["notes"] == "Solo el ARN"

    forbidden = client.post(
        "/api/v1/credentials",
        json={
            "name": "bad",
            "secret_ref": "local/ok",
            "password": "hunter2",
        },
    )
    assert forbidden.status_code == 422

    dumped = client.post(
        "/api/v1/credentials",
        json={"name": "bad2", "secret_ref": "password=hunter2"},
    )
    assert dumped.status_code == 400

    activity = client.get("/api/v1/activity", params={"project_id": project_id})
    summaries = [row["summary"] for row in activity.json()["items"]]
    assert any(f"Brief {suffix}" in row for row in summaries)
    assert any(f"RDS {suffix}" in row for row in summaries)


def test_local_presign_upload_then_create_document() -> None:
    suffix = uuid.uuid4().hex[:8]
    presign = client.post(
        "/api/v1/documents/presign",
        json={"filename": f"nota {suffix}.txt", "content_type": "text/plain"},
    )
    assert presign.status_code == 200, presign.text
    ticket = presign.json()
    key = ticket["storage_key"]
    assert key.startswith("docs/")
    assert ticket["method"] == "PUT"

    uploaded = client.put(
        f"/api/v1/uploads/{key}",
        content=f"hola {suffix}".encode(),
        headers={"Content-Type": "text/plain"},
    )
    assert uploaded.status_code == 204, uploaded.text

    created = client.post(
        "/api/v1/documents",
        json={
            "title": f"Nota {suffix}",
            "source_type": "S3",
            "storage_key": key,
            "content_type": "text/plain",
            "size_bytes": 10,
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["source_type"] == "S3"
    assert created.json()["storage_key"] == key

    link = client.get(f"/api/v1/documents/{created.json()['id']}/url")
    assert link.status_code == 200
    assert "/api/v1/uploads/" in link.json()["url"]

    fetched = client.get(f"/api/v1/uploads/{key}")
    assert fetched.status_code == 200
    assert suffix.encode() in fetched.content
    assert fetched.headers["content-type"].startswith("text/plain")
    assert "inline" in fetched.headers.get("content-disposition", "")

    skipped = client.post(
        "/api/v1/documents",
        json={
            "title": "ghost",
            "source_type": "S3",
            "storage_key": f"docs/{uuid.uuid4()}/missing.txt",
        },
    )
    assert skipped.status_code == 400
