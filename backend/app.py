from __future__ import annotations

import json
import os
from collections import Counter
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sqlalchemy import case, func, or_

from models import News, db

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ["金融", "科技", "消费", "能源", "医药", "房地产", "工业", "汽车", "通信", "农业", "其他"]
SENTIMENTS = ["积极", "中性", "消极"]


def create_app(auto_seed: bool | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.static_folder = str(ROOT / "dist")
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'data' / 'news_analysis.db'}")
    if database_url.startswith("mysql://"):
        database_url = database_url.replace("mysql://", "mysql+pymysql://", 1)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True, "pool_recycle": 280},
        JSON_AS_ASCII=False,
    )
    CORS(app, resources={r"/api/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})
    db.init_app(app)
    register_routes(app)
    register_errors(app)

    should_seed = os.getenv("AUTO_SEED", "1") == "1" if auto_seed is None else auto_seed
    with app.app_context():
        db.create_all()
        if should_seed and News.query.count() == 0:
            seed = ROOT / "data" / "news_seed.json"
            source = ROOT / "data" / "澎湃新闻数据集.xlsx"
            if seed.exists():
                from seed_data import import_seed
                import_seed(seed)
            elif source.exists():
                from import_data import import_excel
                import_excel(source)
    return app


def register_routes(app: Flask):
    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "database": db.engine.dialect.name, "news": News.query.count()})

    @app.get("/api/meta")
    def meta():
        dates = db.session.query(func.min(News.published_at), func.max(News.published_at)).one()
        sources = [row[0] for row in db.session.query(News.source).distinct().order_by(News.source).all()]
        return jsonify({
            "categories": CATEGORIES,
            "sentiments": SENTIMENTS,
            "sources": sources,
            "date_range": [dates[0].isoformat() if dates[0] else None, dates[1].isoformat() if dates[1] else None],
            "analysis_method": "规则辅助分析",
        })

    @app.get("/api/news")
    def news_list():
        query = News.query
        category = request.args.get("category", "").strip()
        sentiment = request.args.get("sentiment", "").strip()
        source = request.args.get("source", "").strip()
        keyword = request.args.get("q", "").strip()
        if category and category != "全部":
            query = query.filter(News.category == category)
        if sentiment and sentiment != "全部":
            query = query.filter(News.sentiment == sentiment)
        if source:
            query = query.filter(News.source == source)
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(or_(News.title.like(like), News.content.like(like), News.keywords.like(like)))
        for arg, column in [("start_date", News.published_at), ("end_date", News.published_at)]:
            value = request.args.get(arg)
            if value:
                try:
                    parsed = date.fromisoformat(value)
                    query = query.filter(column >= parsed if arg == "start_date" else column <= parsed)
                except ValueError:
                    return jsonify({"error": f"{arg} 必须为 YYYY-MM-DD"}), 400
        sort = request.args.get("sort", "date_desc")
        query = query.order_by(News.published_at.asc() if sort == "date_asc" else News.published_at.desc(), News.id.desc())
        page = max(request.args.get("page", 1, type=int), 1)
        page_size = min(max(request.args.get("page_size", 12, type=int), 1), 100)
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        return jsonify({
            "items": [item.to_dict() for item in pagination.items],
            "total": pagination.total,
            "page": page,
            "page_size": page_size,
            "pages": pagination.pages,
        })

    @app.get("/api/news/<int:news_id>")
    def news_detail(news_id: int):
        item = db.get_or_404(News, news_id)
        related = News.query.filter(News.category == item.category, News.id != item.id).order_by(
            func.abs(func.datediff(News.published_at, item.published_at)), News.id.desc()
        ).limit(4).all() if db.engine.dialect.name == "mysql" else News.query.filter(
            News.category == item.category, News.id != item.id
        ).order_by(News.published_at.desc(), News.id.desc()).limit(4).all()
        return jsonify({"item": item.to_dict(full=True), "related": [row.to_dict() for row in related]})

    @app.get("/api/stats/overview")
    def overview():
        total = News.query.count()
        average = db.session.query(func.avg(News.sentiment_score)).scalar() or 0
        dates = db.session.query(func.min(News.published_at), func.max(News.published_at)).one()
        rows = grouped_sentiment()
        counts = {row["name"]: row["value"] for row in rows}
        return jsonify({
            "total": total,
            "categories": db.session.query(News.category).distinct().count(),
            "sources": db.session.query(News.source).distinct().count(),
            "average_score": round(float(average), 4),
            "positive_rate": round(counts.get("积极", 0) / total * 100, 2) if total else 0,
            "negative_count": counts.get("消极", 0),
            "date_range": [dates[0].isoformat() if dates[0] else None, dates[1].isoformat() if dates[1] else None],
        })

    @app.get("/api/stats/categories")
    def categories():
        rows = db.session.query(News.category, func.count(News.id)).group_by(News.category).order_by(func.count(News.id).desc()).all()
        return jsonify([{"name": name, "value": count} for name, count in rows])

    @app.get("/api/stats/sentiment")
    def sentiment():
        return jsonify(grouped_sentiment())

    @app.get("/api/stats/trend")
    def trend():
        dialect = db.engine.dialect.name
        month = func.date_format(News.published_at, "%Y-%m") if dialect == "mysql" else func.strftime("%Y-%m", News.published_at)
        rows = db.session.query(
            month.label("month"), News.sentiment, func.count(News.id), func.avg(News.sentiment_score)
        ).group_by(month, News.sentiment).order_by(month).all()
        months = sorted({row[0] for row in rows})
        result = {"months": months, "positive": [], "neutral": [], "negative": [], "score": []}
        for current in months:
            selected = [row for row in rows if row[0] == current]
            for label, key in [("积极", "positive"), ("中性", "neutral"), ("消极", "negative")]:
                result[key].append(next((row[2] for row in selected if row[1] == label), 0))
            scores = [float(row[3] or 0) * row[2] for row in selected]
            result["score"].append(round(sum(scores) / sum(row[2] for row in selected), 4))
        return jsonify(result)

    @app.get("/api/stats/category-sentiment")
    def category_sentiment():
        rows = db.session.query(
            News.category,
            func.sum(case((News.sentiment == "积极", 1), else_=0)),
            func.sum(case((News.sentiment == "中性", 1), else_=0)),
            func.sum(case((News.sentiment == "消极", 1), else_=0)),
            func.avg(News.sentiment_score),
        ).group_by(News.category).order_by(func.count(News.id).desc()).all()
        return jsonify([{
            "category": row[0], "positive": int(row[1]), "neutral": int(row[2]), "negative": int(row[3]),
            "average_score": round(float(row[4] or 0), 4), "total": int(row[1] + row[2] + row[3]),
        } for row in rows])

    @app.get("/api/stats/sources")
    def sources():
        rows = db.session.query(News.source, func.count(News.id)).group_by(News.source).order_by(func.count(News.id).desc()).limit(10).all()
        return jsonify([{"name": name, "value": count} for name, count in rows])

    @app.get("/api/stats/keywords")
    def keywords():
        counter = Counter()
        for value, in db.session.query(News.keywords).all():
            counter.update(json.loads(value or "[]"))
        return jsonify([{"name": word, "value": count} for word, count in counter.most_common(40)])

    @app.get("/api/stats/board")
    def board():
        # 复用各分组统计视图，减少前端首屏请求并保证口径一致。
        with app.test_request_context():
            overview_data = overview().get_json()
            trend_data = trend().get_json()
            category_data = category_sentiment().get_json()
            source_data = sources().get_json()
            keyword_data = keywords().get_json()
        latest = News.query.filter(News.sentiment == "消极").order_by(News.published_at.desc(), News.id.desc()).limit(12).all()
        return jsonify({
            "overview": overview_data, "trend": trend_data, "category_sentiment": category_data,
            "sources": source_data, "keywords": keyword_data, "latest": [item.to_dict() for item in latest],
        })

    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def frontend(path):
        if path.startswith("api/"):
            return jsonify({"error": "接口不存在"}), 404
        target = Path(app.static_folder) / path
        if path and target.is_file():
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, "index.html")


def grouped_sentiment():
    rows = db.session.query(News.sentiment, func.count(News.id)).group_by(News.sentiment).all()
    counts = dict(rows)
    return [{"name": name, "value": counts.get(name, 0)} for name in SENTIMENTS]


def register_errors(app: Flask):
    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "请求的内容不存在"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error("Server error: %s", error)
        return jsonify({"error": "服务暂时不可用，请稍后重试"}), 500


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=os.getenv("FLASK_DEBUG") == "1")
