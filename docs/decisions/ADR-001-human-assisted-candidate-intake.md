# ADR-001: Human-assisted Candidate Intake

**Date**: 2026-09-12  
**Status**: Accepted  
**Decision Maker**: Customer #0001 / Product Owner

## Context

OR-SPIKE-001B 验证了 Playwright Douyin Search 路线，结果如下：

### 验证结果

| 路线 | 结果 | 原因 |
|------|------|------|
| Feed Collector | ✅ PASS | 稳定可用，100% 成功率 |
| Authenticated Search | ❌ FAIL | 抖音反自动化检测阻断 |

### 失败原因

1. **反自动化检测**：Playwright Chromium 指纹被识别，多次访问后触发风控
2. **登录后页面跳转**：扫码登录后页面跳转到用户主页，非搜索结果页
3. **搜索结果渲染不稳定**：有时渲染有时不渲染
4. **视频身份缺失**：搜索卡片无 `/video/` 链接或视频 ID

## Decision

OpportunityRadar V0 不再要求"抖音关键词搜索必须全自动化"才能继续验证产品价值。

采用 **Human-assisted Candidate Intake** 方案：

```
人工搜索 → CSV 导入 → 自动标准化去重 → Candidate Dataset
```

## Why

当前要验证的核心问题是：

> 给 OpportunityRadar 200-300 个真实候选后，它能否把这些数据压缩成真正值得联系的 TOP20？

而不是：

> 如何自动化地从抖音搜索数据？

数据来源与产品核心 Intelligence 应该解耦。

## Consequences

### 正面
- Candidate Pipeline 不再与单个平台自动搜索强耦合
- 可以立即验证 Buyer Intelligence 和 Precision@20
- 数据来源更可靠（人工判断 + 自动标准化）

### 负面
- 短期不是全自动，需要人工搜索和填写 CSV
- 采集速度受限于人工操作
- 无法实时大规模获取数据

## Revisit

只有当 V0 Intelligence 和商业价值验证通过后，才重新评估：
- Browser Extension（浏览器扩展）
- Ego Lite（轻量级自动化）
- Official API（官方 API）
- Other Data Source（其他数据源）

## Related

- OR-SPIKE-001A: Feed Collector = PASS
- OR-SPIKE-001B: Authenticated Search = FAIL
- OR-SPIKE-001 Overall = CONDITIONAL PASS
- OR-SPIKE-001C: Human-assisted Intake = 当前工作包
- OR-SPIKE-002: Buyer Intelligence = 下一工作包
