# FUTURE.md — 暂不实现的功能

以下内容在当前 V0 阶段**明确不做**。记录于此以便后续阶段规划。

## V0 明确不做

- 真实抖音批量采集
- 验证码绕过 / 风控绕过
- 代理 IP 池
- 多账号群控
- 自动私信 / 自动评论 / 自动关注
- Android / 快手 / 小红书 适配
- 正式登录系统 / 支付系统
- 多租户 / 正式 CRM
- 完整 Sales Copilot
- 复杂 Agent Framework（LangChain/LangGraph）
- 大数据看板
- 自动销售执行

## 下一阶段：Technical Spike 001

**目标**：验证抖音 Web 能否通过浏览器 Worker 稳定完成搜索→采集→去重

技术风险验证点：
1. Playwright 能否稳定打开抖音搜索页
2. 能否提取搜索结果中的视频/账号信息
3. 能否跨多个关键词进行有效去重
4. 是否存在风控/验证码阻断

## V1 候选功能（需 Spike 001 验证通过后）

- 真实 DouyinWebAdapter 实现
- LLM 驱动的 Search Planner（动态生成搜索词）
- LLM 驱动的 Buyer Intelligence（替代确定性评分）
- 验证码检测与人工介入流程
- 采集进度实时推送（WebSocket）
- 更多平台适配器（快手、小红书）
- 正式用户系统
- 反馈闭环（标记有价值/无价值/已联系）
