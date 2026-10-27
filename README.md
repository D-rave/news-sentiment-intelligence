# 闻见 · 财经新闻智能分析系统

基于用户提供的 1962 条澎湃新闻数据，补齐新闻分类展示、情感分析和三栏可视化大屏的完整前后端系统。

## 功能

- **新闻库**：行业、情感、来源、关键词组合筛选，时间排序，分页，全文详情，同行业关联新闻。
- **情感洞察**：全年月度趋势、积极/中性/消极构成、行业情感对比、平均得分、近期风险报道。
- **可视化大屏**：三栏科技风布局、7 个数据区域、动态粒子、实时时钟、60 秒自动刷新、手动刷新、全屏切换。
- **数据接口**：Axios 调用 Flask REST API；分类、情感、趋势、来源等统计在数据库中分组完成。

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 2.7、Vue Router 3、Vite 7.3.7、Axios、CSS/SCSS |
| 本地运行 | Node.js 20.19+ / 22.12+ / 24，Corepack + pnpm 12 |
| 图表 | Apache ECharts **5.4.3**，`echarts.init(element, 'macarons')` |
| 动效 | Particles.js 2.0 |
| 后端 | Flask、Flask-SQLAlchemy、Flask-Cors |
| 数据库 | MySQL 8（正式运行）；SQLite 仅用于免配置预览/开发 |
| 部署 | Gunicorn、Docker、Docker Compose |

## 项目结构

```text
├── src/
│   ├── api/index.js             # Axios 接口封装
│   ├── assets/main.scss         # 全局与科技风基础样式
│   ├── components/              # 新闻详情、情感标签、大屏标题
│   ├── plugins/echarts.js       # ECharts 与 macarons 主题注册
│   ├── views/news.vue           # 新闻分类与检索页面
│   ├── views/sentiment.vue      # 情感分析页面
│   └── views/board.vue          # 三栏可视化大屏
├── backend/
│   ├── app.py                   # Flask 应用、查询和分组统计 API
│   ├── models.py                # MySQL/SQLAlchemy 新闻模型
│   ├── analyzer.py              # 可复现规则辅助分类与情感分析
│   ├── import_data.py           # Excel 幂等导入
│   └── create_database.sql      # MySQL 建库 SQL
├── data/                        # 用户原始数据文件
├── Dockerfile
└── docker-compose.yml
```

## 方式一：Docker Compose 启动完整 MySQL 系统（推荐）

安装 Docker 后，在项目根目录执行：

```bash
docker compose up --build
```

等待 MySQL 健康检查和数据导入完成，访问 `http://localhost:5000`。

- 新闻库：`http://localhost:5000/#/news`
- 情感洞察：`http://localhost:5000/#/sentiment`
- 可视化大屏：`http://localhost:5000/#/board`

MySQL 数据保存在 `mysql_data` 卷中。默认 root 密码仅供本地演示，正式部署请在 `docker-compose.yml` 中修改。

## 方式二：本地开发

### 1. 准备 MySQL

```bash
mysql -u root -p < backend/create_database.sql
```

复制 `.env.example` 为 `.env`，修改 `DATABASE_URL` 中的账号和密码。Flask 不自动加载 `.env`，请在终端中设置环境变量：

```bash
# macOS / Linux
export DATABASE_URL='mysql+pymysql://root:你的密码@127.0.0.1:3306/news_intelligence?charset=utf8mb4'
```

```powershell
# Windows PowerShell
$env:DATABASE_URL='mysql+pymysql://root:你的密码@127.0.0.1:3306/news_intelligence?charset=utf8mb4'
```

未设置 `DATABASE_URL` 时，系统会使用 `data/news_analysis.db`，方便不安装 MySQL 时直接体验；这不替代正式 MySQL 部署。

### 2. 一键启动前后端

支持 Node.js 24，推荐使用项目锁定的 pnpm 12，避免 npm 11 自身的安装异常：

```bash
corepack enable
corepack prepare pnpm@12.15.0 --activate
pnpm install --frozen-lockfile
pnpm dev
```

`pnpm dev` 会自动安装轻量 Flask 依赖、启动 5000 端口的后端，等待 `/api/health` 就绪后再启动 3000 端口的 Vue。首次数据库为空时，直接从 `data/news_seed.json` 载入 1962 条已分析新闻，无需等待重新计算。

访问 `http://localhost:3000`，Vite 已将 `/api` 代理到 Flask。不要使用只启动 Vite 的 `vite` 命令，否则页面会因后端未启动而没有数据。项目使用 Vue 2 兼容范围内最新的 Vite 7.3.7；Vite 8 当前不在 `@vitejs/plugin-vue2` 的支持范围内。

### 3. 可选：重新从 Excel 导入

如需使用新增模型标签或重新运行规则分析：

```bash
pip install -r requirements.txt
python backend/import_data.py
```

数据导入是幂等操作，以标题去重，不会清空已有数据。

### 4. 生产构建

```bash
pip install -r requirements.txt
pnpm build
python backend/app.py
```

Flask 会直接托管 `dist/`，无需额外 Nginx 即可运行。

## 核心 API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/health` | 服务与数据库状态 |
| GET | `/api/meta` | 分类、来源、日期范围 |
| GET | `/api/news` | 新闻检索与分页 |
| GET | `/api/news/<id>` | 全文与关联新闻 |
| GET | `/api/stats/overview` | 核心指标 |
| GET | `/api/stats/categories` | 行业分组统计 |
| GET | `/api/stats/sentiment` | 情感分组统计 |
| GET | `/api/stats/trend` | 月度情感趋势 |
| GET | `/api/stats/category-sentiment` | 行业 × 情感统计 |
| GET | `/api/stats/sources` | 来源排行 |
| GET | `/api/stats/keywords` | 高频关键词 |
| GET | `/api/stats/board` | 大屏聚合数据 |

新闻检索参数：`page`、`page_size`、`category`、`sentiment`、`source`、`q`、`start_date`、`end_date`、`sort`。

## 数据与分析口径

原始 Excel 只有标题、发布时间、来源、正文，**不含已完成的行业或情感标签**。系统通过 `backend/analyzer.py` 中的财经行业词典和情感词典生成可复现的规则辅助标签，并在页面中明确展示该口径。

如果后续 Excel 增加 `行业`、`情感分析`、`情感得分` 列，导入程序会优先使用这些已有标签，并将分析方式标为“数据集模型标签”。情感得分取值范围为 `[-1, 1]`。所有分析仅供文本研究与课程演示，不构成投资建议。

## 安全说明

新系统不在源码中保存任何 API Key、数据库密码或爬虫 Cookie。原脚本如需继续使用，请自行将硬编码密钥迁移到环境变量，并立即轮换已经公开过的密钥。
