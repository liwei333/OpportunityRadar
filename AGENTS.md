# AGENTS.md — OpportunityRadar 开发治理文件

> **本文件约束所有后续 AI 编程 Agent 的行为。**
> 任何 AI Agent 开始任务前，必须完整阅读本文件。
> 本文件优先级高于 Agent 自身的推断和偏好。

---

## 术语等级说明

| 等级 | 含义 |
|------|------|
| **MUST** | 绝对禁止违反。无例外。 |
| **MUST NOT** | 明确禁止的行为。 |
| **SHOULD** | 强烈推荐，除非有明确理由并在报告中说明。 |
| **MAY** | 可选，不影响验收。 |

---

## 一、项目定位与 Scope Lock

### 1.1 当前阶段

**OpportunityRadar MVP V0 — Technical Spike 001**

### 1.2 核心目标

> 根据用户商业目标，自动研究公开市场内容，完成真实数据收集、清洗、筛选、Buyer Intelligence、Buyer Score、Evidence 和 TOP Opportunity 输出。

### 1.3 第一客户

**Customer #0001 = 产品创建者本人**

### 1.4 第一商业目标

> 找到最可能购买 OpportunityRadar 的目标客户，并最终验证至少 1 个真实付费客户。

### 1.5 Scope Lock

AI Agent MUST NOT 擅自扩大当前阶段范围。
当前产品形态是 **AI Research Agent**，MUST NOT 变成：

- 爬虫后台
- CRM 系统
- 群控获客工具
- 自动化营销平台
- 数据大屏

---

## 二、当前 P0 优先级

```
真实数据有效性 > 数据清洗与可追溯 > AI筛选准确率
> Buyer Score可信度 > 商业验证 > UI美观
```

### 核心原则

> **页面丑没有关系，真实数据无效则项目失败。**

---

## 三、当前 Roadmap Gate

### 当前 Gate

**OR-SPIKE-001 — Douyin Web Real Data Collector**

目标：验证抖音 Web 能否通过 Playwright Browser Worker 稳定完成：

```
关键词搜索 → 批量加载 → 结构化提取视频/账号 → 跨关键词去重
```

### Gate 流转规则

```
OR-SPIKE-001 PASS
    ↓
OR-SPIKE-002: 真实候选 → ICP Filter → BUYER/COMPETITOR/PARTNER
    → Buyer Score → Evidence → TOP20 → Precision@20
    ↓
Precision@20 >= 70%
    ↓
真实销售验证
    ↓
≥1 个真实 ¥499 Early Access 付费客户
```

Agent MUST NOT 跳过当前 Gate，MUST NOT 提前实现后续阶段功能。

---

## 四、禁止擅自开发的功能

未经明确工作包授权，MUST NOT 开发以下功能：

- 多租户 / SaaS 正式账户
- 正式登录系统 / 支付系统 / 订阅套餐系统
- Android Agent
- 快手 / 小红书 / 视频号适配
- 自动私信 / 自动评论 / 自动关注 / 自动点赞 / 自动加微信
- CRM 大系统 / 团队权限
- 完整销售自动化 / 复杂数据大屏
- 推荐系统
- 正式多 Agent 框架 / LangChain / LangGraph 重构
- 微服务拆分 / Redis 集群 / Kafka / Elasticsearch / Kubernetes

如果认为未来有价值，MAY 记录到 `docs/FUTURE.md`，MUST NOT 顺手实现。

---

## 五、工作包驱动开发

### 5.1 启动前四问

AI Agent 每次开始任务前，MUST 回答：

1. **当前工作包是什么？**
2. **当前工作包解决哪个问题？**
3. **不属于本工作包的内容有哪些？**
4. **验收标准是什么？**

### 5.2 冲突处理

如果任务描述和仓库文档（README.md、MVP Golden Path、FUTURE.md）冲突：

```
记录冲突 → 采用最小改动 → 在最终报告中说明
```

如果冲突严重影响正确性，MUST 请求人工决策，MUST NOT 自行选择。

---

## 六、禁止需求漂移

AI Agent MUST NOT 因为以下理由扩大实现范围：

- "这样更完整"
- "以后会需要"
- "顺便可以做"
- "架构更漂亮"
- "最佳实践应该这样"

### 遵循原则

```
Vertical Slice > 完整平台
真实验证 > 架构完美
最小实现 > 提前设计未来
```

---

## 七、事实与推断分离

OpportunityRadar 所有数据 MUST 明确区分：

| 标签 | 含义 | 示例 |
|------|------|------|
| **RAW FACT** | 原始页面直接可见的事实 | 页面写着"服务过100家制造企业" |
| **DERIVED FACT** | 基于 RAW FACT 直接计算的 | 该账号有3个内容分区 |
| **AI INFERENCE** | AI 基于证据的合理推断 | "可能存在高频行业研究需求" |
| **ASSUMPTION** | 未经证实的假设 | "该客户应该有预算" |
| **UNKNOWN** | 无法从现有信息确定 | 未提及企业规模 |

### 规则

- RAW FACT 可以记录为事实。
- AI INFERENCE MUST NOT 写入 Raw Data 作为事实。
- MUST NOT 将 "100家制造企业" 润色为 "100个长期付费客户"。
- Buyer Intelligence 产生的推断 MUST 标为 `AI INFERENCE`。

---

## 八、禁止数据幻觉

### 8.1 原始采集数据

LLM MUST NOT 对原始采集数据进行：

- 补全
- 猜测
- 润色
- 修复
- 伪造

### 8.2 缺失字段处理

无法获得的字段 MUST 设为 `null` 或 `unknown`，MUST NOT 猜一个值。

例如：无法获得 `follower_count`、`published_at`、`comment_count`、`account_id` 时，MUST 设为 `null`。

---

## 九、Mock 与 Real Data 严格隔离

### 9.1 核心规则

```
Mock Data ≠ Real Data
```

### 9.2 识别规则

所有 Mock 必须能够一眼识别：

- `MockPlatformAdapter`
- `MockLLMProvider`
- `mock_data.py`
- `MockCollector`
- `MockPlanner`

### 9.3 禁止静默 Fallback

正式运行真实研究任务时，MUST NOT 静默 fallback 到 Mock。

如果真实 Collector 失败，正确结果是 `FAILED`，MUST NOT 自动换 Mock 让页面看起来正常。

---

## 十、禁止"演示成功冒充真实成功"

以下情况 MUST NOT 宣布 `PASS` / `DONE` / `COMPLETE` / `PRODUCTION READY`：

- 只使用 Mock 数据
- 只跑成功一次
- 只静态检查代码
- 没有运行测试
- 没有真实浏览器执行
- 数据量不足
- selector 是猜出来的
- 人工相关性还没审核
- Buyer Score 没证据
- API 只写了没有真正请求
- UI 显示成功但后端没跑

---

## 十一、证据优先

所有关键判断 MUST 遵循：

```
Conclusion → Reason → Evidence → Source
```

### Buyer Score 证据要求

禁止黑盒评分。禁止只输出 `Score = 92` 没有解释。

每个 S/A 级潜客 MUST 提供至少 **2 条有效证据**，包含：

```
Buyer Score = 92
ICP Fit = 25/25
原因：……
Evidence: ……
Source URL: ……
```

---

## 十二、Buyer Score 规则

### V0 评分模型

| 维度 | 权重 |
|------|-----:|
| ICP Fit | 25 |
| Pain / Problem Intensity | 20 |
| Usage Frequency | 15 |
| Existing Spend Signal | 15 |
| Customer Value | 10 |
| Buy-vs-Build Fit | 10 |
| Reachability | 5 |
| **Total** | **100** |

### 等级

| 等级 | 分数范围 |
|------|---------|
| S | 90–100 |
| A | 80–89 |
| B | 65–79 |
| C | <65 |

### 权重保护

未经明确工作包要求，MUST NOT 擅自修改权重。

如果发现问题，MUST 记录：`建议修改 + 证据 + 影响`，等待后续任务。

---

## 十三、对象类型分类

不能把所有高相关对象都当成客户。MUST 至少分类为：

| 类型 | 含义 |
|------|------|
| **BUYER** | 潜在客户 |
| **COMPETITOR** | 竞品提供者 |
| **PARTNER** | 合作伙伴 |
| **IRRELEVANT** | 不相关 |
| **UNKNOWN** | 无法判断 |

### 规则

- Fit 高 ≠ Buyer Score 高
- 已自研类似系统的企业 → `COMPETITOR` 或 `PARTNER`，MUST NOT 进入 Buyer TOP List

---

## 十四、数据采集规范

### 技术栈

```
Python + Playwright + Chromium + DOM/Semantic Extraction + Polars
```

### 提取优先级

```
DOM > href > role > aria > stable attributes > relative DOM relationships
```

### 禁止默认使用

MUST NOT 默认使用 OCR / Vision Model，除非明确工作包要求。

---

## 十五、禁止平台风控对抗

MUST NOT 实现以下功能：

- 验证码破解
- 绕登录验证
- 反检测绕过
- 代理池 / 账号池
- 设备指纹伪造
- 接口签名破解
- 逆向私有 API
- 模拟批量营销行为

### 出现验证时的流程

```
Pause → Human Intervention → Resume
```

---

## 十六、Selector 规则

### 集中管理

抖音等页面 selector MUST NOT 散落代码库，MUST 集中到：

- `Platform Adapter`
- 或专门的 `selectors.py`

### 优先级

```
semantic > href pattern > role > stable attribute > relative structure
```

### 失败诊断

selector 失败时 MUST 保存诊断：

```
URL + query + timestamp + screenshot + relevant DOM + exception
```

MUST NOT 直接猜新的 selector 并宣布修复。

---

## 十七、原始数据永远保存

任何真实 Research Run，Raw Data MUST NOT 被覆盖。

### 存储结构

```
data/runs/<run_id>/
    ├── raw/           # 原始采集数据
    ├── normalized/    # 清洗后数据
    ├── errors/        # 错误记录
    ├── screenshots/   # 诊断截图
    └── report.md      # 运行报告
```

### 规则

- Normalized Data MUST NOT 覆盖 Raw Data
- Raw Data 永远只读

---

## 十八、Data Quality Gate

进入 AI Buyer Intelligence 前，真实数据 MUST 通过 Data Quality Gate。

### 关注指标

| 指标 | 目标 |
|------|------|
| URL 可追溯率 | ≥ 95% |
| 结构化提取成功率 | ≥ 80% |
| 人工基础相关率 | ≥ 80% |
| Extraction Success Rate | 监控中 |
| Duplicate Rate | 监控中 |
| Missing Field Rate | 监控中 |

### 规则

如果未达到目标，MUST NOT 用漂亮的 Buyer Score 掩盖数据问题。

---

## 十九、人工评估不能被 AI 替代

定义为人工审核的指标，AI Agent MUST NOT 自行填写：

- `manual_relevant`
- `Precision@20`

MUST 留空等待 Customer #0001。

### 核心人工指标

| 指标 | 最低 | 目标 |
|------|------|------|
| Precision@20 | 70% | 80% |

---

## 二十、测试纪律

### 修改前建立 Baseline

每次修改前 MUST 至少执行：

```bash
make test        # pytest
make lint        # ruff
make build-web   # 前端构建（如涉及前端）
```

### 修改后重新执行

修改后 MUST 重新执行上述命令。

### 最终报告必须写真实结果

```
pytest:     <实际输出>
ruff:       <实际输出>
frontend build: <实际输出>
```

MUST NOT 写"应该能通过"，只能写实际运行结果。

---

## 二十一、禁止修改测试来"让测试通过"

如果测试失败：

1. MUST 优先修实现
2. MUST NOT 删除测试 / 降低断言 / skip 失败测试 / 改测试数据掩盖 bug

除非测试本身确实错误。修改测试时必须说明：

```
为什么测试错了 + 修改依据
```

---

## 二十二、Live Test 与普通测试分离

真实平台测试（如 Douyin Web）MUST 标记为 `live`：

```bash
pytest -m live      # 真实平台
pytest              # 普通测试（不访问真实平台）
```

MUST NOT 让普通 CI 每次都访问真实平台。

---

## 二十三、错误必须暴露

MUST NOT 静默失败：

```python
# 禁止
try:
    ...
except Exception:
    return []
```

真实采集失败 MUST 产生：

- 结构化错误
- 日志
- run status 更新
- 诊断 artifact

---

## 二十四、LLM 使用规范

### LLM 负责

- 理解 / 分类 / 推断 / 总结
- 评分辅助 / 证据解释

### LLM 不负责

- 创造事实
- 补齐缺失字段
- 修改 Raw Data
- 伪造 Source

### 输出校验

所有结构化输出 MUST 使用 Pydantic 校验。
解析失败 MUST 显式失败或重试，MUST NOT 吞掉错误。

---

## 二十五、Prompt 管理规范

MUST NOT 将大量 Prompt 散落在 service 文件。

如果进入真实 Intelligence 开发，Prompt 应集中管理，至少明确：

```
purpose + input contract + output schema + version
```

---

## 二十六、Python 开发规范

### 技术栈

```
Python 3.12+ / FastAPI / Pydantic v2 / SQLAlchemy 2.x / Polars / Playwright / pytest / ruff
```

### 要求

- type hints
- async-first for I/O
- small functions
- clear boundaries
- structured exceptions

### 禁止

- 巨大 `utils.py` / 巨大 `service.py`
- platform logic 混入 domain
- database 逻辑混入 route

---

## 二十七、前端开发规范

### 技术栈

```
Vue 3 / TypeScript / Vite / Pinia / Vue Router / Element Plus
```

### 原则

```
数据真实性 > 交互完整 > 视觉美观
```

### 禁止伪造

MUST NOT 为了匹配原型伪造后端真实状态。

后端返回 `FAILED`，前端 MUST NOT 显示 `Research completed`。

---

## 二十八、禁止过度架构

当前阶段 MUST NOT 引入：

- DDD 完整版
- CQRS / Event Sourcing
- 复杂消息总线
- 微服务
- 多 Agent orchestration 框架

### 原则

> **最小足够架构。** 保留清晰模块边界即可。

---

## 二十九、修改原则

```
优先修改现有代码 > 增加最小新模块 > 大规模重构
```

大规模重构前 MUST 证明：当前架构已经阻塞当前工作包。否则 MUST NOT 重构。

---

## 三十、Git 纪律

MUST NOT：

- 提交 secret
- 提交 browser profile
- 提交 cookies / 真实登录态
- 提交大型 Raw Data（除非仓库明确要求）
- 删除用户未授权删除的文件
- 覆盖工作区已有用户修改

---

## 三十一、文档与代码一致

如果实现改变当前真实状态，MUST 同步更新：

- `README.md`
- 相关 `docs/`

例如：DouyinWebAdapter 已从 Stub 变成可运行，README MUST NOT 继续写 `DouyinWebAdapter = Stub`。

---

## 三十二、AI 最终汇报格式

所有开发任务结束时，MUST 输出以下结构：

### 1. Scope
本次实际做了什么。

### 2. Changed Files
实际修改文件列表。

### 3. What Works
已经**真实验证**的能力。

### 4. What Does NOT Work
明确未完成内容。

### 5. Tests
真实命令与结果：
```
pytest:     <结果>
ruff:       <结果>
frontend build: <结果>
```

### 6. Data / Evidence
如果涉及真实数据：实际数量、质量指标和证据路径。

### 7. Known Risks
已知问题。

### 8. Gate Decision
如果工作包定义 Gate，只能输出：`PASS` / `CONDITIONAL PASS` / `FAIL`

### 9. Next Recommended Work Package
只推荐下一工作包，MUST NOT 擅自执行。

---

## 三十三、Anti-Hallucination Rules

AI Agent **绝对禁止**以下行为：

1. 未执行命令却说执行过
2. 未打开页面却描述页面结构
3. 未获取真实数据却说是真实数据
4. Mock 数据冒充真实数据
5. 未找到证据却编造 Evidence
6. 未确认企业情况却写成确定事实
7. 未运行测试却说测试通过
8. 未连续运行 3 次却说稳定
9. 用户人工指标由 AI 自己填写
10. 未完成工作包验收却宣布 PASS
11. 因为"看起来合理"而猜 Selector / URL / 字段 / ID
12. 为让 Demo 好看而伪造指标
13. 把未来计划写成当前已实现能力

### 诚实表达规则

| 情况 | 必须写 |
|------|--------|
| 不知道 | `UNKNOWN` |
| 没验证 | `NOT VERIFIED` |
| 只是推断 | `INFERENCE` |

---

## 三十四、优先级决策规则

AI 遇到多个可能方案时，按以下顺序选择：

```
真实数据 > 可验证 > 可追溯 > 正确性 > 简单 > 速度 > 架构优雅 > UI美观
```

---

## 三十五、当前真实状态快照

> 本节记录仓库当前真实状态，防止 Agent 做出错误假设。

### 已运行组件

| 组件 | 状态 |
|------|------|
| MockPlanner | 运行中，返回 16 个固定搜索词 |
| MockCollector | 运行中，使用 MockPlatformAdapter |
| DataCleaner / URLNormalizer | 运行中 |
| AccountDeduplicator | 运行中 |
| BuyerScoringService | 运行中，确定性评分 |
| OpportunityRanker | 运行中 |
| ResearchService 流水线 | 运行中（全 Mock 链路） |

### 未运行组件

| 组件 | 状态 |
|------|------|
| DouyinWebAdapter | **Stub** — 所有方法抛 `NotImplementedError` |
| PlaywrightBrowserWorker | 基础框架存在，click/fill/scroll/extract **未实现** |
| LLM Provider | **Mock** — `LLM_PROVIDER=mock` |

### 数据存储

- SQLite via aiosqlite
- 数据库文件：`data/opportunity_radar.db`

### 测试

- pytest + pytest-asyncio（asyncio_mode = auto）
- 单元测试：buyer_scoring / deduplicator / normalizer / ranking
- 集成测试：API 层
- ruff 代码检查

---

## 三十六、作用域

本文件默认覆盖整个 OpportunityRadar 仓库。

如果未来子目录需要特殊规则，可增加：

- `services/agent/AGENTS.md`
- `apps/web/AGENTS.md`

但当前以本文件为准。

---

## 三十七、与现有文档的关系

| 文档 | 关系 |
|------|------|
| `README.md` | 项目概览，状态描述 |
| `docs/OpportunityRadar_MVP_Golden_Path_V0.1.md` | MVP 验收标准权威来源 |
| `docs/FUTURE.md` | 暂不实现功能清单 |
| 本文件 | **开发治理规则，约束 Agent 行为** |

当本文件与 Golden Path 文档冲突时，以 Golden Path 文档的产品定义为准，以本文件的治理规则为行为约束。

---

> **本文件是活的文档。当项目 Gate 推进或治理规则变化时，MUST 同步更新本文件。**
