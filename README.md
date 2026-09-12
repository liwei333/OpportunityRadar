# OpportunityRadar — 商机雷达

> AI Research Agent：自主市场研究、候选发现、Buyer Score 评分、证据整理

## 产品定位

OpportunityRadar 是一个 AI 研究 Agent。它根据用户的商业目标，自主完成市场研究，从大量公开内容中完成数据收集、清洗、筛选、智能评分和证据整理，最终找出真正值得行动的商业机会和潜在客户。

当前阶段：**MVP V0 / Technical Spike 前置工程**

## 功能架构

```
Vue Web (前端)
    ↓
FastAPI (API 层)
    ↓
Research Service (应用编排)
    ↓
Planner → Collector → Normalizer → Deduplicator → Buyer Scoring → Ranking → SQLite
```

## 技术栈

### 后端
- Python 3.12+
- FastAPI + Uvicorn
- Pydantic v2
- SQLAlchemy 2.x (async) + aiosqlite
- Polars (数据清洗)
- Playwright (浏览器自动化)
- pytest + ruff

### 前端
- Vue 3 + TypeScript
- Vite
- Pinia + Vue Router
- Element Plus

## 项目目录

```text
opportunity-radar/
├── apps/web/                   # Vue 3 前端
│   ├── src/
│   │   ├── api/                # API 客户端
│   │   ├── components/         # 公共组件
│   │   ├── views/              # 页面视图
│   │   │   ├── ResearchView.vue    # 研究输入页
│   │   │   ├── ProgressView.vue    # Agent 进度页
│   │   │   └── OpportunityBoard.vue # 潜客看板
│   │   ├── stores/             # Pinia 状态管理
│   │   ├── router/             # 路由配置
│   │   └── types/              # TypeScript 类型
│   └── package.json
│
├── services/agent/             # Python 后端
│   ├── app/
│   │   ├── main.py             # FastAPI 入口
│   │   ├── api/                # API 路由
│   │   │   ├── health.py       # 健康检查
│   │   │   └── research.py     # 研究任务 API
│   │   ├── core/               # 核心配置
│   │   │   ├── config.py       # 应用配置
│   │   │   ├── exceptions.py   # 异常定义
│   │   │   └── logging.py      # 日志配置
│   │   ├── domain/             # 领域模型
│   │   │   ├── research/       # 研究任务
│   │   │   ├── opportunity/    # 候选和机会
│   │   │   ├── evidence/       # 证据
│   │   │   └── scoring/        # 评分
│   │   ├── application/        # 应用服务
│   │   │   ├── research_service.py  # 流水线编排
│   │   │   ├── planner/        # 搜索规划
│   │   │   ├── collector/      # 数据采集
│   │   │   ├── normalizer/     # 数据清洗/去重
│   │   │   ├── intelligence/   # Buyer 评分
│   │   │   └── ranking/        # 排序推荐
│   │   ├── adapters/           # 外部适配器
│   │   │   ├── platforms/      # 平台适配器
│   │   │   │   ├── base.py     # 平台抽象接口
│   │   │   │   ├── mock.py     # Mock 实现
│   │   │   │   └── douyin_web.py # 抖音 Stub
│   │   │   └── llm/            # LLM 适配器
│   │   ├── infrastructure/     # 基础设施
│   │   │   ├── browser/        # Playwright 浏览器
│   │   │   ├── database/       # 数据库配置 + ORM
│   │   │   └── repositories/   # 数据仓库
│   │   └── schemas/            # API 请求/响应模型
│   ├── tests/
│   │   ├── unit/               # 单元测试
│   │   └── integration/        # API 集成测试
│   └── pyproject.toml
│
├── data/                       # 数据库文件目录
├── docs/                       # 项目文档
└── Makefile                    # 开发命令
```

## 环境要求

- **Python**: 3.12+
- **uv**: Python 包管理器 ([安装](https://docs.astral.sh/uv/))
- **Node.js**: 20+ (推荐通过 nvm 管理)
- **pnpm**: 包管理器 (`npm install -g pnpm`)
- **Playwright Chromium**: 浏览器自动化

## 快速开始

### 1. 安装依赖

```bash
# 一键安装所有依赖
make install

# 或分开安装
cd services/agent && uv sync --extra dev
cd apps/web && pnpm install
```

### 2. 启动后端

```bash
cd services/agent
export PATH="$HOME/.local/bin:$PATH"
uv run uvicorn app.main:app --reload
```

后端启动后访问 http://localhost:8000/api/health 验证。

### 3. 启动前端

```bash
cd apps/web
pnpm dev
```

前端启动后访问 http://localhost:5173。

### 4. Playwright 安装（如需浏览器功能）

```bash
cd services/agent
export PATH="$HOME/.local/bin:$PATH"
uv run playwright install chromium
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/research/tasks` | 创建研究任务 |
| POST | `/api/research/tasks/{id}/run` | 执行研究任务 |
| GET | `/api/research/tasks/{id}` | 查询任务状态 |
| GET | `/api/research/tasks/{id}/opportunities` | 获取结果列表 |

## 测试

```bash
# 运行所有测试
make test

# 仅单元测试
make test-unit

# 仅 API 测试
make test-api
```

## 代码检查

```bash
# 检查
make lint

# 自动修复
make lint-fix
```

## Golden Path 验证

完整的研究流水线：

```text
用户输入商业目标
    ↓
创建 Research Task
    ↓
Mock Planner 生成 16 个 SearchQuery
    ↓
Mock Collector 返回 30 个候选数据
    ↓
Normalizer 清洗 + URL 标准化
    ↓
Deduplicator 按 platform+URL 去重
    ↓
Buyer Scoring 七维评分 (ICP/Pain/Freq/Spend/Value/Build/Reach)
    ↓
Ranking 按总分降序排列，过滤低分
    ↓
写入 SQLite (research_tasks, account_candidates, buyer_scores, evidence)
    ↓
前端展示 TOP Opportunities (含评分、等级、证据、建议)
```

## Buyer Score V0 模型

满分 100 分：

| 维度 | 权重 | 说明 |
|------|------|------|
| ICP Fit | 25 | 业务类型匹配度 |
| Pain Intensity | 20 | 获客痛点强度 |
| Usage Frequency | 15 | 内容产出频次 |
| Existing Spend | 15 | 现有营销投入信号 |
| Customer Value | 10 | 客户价值 |
| Buy vs Build | 10 | 购买 vs 自研倾向 |
| Reachability | 5 | 可触达性 |

等级划分：S (90-100), A (80-89), B (65-79), C (<65)

## 当前状态

- **Feed 采集**：✅ 已验证 — 可稳定提取真实抖音视频数据（100% 提取成功率，100% URL 可追溯）
- **关键词搜索**：❌ 未通过 — 抖音反自动化检测阻断，无法稳定搜索
- **人工辅助采集**：✅ 当前方案 — 人工搜索 + CSV 导入 + 自动标准化去重
- **DouyinWebAdapter**：已通过 `NotImplementedError` 预留接口
- **LLM Provider**：当前使用 Mock，未绑定任何模型厂商

## 当前阶段

**OR-SPIKE-001C — Human-assisted Candidate Intake**

- Feed Collector: **PASS**
- Authenticated Search: **FAIL**（反自动化检测）
- Human-assisted Intake: **当前开发中**

## 下一步

完成 OR-SPIKE-001C 人工采集验证后，进入 **OR-SPIKE-002**：

> 真实候选数据 → ICP Filter → Buyer Intelligence → Buyer Score → Evidence → TOP20 → Precision@20
