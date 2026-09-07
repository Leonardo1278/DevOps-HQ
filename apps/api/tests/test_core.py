import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_project_task_idea_activity_flow() -> None:
    suffix = uuid.uuid4().hex[:8]
    name = f"Test Project {suffix}"

    created = client.post("/api/v1/projects", json={"name": name, "description": "demo"})
    assert created.status_code == 201, created.text
    project = created.json()
    project_id = project["id"]
    assert project["status"] == "PLANNING"
    assert project["slug"].startswith("test-project")

    listed = client.get("/api/v1/projects", params={"q": suffix})
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1

    fetched = client.get(f"/api/v1/projects/{project_id}")
    assert fetched.status_code == 200

    patched = client.patch(
        f"/api/v1/projects/{project_id}",
        json={"health": "RISK", "progress_pct": 40},
    )
    assert patched.status_code == 200
    assert patched.json()["health"] == "RISK"

    task = client.post(
        "/api/v1/tasks",
        json={
            "title": f"Task {suffix}",
            "project_id": project_id,
            "priority": "HIGH",
            "checklist": [{"title": "Paso 1", "is_done": False, "sort_order": 0}],
        },
    )
    assert task.status_code == 201, task.text
    task_id = task.json()["id"]
    assert task.json()["checklist_items"][0]["title"] == "Paso 1"

    done = client.post(f"/api/v1/tasks/{task_id}/complete")
    assert done.status_code == 200
    assert done.json()["status"] == "DONE"
    assert done.json()["completed_at"] is not None

    idea = client.post(
        "/api/v1/ideas",
        json={
            "title": f"Idea {suffix}",
            "description": "convert me",
            "project_id": project_id,
            "impact": "HIGH",
            "effort": "LOW",
        },
    )
    assert idea.status_code == 201, idea.text
    idea_id = idea.json()["id"]

    converted = client.post(f"/api/v1/ideas/{idea_id}/convert-to-task")
    assert converted.status_code == 200, converted.text
    body = converted.json()
    assert body["status"] == "CONVERTED"
    assert body["converted_task_id"]

    activity = client.get("/api/v1/activity", params={"project_id": project_id})
    assert activity.status_code == 200
    actions = {item["action"] for item in activity.json()["items"]}
    assert "created" in actions
    assert "completed" in actions
    assert "converted" in actions

    archived = client.delete(f"/api/v1/projects/{project_id}")
    assert archived.status_code == 200
    assert archived.json()["status"] == "ARCHIVED"
    assert archived.json()["archived_at"] is not None

    missing = client.get("/api/v1/projects", params={"q": suffix})
    ids = [item["id"] for item in missing.json()["items"]]
    assert project_id not in ids


def test_project_list_filter_and_sort() -> None:
    suffix = uuid.uuid4().hex[:8]
    active = client.post(
        "/api/v1/projects",
        json={"name": f"AAA {suffix}", "status": "ACTIVE"},
    )
    planning = client.post(
        "/api/v1/projects",
        json={"name": f"ZZZ {suffix}", "status": "PLANNING"},
    )
    assert active.status_code == 201
    assert planning.status_code == 201

    by_name = client.get("/api/v1/projects", params={"q": suffix, "sort": "name"})
    names = [item["name"] for item in by_name.json()["items"]]
    assert names[0].startswith("AAA")
    assert names[-1].startswith("ZZZ")

    only_active = client.get("/api/v1/projects", params={"q": suffix, "status": "ACTIVE"})
    assert {item["status"] for item in only_active.json()["items"]} == {"ACTIVE"}

    planning_first = client.get(
        "/api/v1/projects",
        params={"q": suffix, "sort": "planning_first"},
    )
    assert planning_first.json()["items"][0]["status"] == "PLANNING"

    moved = client.patch(
        f"/api/v1/projects/{planning.json()['id']}",
        json={"status": "ACTIVE"},
    )
    assert moved.status_code == 200
    assert moved.json()["status"] == "ACTIVE"


def test_purge_project_removes_row() -> None:
    suffix = uuid.uuid4().hex[:8]
    created = client.post("/api/v1/projects", json={"name": f"Borrar {suffix}"})
    assert created.status_code == 201
    project_id = created.json()["id"]

    purged = client.post(f"/api/v1/projects/{project_id}/purge")
    assert purged.status_code == 204

    missing = client.get(f"/api/v1/projects/{project_id}")
    assert missing.status_code == 404

    listed = client.get("/api/v1/projects", params={"q": suffix, "include_archived": True})
    assert project_id not in [item["id"] for item in listed.json()["items"]]


def test_unknown_project_404() -> None:
    response = client.get(f"/api/v1/projects/{uuid.uuid4()}")
    assert response.status_code == 404
