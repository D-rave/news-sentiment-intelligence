from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import select

from analyzer import CATEGORY_KEYWORDS, analyze_sentiment, classify_category, clean_text, extract_keywords
from models import News, db

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FILE = ROOT / "data" / "澎湃新闻数据集.xlsx"


def import_excel(file_path: str | Path = DEFAULT_FILE) -> int:
    """幂等导入：标题已存在时跳过，不删除或覆盖数据库内容。"""
    frame = pd.read_excel(file_path, sheet_name="Sheet1")
    required = {"标题", "发布时间", "来源", "详细内容"}
    if not required.issubset(frame.columns):
        raise ValueError(f"数据文件必须包含字段：{', '.join(required)}")

    inserted = 0
    for row in frame.to_dict("records"):
        title = clean_text(row["标题"])
        if not title:
            continue
        exists = db.session.execute(select(News.id).where(News.title == title)).first()
        if exists:
            continue
        content = clean_text(row["详细内容"])
        published_at = pd.to_datetime(row["发布时间"]).date()
        category = clean_text(row.get("行业")) or classify_category(title, content)
        raw_sentiment = clean_text(row.get("情感分析"))
        raw_score = row.get("情感得分")
        sentiment, score = analyze_sentiment(title, content)
        if raw_sentiment in {"积极", "中性", "消极"}:
            sentiment = raw_sentiment
        try:
            if pd.notna(raw_score):
                score = max(-1.0, min(1.0, float(raw_score)))
        except (TypeError, ValueError):
            pass
        method = "数据集模型标签" if raw_sentiment or pd.notna(raw_score) else "规则辅助分析"
        db.session.add(News(
            title=title,
            published_at=published_at,
            source=clean_text(row["来源"]) or "未知来源",
            content=content,
            category=category if category in {*CATEGORY_KEYWORDS, "其他"} else "其他",
            sentiment=sentiment,
            sentiment_score=score,
            keywords=extract_keywords(title, content),
            analysis_method=method,
        ))
        inserted += 1
        if inserted % 200 == 0:
            db.session.commit()
    db.session.commit()
    return inserted


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="将新闻 Excel 幂等导入 MySQL/SQLite")
    parser.add_argument("--file", default=str(DEFAULT_FILE), help="新闻 Excel 文件路径")
    args = parser.parse_args()
    from app import create_app

    app = create_app(auto_seed=False)
    with app.app_context():
        db.create_all()
        count = import_excel(args.file)
        print(f"导入完成：新增 {count} 条，数据库总计 {News.query.count()} 条。")
