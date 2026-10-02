import pytest
from fastapi.testclient import TestClient

from app import db, seed  # noqa: F401  (ensures import path)
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    with TestClient(app) as cl:
        c = db.connect()
        for t in ("assignments", "swap_requests", "load_alerts",
                  "tasks", "members", "weeks", "settings"):
            c.execute(f"DELETE FROM {t}")
        c.commit(); c.close()
        yield cl


def _setup(client):
    client.post("/api/members", json={"name": "阿明", "active": 1, "data_quality": "clean"})
    client.post("/api/members", json={"name": "小雨", "active": 1, "data_quality": "clean"})
    client.post("/api/tasks", json={"title": "扫地", "weight": 3, "data_quality": "clean"})
    client.post("/api/tasks", json={"title": "洗碗", "weight": 1, "data_quality": "clean"})
    # round-robin with 2 members interleaves per slot: m1 always lands on
    # the first task (weight 3 x7 = 21), m2 on the second (weight 1 x7 = 7)
    c = db.connect()
    c.execute("INSERT INTO weeks(label,status) VALUES ('第12周','draft')")
    c.commit(); c.close()


def test_generate_creates_alerts_and_list_detail_agree(client):
    _setup(client)
    r = client.put("/api/settings", json={"load_waterline": 10})
    assert r.status_code == 200

    r = client.post("/api/weeks/1/generate", json={"days": 7})
    assert r.status_code == 200
    alerts = r.json()["alerts"]
    assert alerts, "expected at least one member over line 10"
    for a in alerts:
        assert a["load"] > 10 and a["waterline"] == 10
        assert a["member_name"] and a["week_label"] == "第12周"

    lst = client.get("/api/load-alerts").json()
    assert len(lst) == len(alerts)
    board = client.get("/api/weeks/1/board").json()
    assert len(board["alerts"]) == len(alerts)

    detail = client.get(f"/api/load-alerts/{lst[0]['id']}").json()
    assert detail == lst[0]  # identical pinned fields

    w = client.get("/api/load-alerts", params={"week_id": 1}).json()
    assert len(w) == len(alerts)
    assert client.get("/api/load-alerts", params={"week_id": 999}).json() == []
    assert client.get("/api/load-alerts/9999").status_code == 404


def test_waterline_zero_or_negative_rejected_by_api(client):
    for bad in (0, -3, "abc"):
        r = client.put("/api/settings", json={"load_waterline": bad})
        assert r.status_code == 400, bad
    assert client.get("/api/settings").json().get("load_waterline") is None


def test_setting_change_does_not_refresh_existing_alert(client):
    _setup(client)
    client.put("/api/settings", json={"load_waterline": 10})
    client.post("/api/weeks/1/generate", json={"days": 7})
    before = client.get("/api/load-alerts").json()
    assert before

    client.put("/api/settings", json={"load_waterline": 999})
    after = client.get("/api/load-alerts").json()
    assert after == before  # old snapshot numbers untouched
