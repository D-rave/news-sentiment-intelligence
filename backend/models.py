from __future__ import annotations

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class News(db.Model):
    __tablename__ = "news"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(500), nullable=False, unique=True, index=True)
    published_at = db.Column(db.Date, nullable=False, index=True)
    source = db.Column(db.String(120), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(30), nullable=False, index=True)
    sentiment = db.Column(db.String(10), nullable=False, index=True)
    sentiment_score = db.Column(db.Float, nullable=False, default=0)
    keywords = db.Column(db.Text, nullable=False, default="[]")
    analysis_method = db.Column(db.String(40), nullable=False, default="规则辅助分析")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.Index("ix_news_category_sentiment", "category", "sentiment"),
        db.Index("ix_news_date_category", "published_at", "category"),
    )

    def to_dict(self, full: bool = False):
        import json

        data = {
            "id": self.id,
            "title": self.title,
            "published_at": self.published_at.isoformat(),
            "source": self.source,
            "category": self.category,
            "sentiment": self.sentiment,
            "sentiment_score": round(self.sentiment_score or 0, 4),
            "keywords": json.loads(self.keywords or "[]"),
            "analysis_method": self.analysis_method,
            "summary": self.content[:180] + ("…" if len(self.content) > 180 else ""),
        }
        if full:
            data["content"] = self.content
        return data
