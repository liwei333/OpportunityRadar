# OpportunityRadar MVP Golden Path & Acceptance Criteria

**版本：V0.1**  
**阶段：MVP 能力验证**  
**第一客户：产品创建者本人（Customer #0001）**

---

## 1. MVP 唯一目标

验证 OpportunityRadar 是否能够：

> 用户只提供一个自然语言商业目标，Agent 自主完成市场研究、批量收集、筛选、潜客评分和证据整理，最终找出真正值得联系的潜在付费客户。

第一个真实任务：

> **寻找最可能购买 OpportunityRadar 的 B2B / 工业品短视频代运营及企业获客服务商。**

MVP 不以“功能完整”为成功标准。

核心验证：

1. **智能**：用户不需要自己设计关键词和筛选规则。
2. **高效**：Agent 能将大量公开信息压缩成少量值得看的结果。
3. **有效**：最终 TOP 潜客确实值得联系。

---

## 2. Golden Path

### Step 1：用户输入商业目标

用户只输入自然语言：

> 帮我寻找最可能购买 OpportunityRadar 的客户，优先寻找服务 B2B、制造业、工业品企业的短视频代运营和企业获客公司。

用户不需要配置：

- 搜索关键词
- 搜索数量
- 视频数量
- 粉丝区间
- 筛选规则
- AI Prompt

---

### Step 2：Research Planner 理解任务

Agent 自动识别：

#### 产品

OpportunityRadar

#### 产品价值

- 市场数据收集
- 潜在客户发现
- 信息筛选
- Buyer Score
- 推荐依据
- 销售辅助

#### ICP

优先：

- B2B 短视频代运营公司
- 工业品短视频服务商
- 企业短视频获客团队
- 制造业营销服务商

典型特征：

- 同时服务多个企业客户
- 重复进行行业调研
- 需要竞品研究
- 需要客户画像
- 需要内容选题
- 需要寻找潜在线索

---

## 3. Search Planning

Agent 自主形成不少于：

**10 个有效研究方向。**

目标：

**20～30 个研究方向。**

搜索维度至少包含：

### 直接业务词

- 企业短视频获客
- 短视频代运营
- B2B短视频
- 工业品短视频
- 制造业短视频运营

### 问题词

- 企业短视频怎么获客
- 工业品怎么做抖音
- ToB短视频怎么找客户
- 短视频精准获客

### 场景词

- 制造业抖音运营
- 机械设备短视频
- 工厂短视频运营
- 企业账号矩阵

### 动态扩展

搜索过程中发现：

> 工业品获客、GEO、矩阵营销等新概念

Agent 可以创建新的搜索分支。

---

## 4. Browser Research

### V0 数据源

仅：

**抖音 Web**

暂不支持：

- 快手
- 小红书
- 视频号
- Android
- 官方 API

### 浏览器 Agent 需要完成

```text
Search Query
    ↓
打开抖音搜索
    ↓
加载搜索结果
    ↓
提取候选内容
    ↓
识别作者
    ↓
继续滚动
    ↓
切换下一个Query
```

目标：

#### 最低验收

≥100 个候选对象

#### 推荐目标

200～300 个候选对象

---

## 5. Collector

第一版只收集影响 Buyer Score 的字段。

### Account

- platform
- account_name
- profile_url
- bio
- follower_count（可获得时）
- business_type
- location（公开且有价值时）

### Content

- title/text
- description
- url
- published_at
- engagement
- source_query

### Evidence

- evidence_text
- source_url
- evidence_type
- extracted_at

禁止为了“数据量”收集无关字段。

---

## 6. Normalize & Deduplicate

系统必须：

- 视频去重
- 账号去重
- 搜索词交叉结果合并
- 同一企业不同账号尽可能归并
- 清除明显无关内容

例如：

```text
原始候选：267

↓ 去重

独立候选：183

↓ 相关性筛选

目标相关：72
```

---

## 7. Relevance Filter

Agent 第一轮只回答：

> 这个对象是不是 OpportunityRadar 潜在客户？

分类：

### HIGH

高度符合 ICP。

### MEDIUM

可能符合，需要进一步分析。

### LOW

明显不匹配。

### COMPETITOR

已经提供类似：

- AI获客工具
- 评论线索系统
- 自动化获客平台
- Research Agent

默认不进入 Buyer TOP List。

但进入：

**Competitor Pool**

---

## 8. Buyer Intelligence

对 HIGH / MEDIUM 候选进一步分析：

### 业务模型

它靠什么赚钱？

### 服务对象

是否服务企业？

### 客户数量信号

是否存在多项目运营需求？

### 重复研究需求

是否反复进行：

- 行业研究
- 竞品研究
- 内容策划
- 客户画像
- 潜客寻找

### Existing Spend Signal

是否存在：

- 专业运营团队
- 数据工具
- AI工具
- CRM
- 广告投放
- 内容团队
- 营销软件

### Buy vs Build

它更可能：

- 买我们的产品

还是：

- 自己开发类似产品？

---

## 9. Buyer Score V0

满分：

**100**

评分模型：

| 维度 | 权重 |
|---|---:|
| ICP Fit | 25 |
| Pain / Problem Intensity | 20 |
| Usage Frequency | 15 |
| Existing Spend Signal | 15 |
| Customer Value | 10 |
| Buy-vs-Build Fit | 10 |
| Reachability | 5 |

### Score Level

#### S

90～100

第一优先级联系。

#### A

80～89

高价值潜客。

#### B

65～79

观察 / 次级联系。

#### C

<65

暂不联系。

---

## 10. Evidence Requirement

**禁止黑盒评分。**

每个 S/A 级潜客至少必须提供：

### 2 条以上有效证据。

例如：

> 明确提供工业制造企业短视频代运营服务。

来源：

XX视频 / 官网 / 主页内容

---

> 同时服务多个企业客户，需要重复做行业和选题研究。

来源：

XX案例 / 公开视频

---

每一个核心判断都必须能够回答：

> **为什么？**

---

## 11. Opportunity Ranking

Agent 最终输出：

## TOP 20 Buyers

每个对象必须包括：

```text
公司 / 账号

Buyer Score：92

等级：
S

业务：
工业品短视频代运营

为什么推荐：
1.
2.
3.

核心需求假设：
……

Existing Spend信号：
……

Buy-vs-Build：
……

主要风险：
……

证据：
……

推荐动作：
优先联系
```

---

## 12. Sales Playbook

对 TOP20 每一家生成：

### Contact Reason

为什么现在应该联系它？

### Value Hypothesis

OpportunityRadar 最可能帮它解决什么？

### Demo Scenario

最适合拿什么真实业务给它演示？

例如：

> 帮它寻找“正在做短视频但效果不好”的激光设备厂家。

---

## 13. Initial Outreach

每个 TOP 潜客生成一条：

**个性化首次触达话术。**

要求：

- 2～4 句
- 不群发感
- 不堆功能
- 必须引用一个真实客户信号
- 只推动一个下一步动作

禁止：

> 我们是一款领先AI大数据精准获客平台……

推荐结构：

```text
我看到你们主要在做【具体业务】。

我们最近做了一个AI市场研究Agent，可以根据目标自动研究短视频市场，把大量内容筛成真正值得联系的客户。

如果你愿意，我可以直接拿你们现在服务的一个行业跑一次。
```

---

## 14. Conversation Copilot

客户回复后，用户可以直接粘贴客户原话。

Agent输出：

### Intent

客户真正表达什么？

### Deal Stage

例如：

- CONTACTED
- INTERESTED
- EVALUATING
- DEMO
- PRICING
- NEGOTIATION
- WON
- LOST

### Objection

例如：

- 价格
- 准确率
- 飞瓜替代
- AI替代
- 数据来源
- 产品成熟度

### Next Best Action

只给一个最推荐动作。

### Reply

生成：

**2～4 句精简回复。**

---

## 15. Pricing Copilot

V0 默认商业策略：

### Standard Price

**¥999/月**

### Founder Early Access

前 10 个合作客户：

**¥499/月**

### 免费策略

只提供：

**一次真实业务 Demo**

不提供长期免费使用。

---

## 16. Feedback Loop

Customer #0001 可以标记每一个推荐：

- 有价值
- 无价值
- 已联系
- 已回复
- 有兴趣
- Demo
- 已报价
- 已成交
- 已失败

失败可标记：

- ICP错误
- 无需求
- 无预算
- 自研
- 已有替代品
- 联系不到
- 价格
- 产品能力不足

这些反馈未来用于校准 Buyer Score。

---

## 17. V0 核心验收指标

### A. 智能

用户只输入：

**1 条自然语言需求**

Agent必须自动完成：

- ICP识别
- 搜索规划
- 扩词
- 数据收集
- 筛选
- 评分
- 证据生成

#### PASS

≥10 个有效研究方向。

#### TARGET

20～30 个。

---

## 18. 高效

### 最低候选量

≥100

### 推荐候选量

≥200

最终必须压缩为：

≤20 个重点推荐。

例如：

```text
250个候选

↓

76个相关

↓

31个高潜

↓

TOP20
```

目标：

> **用户不用自己阅读原始250条信息。**

---

## 19. 有效

Customer #0001 人工审核 TOP20。

判断：

> 如果这是我的真实销售业务，我是否愿意花时间联系它？

### 核心指标

#### Precision@20

最低：

**70%**

即：

```text
TOP20
↓
至少14个
↓
真正值得联系
```

### TARGET

**80%**

即：

16 / 20。

---

## 20. Evidence Quality

TOP20中：

≥90%

必须拥有：

**至少2条真实可追溯证据。**

不允许：

> “AI推测该公司可能需要”。

必须存在具体来源。

---

## 21. Agent Quality Gate

如果：

### Precision@20 < 70%

禁止进入销售阶段。

继续优化：

- Search Planner
- ICP
- Filter
- Buyer Score

如果：

### Precision@20 ≥70%

进入真实市场验证。

---

## 22. 商业验证

第一轮：

### Contact

≥10 家

### 有效回复

目标：

≥5

### 愿意看真实 Demo

目标：

≥3

### 进入报价

目标：

≥2

### 第一阶段最终目标

**≥1 个真实付费用户。**

目标价格：

**¥499 Early Access**

---

## 23. MVP Success

OpportunityRadar V0 真正成功必须同时满足：

### 产品能力

Precision@20 ≥70%

以及：

### 商业能力

至少：

**1 × ¥499 真实成交**

只有同时达到：

```text
找得准
+
有人付钱
```

才进入 V1。

---

## 24. V0 明确不做

- 多租户
- SaaS正式账户
- 支付系统
- Android
- 自动私信
- 自动评论
- 自动关注
- CRM系统
- 微信自动读取
- 多平台完整适配
- 团队权限
- 手机App
- 正式套餐体系
- 大数据看板
- 自动销售执行

---

## 25. V0 产品原则

OpportunityRadar 的核心不是：

> 收集更多数据。

而是：

> **减少用户必须亲自阅读的数据。**

不是：

> AI给一个数字。

而是：

> **评分 + 原因 + 证据。**

不是：

> 推荐更多客户。

而是：

> **推荐更少、但更值得行动的客户。**

不是：

> 帮用户发更多营销消息。

而是：

> **帮助用户找到应该联系的人，并提高每一次沟通的质量。**

---

## 26. V0 North Star

第一阶段唯一北极星：

> **OpportunityRadar 推荐的 TOP 潜客中，有多少最终被用户认为值得行动？**

产品最终北极星：

> **OpportunityRadar 发现的机会，最终有多少转化为真实商业结果？**

---

## 27. 下一步

完成本文件后，立即进入：

**Technical Spike**

只验证当前最大技术风险：

> **抖音 Web 能否通过浏览器 Worker 稳定完成：关键词搜索 → 批量加载 → 结构化提取视频/账号 → 跨关键词去重。**

Technical Spike 暂时：

- 不做复杂 UI
- 不做销售 Copilot
- 不做评论深挖
- 不做多平台
- 不做正式 SaaS 架构

当数据采集黄金链路验证通过后，再进入正式 MVP 工程开发。
