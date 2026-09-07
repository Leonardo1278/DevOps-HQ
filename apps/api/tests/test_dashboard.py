import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_aggregates_open_work() -> None:
    suffix = uuid.uuid4().hex[:8]
    project = client.post(
        "/api/v1/projects",
        json={
            "name": f"Dash {suffix}",
            "description": "Pulso de prueba",
            "status": "ACTIVE",
            "health": "RISK",
            "progress_pct": 22,
            "color": "#f97316",
            "icon": "D",
        },
    )
    assert project.status_code == 201, project.text
    project_id = project.json()["id"]

    urgent = client.post(
        "/api/v1/tasks",
        json={
            "title": f"Urgente {suffix}",
            "project_id": project_id,
            "priority": "URGENT",
            "status": "TODO",
        },
    )
    assert urgent.status_code == 201, urgent.text

    done = client.post(
        "/api/v1/tasks",
        json={
            "title": f"Hecha {suffix}",
            "project_id": project_id,
            "priority": "HIGH",
            "status": "TODO",
        },
    )
    assert done.status_code == 201, done.text
    completed = client.post(f"/api/v1/tasks/{done.json()['id']}/complete")
    assert completed.status_code == 200

    for index in range(6):
        created = client.post(
            "/api/v1/tasks",
            json={
                "title": f"Extra {index} {suffix}",
                "project_id": project_id,
                "priority": "LOW",
            },
        )
        assert created.status_code == 201, created.text

    capture = client.post(
        "/api/v1/inbox",
        json={"content": f"Captura dashboard {suffix}", "project_id": project_id},
    )
    assert capture.status_code == 201, capture.text
    capture_id = capture.json()["id"]

    converted = client.post(
        "/api/v1/inbox",
        json={"content": f"Ya convertida {suffix}", "project_id": project_id},
    ).json()
    converted_ok = client.post(f"/api/v1/inbox/{converted['id']}/convert", json={"to": "note"})
    assert converted_ok.status_code == 200, converted_ok.text

    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200, response.text
    body = response.json()

    kpis = body["kpis"]
    assert kpis["pending_tasks"] >= 7
    assert kpis["urgent_tasks"] >= 1
    assert kpis["active_projects"] >= 1
    assert kpis["receivable_amount"] is None

    today = body["today_tasks"]
    assert len(today) <= 5
    titles = [task["title"] for task in today]
    assert f"Urgente {suffix}" in titles
    assert f"Hecha {suffix}" not in titles
    nested = next(task for task in today if task["title"] == f"Urgente {suffix}")
    assert nested["project"]["id"] == project_id
    assert nested["project"]["name"] == f"Dash {suffix}"

    pulse_ids = [row["id"] for row in body["project_pulse"]]
    assert project_id in pulse_ids
    assert len(body["project_pulse"]) <= 8

    capture_ids = [row["id"] for row in body["recent_captures"]]
    capture_contents = [row["content"] for row in body["recent_captures"]]
    assert capture_id in capture_ids
    assert f"Captura dashboard {suffix}" in capture_contents
    assert f"Ya convertida {suffix}" not in capture_contents
    assert len(body["recent_captures"]) <= 5

    summaries = [row["summary"] for row in body["recent_activity"]]
    assert any(suffix in summary for summary in summaries)
    assert len(body["recent_activity"]) <= 6
