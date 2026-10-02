import pytest

from app import db, seed
from app.modules.load_alert import rebuild_week_alerts, list_alerts, get_alert
from app.modules.settings_store import put as put_settings, SettingsError, get_waterline


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    seed.init_db()
    c = db.connect()
    for t in ("assignments", "swap_requests", "load_alerts",
              "tasks", "members", "weeks", "settings"):
        c.execute(f"DELETE FROM {t}")
    c.commit()
    yield c
    c.close()


def _seed_week(c):
    """Week with: m1 load 6 (weight-3 task x2), m2 load 1 (weight-1 task)."""
    c.execute("INSERT INTO weeks(id,label,status) VALUES (1,'第12周','ready')")
    c.execute("INSERT INTO members(id,name,active,data_quality) VALUES (1,'阿明',1,'clean')")
    c.execute("INSERT INTO members(id,name,active,data_quality) VALUES (2,'小雨',1,'clean')")
    c.execute("INSERT INTO tasks(id,title,weight,data_quality) VALUES (10,'扫地',3,'clean')")
    c.execute("INSERT INTO tasks(id,title,weight,data_quality) VALUES (20,'洗碗',1,'clean')")
    c.execute("INSERT INTO assignments(week_id,day,task_id,member_id) VALUES (1,0,10,1)")
    c.execute("INSERT INTO assignments(week_id,day,task_id,member_id) VALUES (1,1,10,1)")
    c.execute("INSERT INTO assignments(week_id,day,task_id,member_id) VALUES (1,0,20,2)")
    c.commit()


# ---------- over the line: one alert per overloaded member ----------

def test_over_waterline_creates_one_alert_per_member(conn):
    _seed_week(conn)
    put_settings(conn, {"load_waterline": 5})
    created = rebuild_week_alerts(conn, 1)
    conn.commit()

    assert len(created) == 1
    a = created[0]
    # pinned snapshot fields
    assert a["member_id"] == 1
    assert a["member_name"] == "阿明"
    assert a["load"] == 6
    assert a["waterline"] == 5
    assert a["week_id"] == 1
    assert a["week_label"] == "第12周"

    rows = list_alerts(conn)
    assert len(rows) == 1
    # list and detail expose the identical shape
    assert get_alert(conn, rows[0]["id"]) == rows[0]


def test_load_equal_to_waterline_creates_nothing(conn):
    _seed_week(conn)
    put_settings(conn, {"load_waterline": 6})  # m1 load == 6, not strictly over
    assert rebuild_week_alerts(conn, 1) == []
    conn.commit()
    assert list_alerts(conn) == []


def test_under_waterline_zero_alerts(conn):
    _seed_week(conn)
    put_settings(conn, {"load_waterline": 100})
    assert rebuild_week_alerts(conn, 1) == []
    conn.commit()
    assert list_alerts(conn) == []


def test_no_waterline_configured_zero_alerts(conn):
    _seed_week(conn)
    assert rebuild_week_alerts(conn, 1) == []
    conn.commit()
    assert list_alerts(conn) == []


# ---------- snapshots are immutable after generation ----------

def test_changing_waterline_keeps_old_alert_numbers(conn):
    _seed_week(conn)
    put_settings(conn, {"load_waterline": 5})
    rebuild_week_alerts(conn, 1)
    conn.commit()

    put_settings(conn, {"load_waterline": 100})
    conn.commit()
    rows = list_alerts(conn)
    assert len(rows) == 1
    assert rows[0]["load"] == 6
    assert rows[0]["waterline"] == 5  # snapshot, not the new 100


def test_changing_task_weight_keeps_old_alert_numbers(conn):
    _seed_week(conn)
    put_settings(conn, {"load_waterline": 5})
    rebuild_week_alerts(conn, 1)
    conn.commit()

    conn.execute("UPDATE tasks SET weight=50 WHERE id=10")
    conn.commit()
    rows = list_alerts(conn)
    assert len(rows) == 1
    assert rows[0]["load"] == 6  # snapshot, not recomputed to 100


# ---------- repeated generation: overwrite, never append ----------

def test_regenerate_same_week_overwrites(conn):
    _seed_week(conn)
    put_settings(conn, {"load_waterline": 5})
    first = rebuild_week_alerts(conn, 1)
    conn.commit()
    second = rebuild_week_alerts(conn, 1)  # regenerate same week
    conn.commit()

    assert len(second) == 1
    rows = list_alerts(conn, week_id=1)
    assert len(rows) == 1  # one row per (week, member), not appended
    assert rows[0]["id"] != first[0]["id"]  # replaced, not reused


def test_regenerate_removes_alerts_no_longer_over_line(conn):
    _seed_week(conn)
    put_settings(conn, {"load_waterline": 5})
    rebuild_week_alerts(conn, 1)
    conn.commit()
    assert len(list_alerts(conn, week_id=1)) == 1

    # m1 no longer overloaded; stale alert must be cleared on regenerate
    conn.execute("DELETE FROM assignments WHERE member_id=1 AND task_id=10 AND day=1")
    conn.commit()
    rebuild_week_alerts(conn, 1)
    conn.commit()
    assert list_alerts(conn, week_id=1) == []


def test_list_can_filter_by_week(conn):
    _seed_week(conn)
    conn.execute("INSERT INTO weeks(id,label,status) VALUES (2,'第13周','ready')")
    put_settings(conn, {"load_waterline": 5})
    rebuild_week_alerts(conn, 1)
    rebuild_week_alerts(conn, 2)  # no assignments -> nothing
    conn.commit()
    assert len(list_alerts(conn)) == 1
    assert list_alerts(conn, week_id=2) == []


# ---------- settings validation ----------

@pytest.mark.parametrize("bad", [0, -1, -0.01, "0", "abc", True, False])
def test_waterline_must_be_positive_number(conn, bad):
    with pytest.raises(SettingsError):
        put_settings(conn, {"load_waterline": bad})
    assert get_waterline(conn) is None  # rejected write leaves nothing behind


def test_waterline_accepts_positive_numbers(conn):
    put_settings(conn, {"load_waterline": 5})
    conn.commit()
    assert get_waterline(conn) == 5
    put_settings(conn, {"load_waterline": "3.5"})
    conn.commit()
    assert get_waterline(conn) == 3.5


def test_bad_setting_does_not_partially_write(conn):
    with pytest.raises(SettingsError):
        put_settings(conn, {"household": "绿纸之家", "load_waterline": 0})
    conn.commit()
    assert conn.execute("SELECT COUNT(*) c FROM settings").fetchone()["c"] == 0
