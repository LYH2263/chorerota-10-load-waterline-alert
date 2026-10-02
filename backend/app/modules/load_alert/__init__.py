"""Load-waterline alerts.

Split into two modules:

* :mod:`app.modules.load_alert.builder` builds alerts after a weekly board
  is generated (summation + snapshot, overwrite-per-week semantics);
* :mod:`app.modules.load_alert.repo` is the read side (list / detail).

An alert is an immutable snapshot: it pins the member, their summed task
weight for the week, the waterline *at generation time* and the week.
Changing the setting or task weights afterwards never touches existing
rows — the only way alerts for a week change is regenerating that week,
which overwrites that week's alerts as a batch.
"""

DDL = """
CREATE TABLE IF NOT EXISTS load_alerts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_id INT,
    week_label TEXT,
    member_id INT,
    member_name TEXT,
    load REAL,
    waterline REAL,
    created_at TEXT
);
"""

from app.modules.load_alert.builder import rebuild_week_alerts  # noqa: E402,F401
from app.modules.load_alert.repo import get_alert, list_alerts  # noqa: E402,F401
