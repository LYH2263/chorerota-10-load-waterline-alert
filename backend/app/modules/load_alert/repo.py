"""Read side for load-waterline alerts: list and detail share one shape."""

from app.modules.load_alert.builder import ALERT_FIELDS

_COLS = ", ".join(ALERT_FIELDS)


def _row_to_dict(row) -> dict:
    return {k: row[k] for k in ALERT_FIELDS}


def list_alerts(c, week_id=None) -> list[dict]:
    """All alerts (newest first), optionally scoped to one week.

    The list uses the same pinned snapshot fields as the detail view.
    """
    if week_id is None:
        rows = c.execute(f"SELECT {_COLS} FROM load_alerts ORDER BY id DESC")
    else:
        rows = c.execute(
            f"SELECT {_COLS} FROM load_alerts WHERE week_id=? ORDER BY id DESC",
            (week_id,),
        )
    return [_row_to_dict(r) for r in rows]


def get_alert(c, alert_id: int):
    row = c.execute(
        f"SELECT {_COLS} FROM load_alerts WHERE id=?", (alert_id,)
    ).fetchone()
    return _row_to_dict(row) if row else None
