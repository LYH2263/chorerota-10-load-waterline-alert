"""Build load-waterline alerts for a generated week."""

from datetime import datetime

from app.modules.settings_store import get_waterline

# fields pinned on every alert row, exposed identically by list and detail
ALERT_FIELDS = (
    "id", "week_id", "week_label", "member_id", "member_name",
    "load", "waterline", "created_at",
)


def member_loads(c, week_id: int) -> dict:
    """Sum of task weights assigned to each member in the week."""
    rows = c.execute(
        """
        SELECT a.member_id AS member_id, COALESCE(SUM(t.weight), 0) AS load
        FROM assignments a
        JOIN tasks t ON t.id = a.task_id
        WHERE a.week_id = ?
        GROUP BY a.member_id
        """,
        (week_id,),
    )
    return {r["member_id"]: r["load"] for r in rows}


def rebuild_week_alerts(c, week_id: int) -> list[dict]:
    """Recompute alerts for a week from its assignments and the current
    waterline, replacing any previous alerts for that week.

    Overwrite semantics (decided for repeated generation of the same
    week): one alert per over-line member, at most one row per
    (week, member). No waterline configured -> no rows. Members at or
    under the line produce nothing.
    """
    waterline = get_waterline(c)
    c.execute("DELETE FROM load_alerts WHERE week_id=?", (week_id,))
    created: list[dict] = []
    if waterline is None:
        return created

    week = c.execute("SELECT label FROM weeks WHERE id=?", (week_id,)).fetchone()
    week_label = week["label"] if week else None
    loads = member_loads(c, week_id)
    now = datetime.now().isoformat(timespec="seconds")
    for member_id, load in sorted(loads.items()):
        if load <= waterline:
            continue  # strictly over the line; equal is fine
        m = c.execute("SELECT name FROM members WHERE id=?", (member_id,)).fetchone()
        cur = c.execute(
            """
            INSERT INTO load_alerts(week_id,week_label,member_id,member_name,load,waterline,created_at)
            VALUES (?,?,?,?,?,?,?)
            """,
            (week_id, week_label, member_id, m["name"] if m else "?", load, waterline, now),
        )
        created.append({
            "id": cur.lastrowid, "week_id": week_id, "week_label": week_label,
            "member_id": member_id, "member_name": m["name"] if m else "?",
            "load": load, "waterline": waterline, "created_at": now,
        })
    return created
