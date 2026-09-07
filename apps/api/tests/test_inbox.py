import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_inbox_capture_classify_and_convert() -> None:
    suffix = uuid.uuid4().hex[:8]
    project = client.post("/api/v1/projects", json={"name": f"Inbox {suffix}"}).json()
    project_id = project["id"]

    captured = client.post(
        "/api/v1/inbox",
        json={"content": f"Revisar contrato {suffix}\nDetalle del alcance"},
    )
    assert captured.status_code == 201, captured.text
    item = captured.json()
    item_id = item["id"]
    assert item["item_type"] == "UNKNOWN"
    assert item["processing_status"] == "PENDING"

    classified = client.post(
        f"/api/v1/inbox/{item_id}/classify",
        json={"item_type": "TASK", "project_id": project_id},
    )
    assert classified.status_code == 200, classified.text
    assert classified.json()["item_type"] == "TASK"
    assert classified.json()["processing_status"] == "CLASSIFIED"
    assert classified.json()["project_id"] == project_id

    converted = client.post(f"/api/v1/inbox/{item_id}/convert", json={"to": "task"})
    assert converted.status_code == 200, converted.text
    body = converted.json()
    assert body["processing_status"] == "CONVERTED"
    assert body["converted_entity_type"] == "task"
    assert body["converted_entity_id"]

    task = client.get(f"/api/v1/tasks/{body['converted_entity_id']}")
    assert task.status_code == 200
    assert task.json()["title"] == f"Revisar contrato {suffix}"
    assert task.json()["project_id"] == project_id

    again = client.post(f"/api/v1/inbox/{item_id}/convert", json={"to": "idea"})
    assert again.status_code == 409

    idea_item = client.post(
        "/api/v1/inbox",
        json={"content": f"Línea premium {suffix}", "item_type": "IDEA", "project_id": project_id},
    ).json()
    idea_converted = client.post(
        f"/api/v1/inbox/{idea_item['id']}/convert",
        json={"to": "idea"},
    )
    assert idea_converted.status_code == 200, idea_converted.text
    idea = client.get(f"/api/v1/ideas/{idea_converted.json()['converted_entity_id']}")
    assert idea.status_code == 200
    assert idea.json()["source"] == "inbox"

    note_item = client.post("/api/v1/inbox", json={"content": f"Memo {suffix}"}).json()
    note_converted = client.post(
        f"/api/v1/inbox/{note_item['id']}/convert",
        json={"to": "note", "project_id": project_id},
    )
    assert note_converted.status_code == 200, note_converted.text
    note = client.get(f"/api/v1/notes/{note_converted.json()['converted_entity_id']}")
    assert note.status_code == 200
    assert "Memo" in note.json()["content"]

    open_list = client.get("/api/v1/inbox")
    open_ids = [row["id"] for row in open_list.json()["items"]]
    assert item_id not in open_ids

    all_list = client.get("/api/v1/inbox", params={"include_converted": True})
    all_ids = [row["id"] for row in all_list.json()["items"]]
    assert item_id in all_ids

    activity = client.get("/api/v1/activity", params={"project_id": project_id})
    actions = {row["action"] for row in activity.json()["items"]}
    assert "created" in actions
    assert "classified" in actions
    assert "converted" in actions
