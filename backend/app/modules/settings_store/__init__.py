"""Settings read/write.

The settings table is a generic key/value store; this module owns the
validation rules for typed keys (currently ``load_waterline``).
"""

# keys whose values are numeric and must be strictly positive
_POSITIVE_NUMERIC_KEYS = {"load_waterline"}


class SettingsError(ValueError):
    def __init__(self, key: str, reason: str):
        super().__init__(f"{key}: {reason}")
        self.key = key
        self.reason = reason


def get_all(c) -> dict:
    return {r["key"]: r["value"] for r in c.execute("SELECT key,value FROM settings")}


def get(c, key: str):
    row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


def get_waterline(c):
    """Return the load waterline as a number, or None when unset/blank."""
    raw = get(c, "load_waterline")
    if raw is None or str(raw).strip() == "":
        return None
    try:
        n = float(raw)
    except (TypeError, ValueError):
        return None
    return int(n) if n.is_integer() else n


def put(c, items: dict):
    """Validate then upsert a batch of settings.

    Nothing is written when any item is invalid, so a bad request never
    partially mutates the store.
    """
    for k, v in items.items():
        if k in _POSITIVE_NUMERIC_KEYS:
            _require_positive_number(k, v)
    for k, v in items.items():
        c.execute(
            "INSERT INTO settings(key,value) VALUES (?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (k, str(v)),
        )


def _require_positive_number(key: str, value):
    if isinstance(value, bool):
        raise SettingsError(key, "not_a_number")
    try:
        n = float(value)
    except (TypeError, ValueError):
        raise SettingsError(key, "not_a_number")
    if n != n or n in (float("inf"), float("-inf")):
        raise SettingsError(key, "not_a_number")
    if n <= 0:
        raise SettingsError(key, "must_be_positive")
