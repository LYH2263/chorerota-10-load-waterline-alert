"""告警建造：周表生成成功后按成员汇总权重负荷，超水位者各产一条快照单。

覆盖口径：同一周重复生成时，先删该周旧单再重建，每成员每周至多一条。
单据内负荷/水位为当时快照，之后改水位或任务权重不回刷。
"""


def member_loads(c, week_id: int) -> list[dict]:
    """汇总某周每位成员承担的任务权重（assignments join tasks）。"""
    return [
        dict(r)
        for r in c.execute(
            """
            SELECT a.member_id AS member_id,
                   m.name AS member_name,
                   COALESCE(SUM(t.weight), 0) AS load
            FROM assignments a
            JOIN tasks t ON t.id = a.task_id
            JOIN members m ON m.id = a.member_id
            WHERE a.week_id = ?
            GROUP BY a.member_id
            """,
            (week_id,),
        )
    ]


def rebuild_for_week(c, week_id: int, waterline: int | None) -> list[dict]:
    """覆盖式重建某周告警。

    先删除该周全部旧单；waterline 为 None（未登记水位）时只删不建。
    仅给 load > waterline 的成员建单，钉死当时水位与周/成员快照。
    返回新建的告警行（dict 列表）。
    """
    c.execute("DELETE FROM load_alerts WHERE week_id=?", (week_id,))
    if waterline is None:
        return []

    week = c.execute("SELECT id,label FROM weeks WHERE id=?", (week_id,)).fetchone()
    week_label = week["label"] if week else None
    created = []
    for row in member_loads(c, week_id):
        if row["load"] <= waterline:
            continue
        cur = c.execute(
            """
            INSERT INTO load_alerts(week_id, week_label, member_id, member_name, load, waterline)
            VALUES (?,?,?,?,?,?)
            """,
            (week_id, week_label, row["member_id"], row["member_name"], row["load"], waterline),
        )
        alert = {
            "id": cur.lastrowid,
            "week_id": week_id,
            "week_label": week_label,
            "member_id": row["member_id"],
            "member_name": row["member_name"],
            "load": row["load"],
            "waterline": waterline,
        }
        created.append(alert)
    return created
