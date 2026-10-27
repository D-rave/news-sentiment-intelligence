"""可复现的财经新闻规则辅助标注。

这些结果用于系统演示与离线分析，不冒充大模型的输出。
如需替换为模型结果，可在导入前为数据表增加行业、情感分析和情感得分列。
"""
from __future__ import annotations

import json
import re
from collections import Counter

CATEGORY_KEYWORDS = {
    "金融": ["银行", "券商", "证券", "保险", "金融", "央行", "利率", "贷款", "基金", "信托", "降准", "降息", "汇率"],
    "科技": ["科技", "半导体", "芯片", "人工智能", "AI", "软件", "计算机", "电子", "云计算", "机器人", "算力", "寒武纪"],
    "消费": ["消费", "食品", "饮料", "白酒", "零售", "家电", "餐饮", "旅游", "美妆", "商贸", "茅台", "乳业"],
    "能源": ["能源", "石油", "石化", "煤炭", "电力", "光伏", "风电", "储能", "电池", "天然气", "新能源", "充电"],
    "医药": ["医药", "医疗", "药品", "生物", "疫苗", "医院", "器械", "诊疗", "药企", "中药", "创新药"],
    "房地产": ["房地产", "地产", "楼市", "住房", "物业", "土地", "房贷", "保障房", "万科", "保利发展"],
    "工业": ["工业", "制造", "机械", "化工", "钢铁", "有色", "建筑", "军工", "船舶", "材料", "基建", "工程"],
    "汽车": ["汽车", "车企", "整车", "新能源车", "智能驾驶", "自动驾驶", "动力电池", "比亚迪", "理想汽车", "赛力斯"],
    "通信": ["通信", "通讯", "5G", "6G", "运营商", "电信", "移动", "联通", "光模块", "基站", "卫星互联网"],
    "农业": ["农业", "农林", "牧渔", "养殖", "种植", "种业", "生猪", "猪肉", "饲料", "粮食", "农产品"],
}

POSITIVE_WORDS = [
    "上涨", "增长", "利好", "突破", "改善", "回升", "走强", "领涨", "盈利", "超预期", "创新高", "增持", "回购",
    "分红", "涨停", "回暖", "复苏", "提振", "扩大", "加速", "优势", "机遇", "亮眼", "修复", "高质量发展", "订单饱满",
]
NEGATIVE_WORDS = [
    "下跌", "下降", "利空", "风险", "亏损", "下滑", "走弱", "领跌", "退市", "违规", "处罚", "减持", "跌停", "承压",
    "低迷", "违约", "调查", "立案", "警示", "暴跌", "收紧", "不及预期", "爆雷", "终止", "否决", "下滑", "贸易摩擦",
]
NEUTRAL_WORDS = ["维持", "平稳", "持平", "中性", "震荡", "观望", "符合预期"]

KEYWORD_POOL = sorted({word for words in CATEGORY_KEYWORDS.values() for word in words} | {
    "A股", "上证指数", "深证成指", "创业板指", "科创板", "北交所", "资本市场", "上市公司", "政策", "市场", "成交额",
    "外资", "并购重组", "市值", "股价", "业绩", "营收", "净利润", "新质生产力", "低空经济", "国企改革",
}, key=len, reverse=True)


def classify_category(title: str, content: str) -> str:
    title = title or ""
    content = content or ""
    scores = {}
    for category, words in CATEGORY_KEYWORDS.items():
        score = sum(title.count(word) * 4 + content.count(word) for word in words)
        scores[category] = score
    category, score = max(scores.items(), key=lambda item: item[1])
    return category if score >= 2 else "其他"


def analyze_sentiment(title: str, content: str) -> tuple[str, float]:
    # 标题权重更高；短正文降低中性平滑项，长正文避免极端分数。
    title = title or ""
    content = (content or "")[:12000]
    positive = sum(title.count(word) * 3 + content.count(word) for word in POSITIVE_WORDS)
    negative = sum(title.count(word) * 3 + content.count(word) for word in NEGATIVE_WORDS)
    neutral = sum(title.count(word) * 2 + content.count(word) for word in NEUTRAL_WORDS)
    score = (positive - negative) / (positive + negative + neutral + 8)
    score = max(-1.0, min(1.0, round(score, 4)))
    if score >= 0.08:
        return "积极", score
    if score <= -0.08:
        return "消极", score
    return "中性", score


def extract_keywords(title: str, content: str, limit: int = 8) -> str:
    text = f"{title or ''} {content or ''}"
    counts = Counter()
    for word in KEYWORD_POOL:
        count = text.count(word)
        if count:
            counts[word] = count + (title or "").count(word) * 3
    return json.dumps([word for word, _ in counts.most_common(limit)], ensure_ascii=False)


def clean_text(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return re.sub(r"\s+", " ", text)
