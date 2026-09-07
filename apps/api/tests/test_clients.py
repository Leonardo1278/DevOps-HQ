import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_clients_sync_and_crud() -> None:
    suffix = uuid.uuid4().hex[:8]
    extra = client.post(
        "/api/v1/projects",
        json={"name": f"Alpahtli {suffix}", "description": "web"},
    ).json()

    synced = client.post("/api/v1/clients/sync-from-projects")
    assert synced.status_code == 200, synced.text
    names = {item["name"] for item in synced.json()["items"]}
    assert f"Alpahtli {suffix}" not in names

    created = client.post(
        "/api/v1/clients",
        json={"name": f"Nuevo {suffix}", "notes": "manual", "project_ids": [extra["id"]]},
    )
    assert created.status_code == 201, created.text
    client_id = created.json()["id"]

    fetched = client.get(f"/api/v1/clients/{client_id}")
    assert fetched.status_code == 200
    assert extra["id"] in [item["id"] for item in fetched.json()["projects"]]

    deleted = client.delete(f"/api/v1/clients/{client_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/clients/{client_id}").status_code == 404
    still = client.get(f"/api/v1/projects/{extra['id']}")
    assert still.status_code == 200
    assert still.json()["id"] == extra["id"]


def test_delete_task_and_idea() -> None:
    suffix = uuid.uuid4().hex[:8]
    project = client.post("/api/v1/projects", json={"name": f"Del {suffix}"}).json()
    task = client.post(
        "/api/v1/tasks",
        json={"title": f"Tarea {suffix}", "project_id": project["id"]},
    ).json()
    idea = client.post(
        "/api/v1/ideas",
        json={"title": f"Idea {suffix}", "project_id": project["id"]},
    ).json()

    assert client.delete(f"/api/v1/tasks/{task['id']}").status_code == 204
    assert client.get(f"/api/v1/tasks/{task['id']}").status_code == 404
    assert client.delete(f"/api/v1/ideas/{idea['id']}").status_code == 204
    assert client.get(f"/api/v1/ideas/{idea['id']}").status_code == 404
