"""load_waterline 设置读写。"""

KEY = "load_waterline"


def get_waterline(c) -> int | None:
    """返回当前水位；未登记或值非整数时返回 None。"""
    row = c.execute("SELECT value FROM settings WHERE key=?", (KEY,)).fetchone()
    if row is None:
        return None
    try:
        return int(str(row["value"]).strip())
    except (TypeError, ValueError):
        return None


def set_waterline(c, raw) -> int:
    """校验并落库水位，必须为 > 0 的整数；非法值抛 ValueError 且不写库。"""
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError, AttributeError):
        raise ValueError("load_waterline must be an integer > 0")
    if value <= 0:
        raise ValueError("load_waterline must be an integer > 0")
    c.execute(
        "INSERT INTO settings(key,value) VALUES (?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (KEY, str(value)),
    )
    return value
