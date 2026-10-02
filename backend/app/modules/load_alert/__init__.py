"""负荷水位告警单：设置读写、告警建造、列表详情三个子模块。"""
from app.modules.load_alert import builder, repository, settings

__all__ = ["builder", "repository", "settings"]
