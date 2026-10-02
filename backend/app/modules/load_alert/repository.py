"""告警单列表与详情读取（只返回落库时钉死的快照字段）。"""


def list_alerts(c, week_id: int | None = None) -> list[dict]:
    if week_id is None:
        rows = c.execute("SELECT * FROM load_alerts ORDER BY id DESC")
    else:
        rows = c.execute(
            "SELECT * FROM load_alerts WHERE week_id=? ORDER BY id DESC", (week_id,)
        )
    return [dict(r) for r in rows]


def get_alert(c, alert_id: int) -> dict | None:
    row = c.execute("SELECT * FROM load_alerts WHERE id=?", (alert_id,)).fetchone()
    return dict(row) if row else None
