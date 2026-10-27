from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from models import News, db


def import_seed(file_path: str | Path) -> int:
    """使用标准库载入预分析数据，供预览和快速开发启动使用。"""
    rows = json.loads(Path(file_path).read_text(encoding="utf-8"))
    existing = {title for title, in db.session.query(News.title).all()}
    records = []
    for row in rows:
        if row["title"] in existing:
            continue
        records.append({
            **row,
            "published_at": date.fromisoformat(row["published_at"]),
        })
    for start in range(0, len(records), 300):
        db.session.bulk_insert_mappings(News, records[start:start + 300])
        db.session.commit()
    return len(records)
