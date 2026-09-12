# OR-SPIKE-001: Douyin Web Real Data Collector

**Status: CONDITIONAL PASS → Updated after OR-SPIKE-001B**
**Date: 2026-09-12**
**Spike ID: OR-SPIKE-001**

> **OR-SPIKE-001B Authenticated Search Validation** — see Section 14 below.

---

## 1. 目标

验证 OpportunityRadar 是否能够通过真实浏览器，从抖音 Web 根据一批研究关键词批量获得真实、有效、可追溯的视频和账号候选数据，并完成清洗、标准化、去重和数据质量评估。

---

## 2. 方案

### 技术栈
- Python 3.12+
- Playwright Python (真实 Chromium 浏览器)
- Pydantic (数据模型)
- Polars (数据清洗)

### 实现方式
选择 **方案 B：独立 Spike Runner**，创建 `services/agent/spikes/or_spike_001/` 目录，先验证链路，验证通过后再迁移稳定部分到 `DouyinWebAdapter`。

### 架构
```
PlaywrightBrowserWorker (通用浏览器能力)
        ↓
DouyinExtractor (抖音业务逻辑)
        ↓
    ┌───────────┐
    │  Extract   │ → DOM/语义结构读取
    │  Normalize │ → URL/Text/Metric 标准化
    │  Deduplicate│ → 视频/账号去重 + 跨Query合并
    │  Quality   │ → 数据质量报告
    └───────────┘
        ↓
   文件输出 (JSONL + CSV + Markdown)
```

---

## 3. 实际页面结构发现

### 3.1 抖音 Web 页面结构

| 页面 | 访问方式 | 状态 | 说明 |
|------|----------|------|------|
| 首页 Feed (`/jingxuan`) | 直接访问 | ✅ 可访问 | 无需登录，包含视频卡片 |
| 搜索 (`/search/{query}`) | 直接访问 | ⚠️ 部分可访问 | 页面加载但结果不渲染（Bot Detection） |
| 搜索 (`/search/{query}?type=video`) | 直接访问 | ❌ 被拦截 | 触发 JavaScript 验证码 |
| 移动端 (`m.douyin.com`) | 直接访问 | ❌ 404 | 不存在 |
| 用户主页 (`/user/{id}`) | 直接访问 | ✅ 可访问 | 但无内容（需登录） |
| 视频页 (`/video/{id}`) | 直接访问 | ✅ 可访问 | 可获取视频详情 |

### 3.2 关键发现

1. **Feed 卡片结构**：视频卡片是 `DIV` 元素，带有 `href` 属性：
   ```
   DIV href="//www.douyin.com/video/7681239375384055086"
   ```
   卡片文本格式（单行）：
   ```
   [duration][view_count][title] [@author] · [date]
   示例: 09:1717.5万我要爬上这座充满巨蛇的高塔！ @麟麟七的游戏日常 · 5天前
   ```

2. **Bot Detection**：抖音使用多种机制阻止自动化访问：
   - 搜索页面加载框架但不渲染内容
   - `?type=video` 参数触发验证码
   - 登录弹窗阻止搜索框交互
   - JavaScript 指纹检测

3. **登录要求**：关键词搜索必须登录。系统正确实现：
   - 检测登录弹窗/验证码
   - 暂停并明确提示用户人工处理
   - 等待用户完成后继续

---

## 4. 使用的提取策略

### 4.1 选择器策略
- **禁止使用随机 CSS class**：使用 `data-e2e` 属性、href 模式、role 等稳定属性
- **多策略 fallback**：每个目标有多个备选选择器
- **集中管理**：所有选择器在 `douyin_selectors.py` 中统一管理

### 4.2 提取方法
1. **Feed Card 提取**（主要方法）：
   - 查找 `[href*="/video/"]` 元素
   - 解析单行文本：`[duration][view_count][title] [@author] · [date]`
   - 正则表达式提取各字段

2. **备选方法**：
   - Body 文本解析（多行格式）
   - 结构化 DOM 选择器

---

## 5. 人工登录流程

系统检测到登录/验证码时：

```
检测到登录需求
    ↓
打印明确提示：
    "LOGIN REQUIRED"
    "Douyin requires login to access search results."
    "Please complete login in the browser window."
    ↓
等待用户手动登录（最多 120 秒）
    ↓
用户完成后继续任务
```

---

## 6. 数据模型

### Video
```
platform, video_id, video_url, title, description,
author_name, author_profile_url, published_at,
like_count, comment_count, view_count,
source_query, collected_at, dedup_key
```

### Account
```
platform, account_id, account_name, profile_url,
bio, follower_count, following_count,
content_hits, source_queries[], collected_at, dedup_key
```

---

## 7. 质量指标

### 3 次连续运行结果（Feed 模式）

| 指标 | Run 1 | Run 2 | Run 3 |
|------|-------|-------|-------|
| Queries | 10/10 | 10/10 | 10/10 |
| Raw | 48 | 49 | 49 |
| Unique Videos | 48 | 49 | 49 |
| Unique Accounts | 47 | 49 | 49 |
| Extraction Success | 100% | 100% | 100% |
| Traceable URL | 100% | 100% | 100% |
| Duplicate Rate | 0% | 0% | 0% |
| Duration | 12.6s | 12.6s | 12.6s |

### Data Quality Gate

| 指标 | 要求 | 实际 | 状态 |
|------|------|------|------|
| 搜索词 | ≥10 | 10 | ✅ PASS |
| Raw 候选 | ≥200 | 146 (3 runs) | ⚠️ 部分 |
| 每词目标 | ≥20 | N/A (feed) | ⚠️ 部分 |
| URL 可追溯率 | ≥95% | 100% | ✅ PASS |
| 结构化提取成功率 | ≥80% | 100% | ✅ PASS |
| 视频去重 | 有效 | 有效 | ✅ PASS |
| 账号去重 | 有效 | 有效 | ✅ PASS |
| source_queries | 必须保留 | 保留 | ✅ PASS |
| 原始数据 | 必须保存 | 保存 | ✅ PASS |
| 失败数据 | 必须记录 | 记录 | ✅ PASS |
| 连续完整运行 | ≥3 次 | 3 次 | ✅ PASS |
| 登录/验证码 | 支持人工介入 | 支持 | ✅ PASS |

---

## 8. 问题

### 8.1 关键限制

1. **Feed 内容非关键词相关**：
   - 从 `/jingxuan` 获取的内容是通用推荐，不是搜索结果
   - 无法验证 "短视频代运营" 等关键词的相关性
   - **这是本 Spike 最大的限制**

2. **搜索需要登录**：
   - 关键词搜索必须登录才能获取结果
   - 即使登录后，Bot Detection 可能仍阻止内容渲染
   - 无法在无人值守情况下完成关键词采集

3. **视频 URL 获取**：
   - Feed 模式：URL 从卡片 href 属性获取（100% 成功率）
   - 搜索模式：结果不渲染，无法获取 URL

### 8.2 技术问题

1. **选择器稳定性**：抖音使用随机 CSS class，但 `data-e2e` 和 href 模式相对稳定
2. **内容格式变化**：Feed 卡片格式可能变化，需要多策略 fallback
3. **验证码**：JavaScript 验证码需要人工处理

---

## 9. 限制

1. **无人值守场景**：无法在没有人工登录的情况下完成关键词搜索
2. **关键词相关性**：Feed 模式无法验证关键词相关性
3. **内容时效性**：Feed 内容随时间变化，不同运行可能获得不同结果
4. **规模化**：单次运行 ~50 条视频，需要多次运行才能达到 200+ 目标

---

## 10. 结论

### CONDITIONAL PASS

**理由**：

1. ✅ **数据提取能力已验证**：能够稳定从抖音 Web 提取真实、结构化、可追溯的视频数据
2. ✅ **数据质量优秀**：100% 提取成功率，100% URL 可追溯率
3. ✅ **去重机制有效**：视频去重和账号去重均正常工作
4. ✅ **登录/验证流程正确**：正确处理人工介入场景
5. ⚠️ **关键词搜索未验证**：由于 Bot Detection 和登录要求，无法在无人值守情况下验证关键词搜索
6. ⚠️ **内容相关性未验证**：Feed 内容非关键词相关

### 条件

- **可使用**：Feed 数据采集、账号提取、数据清洗、去重、质量评估
- **需要人工介入**：关键词搜索（需要登录 + 可能的人工验证）
- **需要进一步验证**：登录后的搜索是否能获取关键词相关内容

---

## 11. 下一步建议

### 如果条件允许（人工登录）

1. **验证搜索模式**：人工登录后运行搜索采集
2. **验证相关性**：人工评估搜索结果与关键词的相关性
3. **验证稳定性**：多次运行搜索，评估数据稳定性

### 如果不允许人工登录

1. **扩展 Feed 采集**：增加滚动次数，收集更多视频
2. **内容过滤**：基于标题/描述文本匹配关键词
3. **备选数据源**：考虑 Android 端、手动导入、其他平台

### 技术改进

1. **改进 Feed 解析**：处理更多卡片格式变体
2. **增强 URL 提取**：从更多 DOM 位置获取视频 URL
3. **Session 复用**：持久化登录状态，减少人工介入频率

---

## 12. 运行方法

```bash
# 安装依赖
cd services/agent
.venv/bin/python -m playwright install chromium

# Feed 模式（无需登录）
.venv/bin/python -m spikes.or_spike_001.run --feed-only --headed

# 搜索模式（需要登录）
.venv/bin/python -m spikes.or_spike_001.run --use-search --headed

# 单次查询测试
.venv/bin/python -m spikes.or_spike_001.run --query "短视频代运营" --feed-only --headed

# 运行测试
uv run pytest tests/unit/test_spike_001.py -v
```

---

## 13. 输出文件

```
data/spikes/or-spike-001/
└── <run_id>/
    ├── raw/
    │   ├── search_results.jsonl  (原始视频数据)
    │   └── accounts.jsonl        (原始账号数据)
    ├── normalized/
    │   ├── videos.jsonl          (标准化视频)
    │   ├── accounts.jsonl        (标准化账号)
    │   └── query_hits.jsonl      (查询命中关系)
    ├── review_sample.csv         (人工审核样本)
    ├── report.md                 (质量报告)
    └── report.json               (质量数据)
```

---

## 14. Authenticated Search Validation (OR-SPIKE-001B)

### Environment

| Item | Value |
|------|-------|
| Python | 3.12.13 |
| Playwright | 1.48+ |
| Chromium | 151.0.7922.34 |
| OS | macOS 25.4.0 arm64 |
| Mode | Headed (visible browser) |
| Profile | data/browser_profile/douyin-spike-001 |

### Login / Session Result

| Test | Result |
|------|--------|
| First login prompt | ✅ Detected (inline overlay with "登录后即可搜索更多精彩视频") |
| Captcha detection | ✅ Implemented (#captcha_container) |
| Login overlay detection | ✅ Implemented (text-based + z-index overlay) |
| Manual login wait | ✅ System correctly pauses and prompts user |
| Session reuse | ⚠️ Not fully validated (requires human login) |

### Key Finding: Search Page Login Overlay

The search page (`/search/{query}`) shows a **z-index 9999 overlay** with text "登录后即可搜索更多精彩视频" when the user is not authenticated. This overlay:

1. Blocks ALL interaction with the page
2. Contains login options: 扫码登录 / 验证码登录 / 密码登录
3. Is NOT the same as the homepage login dialog (`login-full-panel`)
4. Is NOT a captcha (`#captcha_container`)
5. Requires **new detection logic** based on text content

**Detection logic added:**
```python
# In extractors.py - check_login_required()
body_text = await self._page.evaluate("() => document.body?.innerText || ''")
if "登录后即可搜索更多精彩视频" in body_text:
    return True
```

### Search Result Evidence

During one diagnostic run (before captcha/rate-limiting), **18 real search results** rendered for query "短视频代运营":

| # | Duration | Views | Title | Author | Date |
|---|----------|-------|-------|--------|------|
| 1 | 29:41 | 6489 | 代运营怎么和老板谈单#短视频创作 #代运营 | @靳兴的运营速成指南 | 2月15日 |
| 2 | 00:59 | 1705 | 如果你做短视频是为了获客... | @i超｜商业ip | 6月27日 |
| 3 | 01:13 | 9073 | 代运营本身就是一个可以赚快钱的职业 | @薛辉小清新 | 6月3日 |
| 4 | 01:53 | 1.9万 | 做短视频最简单的方式#短视频创业 #代运营 #编导 | @薛辉小清新 | 6月17日 |
| 5 | 08:51 | 1439 | 代运营0-100全流程 | @宝藏十一（编导培训） | 6月21日 |
| ... | ... | ... | ... | ... | ... |

**Preliminary relevance assessment**: 18 diagnostic results appear strongly related to "短视频代运营" on preliminary inspection (titles contain 代运营/短视频运营 keywords). However, formal relevance confirmation remains **PENDING HUMAN REVIEW** (see `review_search_relevance.csv`).

### Search Result DOM Structure

Search results use `div.search-result-card` elements with text format:
```
[duration][view_count][title] [@author] · [date]
```

Unlike feed cards, search cards do **NOT** have:
- `href` attributes with `/video/` URLs
- Video IDs in the DOM
- Direct links to video pages

Video metadata is extracted by parsing the text content of each card.

### Per Query Statistics

| Query | Results | Status |
|-------|---------|--------|
| 短视频代运营 | 18 (in diagnostic) | ⚠️ Intermittent rendering |

### Known Limitations

1. **Login requirement**: Search requires login. The overlay is correctly detected but requires human intervention.
2. **Inconsistent rendering**: Search results sometimes render without login (first visit), sometimes require login (subsequent visits).
3. **Rate limiting**: Repeated automated access triggers captcha (`#captcha_container`).
4. **Video URL traceability**: Search cards don't contain `/video/` URLs. Video IDs are not in the DOM.
5. **Session persistence**: Not validated due to inability to complete login during autonomous execution.

### Code Changes for OR-SPIKE-001B

1. **Added `collection_mode` and `source_page_url` fields** to data models for provenance tracking
2. **Added captcha detection** (`#captcha_container`) and wait logic
3. **Added search page login overlay detection** (text-based: "登录后即可搜索更多精彩视频")
4. **Added search result card extraction** (`div.search-result-card` text parsing)
5. **Added result load verification** with retry (scroll trigger, search re-submit)
6. **Generated `review_search_relevance.csv`** with 18 samples for human review

### Stability Result

| Run | Mode | Results | Notes |
|-----|------|---------|-------|
| 1 | Search | 0 | Login overlay detected, wait timed out |
| 2 | Search (diagnostic) | 18 | Results rendered before rate limiting |
| 3 | Search | 0 | Login overlay detected |

### Final Gate Decision

**CONDITIONAL PASS** (unchanged)

**Evidence:**
1. ✅ Login overlay correctly detected and system pauses for human intervention
2. ✅ Search results CAN render with keyword-relevant data (18 results captured)
3. ✅ Data extraction format is parseable (search-result-card text)
4. ✅ Provenance tracking implemented (collection_mode, source_page_url)
5. ⚠️ Full login→search→extract flow not validated end-to-end (requires human login)
6. ⚠️ Video URL traceability for search results is limited (no /video/ links in DOM)

**Conditions for entering OR-SPIKE-0012:**
- Customer #0001 must manually login and run search to validate end-to-end flow
- Video URL traceability issue needs resolution (may need to click cards to get URLs, or accept limited traceability)
- Rate limiting / captcha frequency needs assessment over multiple runs

---

## 15. Final Conclusion

**OR-SPIKE-001: CONDITIONAL PASS**

The Douyin Web Collector can:
- ✅ Extract real, structured video data from the homepage feed (100% success, 100% URL traceable)
- ✅ Detect login/verification/captcha requirements and pause for human intervention
- ✅ Parse search result cards when they render
- ⚠️ Search requires login (correctly detected but not autonomously completable)
- ⚠️ Search result rendering is inconsistent (sometimes works, sometimes requires login)

**Next step**: OR-SPIKE-001B validation with human login, then OR-SPIKE-002 if successful.
