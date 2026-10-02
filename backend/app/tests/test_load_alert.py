import pytest
from app import seed
from app.db import connect
from app.engines.rota import build_week_slots
from app.modules.load_alert import builder, repository, settings


@pytest.fixture
def db(monkeypatch, tmp_path):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    seed.init_db()
    c = connect()
    yield c
    c.close()


def seed_week(c, week_id=1, days=7):
    """与 generate 接口相同的落位路径：clean 成员 × clean 正权重任务轮询入库。"""
    mids = [r["id"] for r in c.execute(
        "SELECT id FROM members WHERE active=1 AND data_quality='clean' ORDER BY id")]
    tids = [r["id"] for r in db.execute(
        "SELECT id FROM tasks WHERE data_quality='clean' AND weight>0 ORDER BY id")]
    slots = build_week_slots(mids, tids, days=days)
    for s in slots:
        c.execute(
            "INSERT INTO assignments(week_id,day,task_id,member_id) VALUES (?,?,?,?)",
            (week_id, s["day"], s["task_id"], s["member_id"]))
    c.commit()
    return slots


def test_alert_created_only_for_over_waterline(db):
    # 轮询下：阿明/小雨固定拿权重1的任务（各 7），爷爷固定拿扫地权重2（=14）
    seed_week(db)
    settings.set_waterline(db, 7)
    db.commit()
    created = builder.rebuild_for_week(db, 1, settings.get_waterline(db))
    db.commit()

    alerts = repository.list_alerts(db)
    assert len(alerts) == 1
    a = alerts[0]
    assert a["member_id"] == 3 and a["member_name"] == "爷爷"
    assert a["load"] == 14 and a["waterline"] == 7  # 钉死当时数字
    assert a["week_id"] == 1 and a["week_label"] == "第12周"
    assert repository.get_alert(db, created[0]["id"])["load"] == 14


def test_zero_alerts_when_all_under_waterline(db):
    seed_week(db)
    builder.rebuild_for_week(db, 1, 100)
    db.commit()
    assert repository.list_alerts(db) == []


def test_change_waterline_does_not_rewrite_old_alert(db):
    seed_week(db)
    settings.set_waterline(db, 7)
    db.commit()
    builder.rebuild_for_week(db, 1, 7)
    db.commit()
    old = repository.list_alerts(db)[0]

    settings.set_waterline(db, 100)  # 只改水位
    db.commit()
    kept = repository.get_alert(db, old["id"])
    assert kept["load"] == 14 and kept["waterline"] == 7  # 旧单不回刷


def test_change_task_weight_does_not_rewrite_old_alert(db):
    seed_week(db)
    builder.rebuild_for_week(db, 1, 7)
    db.commit()
    old = repository.list_alerts(db)[0]

    db.execute("UPDATE tasks SET weight=99 WHERE id=3")  # 只改任务权重
    db.commit()
    kept = repository.get_alert(db, old["id"])
    assert kept["load"] == 14 and kept["waterline"] == 7


def test_regenerate_same_week_overwrites(db):
    seed_week(db)
    builder.rebuild_for_week(db, 1, 7)
    db.commit()
    assert len(repository.list_alerts(db)) == 1

    # 同周再次生成、新水位下无人超线：旧单被清空而不是追加
    builder.rebuild_for_week(db, 1, 100)
    db.commit()
    assert repository.list_alerts(db) == []

    # 再超线：每成员每周仍至多一条（UNIQUE + 覆盖口径）
    builder.rebuild_for_week(db, 1, 7)
    db.commit()
    rows = repository.list_alerts(db)
    assert len(rows) == 1 and rows[0]["member_id"] == 3


def test_waterline_must_be_positive_integer(db):
    for bad in (0, -1, "x", None):
        with pytest.raises(ValueError):
            settings.set_waterline(db, bad)
    db.commit()
    assert settings.get_waterline(db) is None  # 拒写，不落库
    assert settings.set_waterline(db, "6") == 6
    db.commit()
    assert settings.get_waterline(db) == 6
