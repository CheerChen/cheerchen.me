+++
date = '2026-09-15T12:00:00+09:00'
draft = true
title = '从“斩杀线”到 251 会话：推理模型 Overthinking 的数据差距与自救'
seo_description = "满怀期待地用上号称极速试错、自带读图、性价比斩杀线的新一代推理模型，却在 Coding Agent 里频繁遭遇读图超限与几万字符的过度思考发呆。通过反向解析 251 个有效会话与 1.2 万个思考块，用数据揭露 reasoning_effort 的断层差距，并落地开源检测插件 pi-overthink-warning。"
tags = ["generative-ai", "dev-tools", "best-practices"]
categories = ["ai-collab"]
nolastmod = true
+++

## 一、 起因：被推文“神话”吸引后的巨大落差

前段时间，社交平台上几乎被新一代国产大模型刷屏。不管是 DeepSeek V4 Flash / V4.1 Flash 还是 GLM-5.3 Flash，社区推文与评测里到处充斥着令人兴奋的关键词：

- **极速试错神话**：“Opus 刚慢吞吞跑完一轮尝试，DS 4.1 已经极速试错了三四轮。”
- **白菜价与“性价比斩杀线”**：基准评测全面跻身第一梯队，但 Token 单价只有顶级商业模型的零头，被盛赞为彻底击穿大模型行业定价的“斩杀线”。
- **原生多模态读图**：界面排查、前端样式对齐和报错截图可以直接喂给 Agent，不再需要切换昂贵的专有模型。

作为一名 Coding Agent（日常高频使用 pi、Devin、Copilot）的重度用户，看到这样的宣传自然毫不犹豫地全面切换过去，期待享受“又快、又便宜、还能看图”的效率红利。

然而，当满怀期待地把它们丢进真实、高强度的日常工程工作流后，等待我的并不是生产力飞跃，而是接二连三让人怀疑人生的暗坑。

### 暗坑 1：读图能力的“鸡肋”陷阱

宣传里白纸黑字写着多模态读图支持，但在真实的 Coding Agent 环境中，Agent 每次交互都会把历史消息作为上下文完整发送给 API。

在 DeepSeek V4 Flash 的 vision 变体（`deepseek-v4-flash-vision-exp`）下，一旦 Session 上下文累积超过 4 张截图，API 就会返回 400 错误：`"At most 4 image(s) may be provided in one prompt"`。从实测 Session 日志可以看到，第 5 张图触发错误后，用户尝试让其继续，但后续请求全部返回 `stopReason=error`，整个会话在此被迫终止。

更隐蔽的是非 vision 模型的情况：`deepseek-v4-flash` 和 `deepseek-v4.1-flash` 在遇到图片时，pi 会返回 `"Current model does not support images. The image will be omitted"` —— 图片被静默丢弃，模型看不到图但不会报错。这意味着你以为模型在对照截图排查，实际上它完全在盲猜。

*注：本节是 overthinking 分析之外的额外观察，不纳入下文的 251 Session 数据统计。读图限制与 overthinking 是两个独立问题，但都指向同一结论：新模型在 Coding Agent 工程落地场景中的成熟度仍有不足。*

### 暗坑 2：让人抓狂的“卡顿与发呆”

更折磨人的是编码时的体感。

以前使用 GLM-5.2 时，Agent 思考和执行都干脆利落；但换上宣称“速度极快”的几款新模型后，终端光标却开始频繁陷入长时间的“发呆”。等它终于吐出结果，往往伴随着几万字的推演过程，最后落实到代码上却只是改了一个无足轻重的变量名，甚至原地绕了一圈告诉你“无需修改”。

### 最初的自我怀疑

面对这种剧烈的心理反差，我最开始是在反思自己：
- 是不是我的 Prompt 没写好？没有加上“请简洁回答，不要废话”？
- 是不是任务拆解得不够细，导致模型在复杂逻辑里打转？

但随着调教 Prompt 屡屡受挫，我意识到不能停留在玄学和体感上。既然本地存放着所有 Agent 的运行日志，不如直接掀开底牌，用真实数据看看这几款模型到底在背后干了什么。

---

## 二、 取证与清洗：跨 3 款 Agent、251 个有效 Session 的逆向分析

为了搞清楚模型到底在背后写了多少思考内容，我把本地积累的所有 Coding Agent 历史会话日志全部翻了出来。

### 1. 数据来源与逆向解析

不同工具对推理内容（Reasoning Content）的存储方式各有不同：

| 来源 | 日志路径 | 格式与字段 | 是否可实时/离线读取 |
|---|---|---|---|
| **pi** | `~/.pi/agent/sessions/**/*.jsonl` | JSONL，`content[].type === "thinking"` | 是（实时结构化保存） |
| **Devin** | `~/.local/share/devin/cli/transcripts/*.json` | JSON，`steps[].reasoning_content` | 是（Session 结束后归档写入） |
| **Copilot** | `~/.copilot/session-state/*/events.jsonl` | JSONL，`data.reasoningText` | 是（事件流格式） |
| **Codex** | `~/.codex/sessions/**/*.jsonl` | JSONL | 否（思考内容加密存储） |
| **Grok** | `~/.grok/sessions/**/chat_history.jsonl` | JSONL | 否（Reasoning 字段为空） |

*注：Codex 因思考内容加密、Grok 因字段为空，均予以排除。*

### 2. 数据集画像

总扫描会话为 274 个（pi=174，Devin=100），最终提取出 **251 个包含 Thinking Block 的有效 Session**，共提取出 **12,324 个独立 Thinking Block（思考块）**：

- **正常组（156 Sessions）**：GPT-5.6 Sol (56)、GPT-5.6 Luna (29)、GLM-5.2 High (68)、Gemini 3.8 Flash (3)。
- **问题组（85 Sessions）**：GLM-5.3 Flash (33)、DeepSeek V4 Flash (40)、DeepSeek V4.1 Flash (12)。
- **排除样本**：GPT-5.6 Terra (2)、Claude Opus 5 (1)、Qwen 3.7 Max (1)、ox-alpha-free (1)、GPT-5.4 (1) 共 6 个 Session 因样本量不足 3，不纳入后续模型间横向对比。

---

## 三、 数据大起底：关于推理模型的四个残酷真相

当把清洗后的数据汇总成表格后，真相浮出水面。

### 真相一：同样是 `high`，思考量相差 10~84 倍

在 Agent 界面中，我们经常把 `reasoning_effort` 设为 `high`。直觉上，各家的 `high` 应该代表相似的深度推理预算。

但实测数据展现了一副荒诞的景象：

| 模型 | 默认/常用 effort | Session 数 | 平均最大思考块 (字符) | 平均总思考字符 | 平均块数 |
|---|---|---|---|---|---|
| **GPT-5.6 Sol** | high | 56 | 513 | 4,418 | 25.0 |
| **GPT-5.6 Luna** | high | 29 | 1,362 | 11,440 | 79.6 |
| **GLM-5.2 High** | high | 68 | 7,117 | 35,210 | 26.4 |
| **DS V4 Flash** | high | 40 | 14,844 | 167,479 | 70.0 |
| **GLM-5.3 Flash** | high | 33 | 18,927 | 123,280 | 56.6 |
| **DS V4.1 Flash** | high | 12 | **29,795** | **221,134** | 67.1 |

以上数据按模型整体统计（含该模型所有 effort 档位），因为各模型的默认档位本身就是 high，且部分模型在 Devin 中只有 high 可选。在同样处于 high 档位的前提下：
- GPT-5.6 Luna 的平均最大块为 **1,362 字符**，而 DS V4.1 Flash 高达 **29,795 字符** —— **相差 22 倍**。
- 如果看单块分布的 p95：GPT-5.6 Luna 的 p95 仅为 **164 字符**，DS V4.1 Flash 的 p95 却高达 **13,754 字符** —— **相差 84 倍**。
- 看平均总思考字符：GPT-5.6 Sol 仅 4,418 字符，而 DS V4.1 Flash 达到 221,134 字符 —— **相差 50 倍**。

所谓“极速输出”的优势，在膨胀了几十倍的无意义思考内容面前被彻底吞噬。模型不是跑得快，而是把所有的算力和时间都消耗在了内耗上。

### 真相二：档位语义混乱 —— `low` 不一定低

很多厂商声称如果觉得慢，可以把推理档位调低。但实测中，档位语义已经完全混乱：

| 模型 | 档位 | Session 数 | 平均最大块 (字符) |
|---|---|---|---|
| **GLM-5.2** | high（全 Session 平均） | 68 | 7,117 |
| **GLM-5.3 Flash** | high | 18 | 16,263 |
| **GLM-5.3 Flash** | low | 2 | 44,118（含 1 个 77k 异常值） |

GLM-5.3 Flash 的 `low` 档仅有 2 个 Session，其中 1 个最大块高达 77,672 字符（`chivalrous-catboat`），另 1 个仅 3,389 字符（完全正常）。虽然样本量较小，无法确认 `low` 档是否普遍失控，但至少说明 `low` 档并不能保证“低思考量” —— API 层面的 `reasoning_effort` 标签与实际推理预算的关系，远比想象中复杂。

### 真相三：平台硬性锁死，用户毫无降级空间

为什么大家不手动把档位调低呢？深入调研后才发现：**很多时候不是用户不想调，是平台根本没给调的选项**。

| 模型 | low 可用 | medium 可用 | high 可用 | xhigh 可用 | max 可用 |
|---|---|---|---|---|---|
| **DS V4 Flash** | ❌ | ❌ | ✅ | — | ✅ |
| **DS V4.1 Flash** | ❌ | ❌ | ✅ | — | ✅ |
| **GLM-5.2** | ❌ | ❌ | ✅ | — | ✅ |
| **GLM-5.3 Flash** | ✅ | ❌ | ✅ | — | ✅ |
| **Claude Opus 5** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **GPT-5.6 Sol** | ✅ | ✅ | ✅ | ✅ | ✅ |

在 Devin 的预设集成中，DeepSeek V4/V4.1 Flash **最低只能选择 high**。而在 GLM-5.3 官方文档中，明确记录了移除了 `thinking.type: "disabled"` 选项，Thinking 模式被强制全局开启，默认 `reasoning_effort: "max"` 每次任务据官方文档动辄产生约 75,000 output tokens。用户被死死绑在超重推理档位上动弹不得。

### 真相四：Prompt 压制推理预算完全是徒劳的

很多开发者在发现模型啰嗦时，第一反应是在 System Prompt 里写上：“简洁回答”、“不要过度思考”、“直接输出代码”。

但翻阅官方技术文档后会发现，这纯粹是心理安慰：

1. **超参全面失效**：根据 DeepSeek 官方 API 文档，在开启 Thinking 模式后，`temperature`、`top_p`、`presence_penalty`、`frequency_penalty` 等所有传统采样参数均被后端强制忽略。
2. **反思诅咒（Over-verification）**：Anthropic 官方文档（Extended thinking tips）指出，对新一代推理模型施加明确的自我验证指令（Explicit Verification Instructions），不仅压不住思考量，反而会诱发模型陷入更严重的反复自我辩论与过量验证。

---

## 四、 两种典型的 Overthinking 形态与案例复盘

从 251 个会话的统计中，我们可以清晰地将 Overthinking 归纳为两种形态：

```
                       ┌─ 形态 1: 纵向深挖（单块 10k~80k 字符，反复推演否定）
Overthinking 两种形态 ─┤
                       └─ 形态 2: 横向铺开（单块看似正常，但极其琐碎，84 次搜索换 3 次写入）
```

### 1. 纵向深挖（单块极端膨胀）

模型在一个思考块里陷入长达几万字符的自言自语，反复提出假设、推翻假设、重新论证边界条件。

**典型表现**：
- 正常模型的单块思考通常集中在几百字符，用来梳理调用工具的前置条件。
- 问题模型在单个块里动辄输出 20,000 ~ 70,000 字符，把一个简单的函数重命名当成登月工程来推导。

### 2. 横向铺开（步步都在想，总量大爆炸）

这种形态更为隐蔽。单看每一个思考块，字符数都在 1,000 ~ 3,000 之间，看似很“克制”，但整个任务被拆得极碎，累积思考量惊人。

**真实案例（Session `01a09ef1`，DS V4.1 Flash）**：
- 用户仅输入了 **2 条简单的 UI 调整需求**；
- 产生了 **83 个思考块**，平均每块 1,381 字符，累计思考字符 **114,650**；
- 伴随产生 **148 次工具调用**，其中 **84 次是文件读取与 grep 搜索（探索）**，真正落实到文件写入的只有 **3 次（行动）**。

*注：横向铺开是启发式提醒，不是精确判定。一个跑了一下午的正常 Session 可能自然累积到 80 块、100k 字符。我们的数据显示，较低规则（50 块或 50k 字符）在正常 Session 上的误报率约 25.7%，较高规则（80 块或 100k 字符）约 17.5%。因此监控插件对横向铺开只设 warn/alert 两级，不设 critical。*

### 3. 超标率的分层

先定义"标"。一个 Session 满足以下任意一条即判定为**过度思考超标**：

- **纵向深挖**：单个思考块超过 **12,000 字符**（正常模型 p99 仅 6,891 字符）
- **横向铺开**：累计思考块 ≥ **80 个**，或累计思考字符 ≥ **100,000**（正常模型平均仅 25,197 字符 / 40.8 块）

阈值的具体推导见第六章。基于此标准，各有效模型（样本量 ≥ 3）的超标率如下：

| 模型 | 总 Session 数 | 超标数 | 超标率 | 平均最大块 (字符) | 平均块数 | 平均总字符 |
|---|---|---|---|---|---|---|
| **GPT-5.6 Sol** | 56 | 2 | **4%** | 379 | 24.0 | 2,403 |
| **GPT-5.6 Luna** | 29 | 3 | **10%** | 1,362 | 79.6 | 11,440 |
| **GLM-5.2 High** | 68 | 11 | **16%** | 7,117 | 26.4 | 35,510 |
| **GLM-5.3 Flash** | 33 | 20 | **61%** | 18,927 | 56.6 | 123,280 |
| **DS v4 Flash** | 40 | 25 | **62%** | 14,844 | 70.0 | 167,479 |
| **DS v4.1 Flash** | 12 | 10 | **83%** | 29,795 | 67.1 | 221,134 |

分层梯队极为清晰：

```text
GPT-5.6 Sol     4%   ─┐
GPT-5.6 Luna   10%   │  正常可用区间 (4% - 16%)
GLM-5.2 High   16%   ─┘
                     ← 近 4 倍跳跃
GLM-5.3 Flash  61%   ─┐
DS v4 Flash    62%   │  重度 Overthinking 区间 (61% - 83%)
DS v4.1 Flash  83%   ─┘
```

从 GLM-5.2 的 16% 到 GLM-5.3 Flash 的 61%，超标率出现了近 4 倍的跳跃。

---

## 五、 现有生态盲区：为什么开源检测插件全军覆没？

既然 Overthinking 如此普遍，为什么社区现有的 Agent 插件没能发现它？

我调研了 pi 社区中最主流的几款循环与状态检测插件：

| 插件 | 检测原理 | 为什么对 Overthinking 失效 |
|---|---|---|
| `pi-loop-police` | 检测 thinking 块内连续重复（≥80 字符重复） | 检测的是死循环卡死；Overthinking 每次都是全新词句；且其滑动窗口仅 4,000 字符，对万字长块直接失效 |
| `pi-deadloop` | 检测会话级 Jaccard 相似度（4 轮 ≥85%） | 同上，侧重于重复回复判断 |
| `pi-behavior-monitors` | 引入 Side-channel LLM 进行行为分类 | 判定成本高，带来额外的 API 延迟与开销 |
| `pi-thinking-tail` | 仅在 UI 层折叠长思考块 | 纯视觉美化，不做任何逻辑检测与告警 |

**核心痛点**：现有生态插件默认假设“异常 = 循环重复”。但推理模型的 Overthinking 恰恰是“逻辑连贯的高密度废话”，且现有插件的滑动检测窗口在动辄几万字符的单块面前根本无法覆盖。

---

## 六、 自制破局工具：`pi-overthink-warning` 插件

既然市面上没有能打的工具，那就基于 1.2 万个思考块的真实数据分布，自己写一个。

### 1. 科学阈值的推导

通过对正常 Session 与问题 Session 的字符分布进行经验百分位统计，我们确定了高区分度的阶梯阈值：

| 阈值 | 正常块触发率 | 问题块触发率 | 区分倍率 | 告警级别 |
|---|---|---|---|---|
| **5,000 字符** | 1.63% | 12.27% | 7.5x | **warn**（黄色通知） |
| **8,000 字符** | 0.75% | 6.77% | 9.1x | **alert**（黄色通知 + 状态栏） |
| **12,000 字符** | 0.39% | 3.63% | 9.4x | **critical**（红色通知 + 状态栏） |

横向铺开阈值（启发式判定）：

| 规则 | 正常 Session 触发率 | 问题 Session 触发率 | 告警级别 |
|---|---|---|---|
| 块数 ≥ 50 或 累计字符 ≥ 50,000 | 25.7% | 60.2% | **warn** |
| 块数 ≥ 80 或 累计字符 ≥ 100,000 | 17.5% | 44.6% | **alert** |

### 2. 插件设计哲学：克制与务实

在开发 `pi-overthink-warning` 时，我确立了四条极客原则：

1. **只提醒，不干预**：绝不在思考中途强行注入 System Prompt，也不粗暴中断模型执行，避免破坏上下文。
2. **非阻塞交互**：放弃模态弹窗。warn 使用黄色通知，alert 使用黄色通知 + 持续状态栏，critical 使用红色通知 + 持续状态栏。三级颜色递进，但都不阻塞用户操作。
3. **单调升级机制**：在同一个 Session 内，告警级别只升不降，避免每一次工具调用都反复弹出提示打扰思路。
4. **务实的解决建议**：告警文案以 "Switch model" 为主建议，"lower reasoning effort if available" 为辅 —— 因为在实际环境中，大部分 Overthinking 模型根本没有降级选项。

### 3. 安装与使用

该插件已在 GitHub 开源：[https://github.com/cheerchen/pi-overthink-warning](https://github.com/cheerchen/pi-overthink-warning)

在 pi 环境中可一键安装：

```bash
pi install git:github.com/cheerchen/pi-overthink-warning
```

### 4. Devin 监控的限制

在调查 Devin 的 hook 系统后发现，Devin 目前没有 reasoning 实时事件（仅有 PreToolUse/PostToolUse/UserPromptSubmit/Stop/SessionStart/SessionEnd/PostCompaction）。reasoning content 只在 session 结束后写入 transcript 文件，session 进行中不在任何实时可读的位置。因此 `pi-overthink-warning` 目前仅支持 pi，Devin 的实时监控暂不可行。

---

## 七、 复现方法

分析与扫描脚本已随插件仓库开源：[https://github.com/cheerchen/pi-overthink-warning](https://github.com/cheerchen/pi-overthink-warning)

```bash
# 克隆分析仓库
git clone https://github.com/cheerchen/pi-overthink-warning
cd pi-overthink-warning

# 批量扫描所有 session，按模型分组
uv run scripts/batch_scan.py

# 合并模型，计算问题率
uv run scripts/incident_rate.py

# 单 session 特征提取
uv run scripts/analyze_overthinking.py "label" /path/to/session.jsonl
```

本地数据源路径参考：
- pi: `~/.pi/agent/sessions/**/*.jsonl`
- Devin: `~/.local/share/devin/cli/transcripts/*.json`

---

## 八、 数据局限

为保证技术严谨性，在此列出本研究的数据边界与局限：

1. **样本量**：部分模型仅有 1~2 个 session（GPT-5.6 Terra、Claude Opus 5、Qwen 3.7 Max、ox-alpha-free、GPT-5.4），样本不足未纳入模型间对比结论。
2. **GLM-5.3 Flash low**：仅 2 个 session，无法确认 low 档是否长期稳定可控。
3. **Devin effort 限制**：DS V4/V4.1 Flash 在 Devin 中最低只能选 high，无法实测其 low/medium 档位表现。
4. **任务类型偏差**：Session 数据来源于真实日常开发，各模型处理的任务复杂度分布不完全均匀；横向铺开阈值存在一定的长任务误报。
5. **Copilot 数据量**：仅有少量 session（全部为 Claude Opus），代表性有限。
6. **加密与空字段排除**：Codex 思考加密、Grok 思考为空，无法纳入统计。

---

## 九、 总结与反思：走出技术社区宣发的“滤镜”

这次针对 251 个 Session 的数据逆向与分析，让我深刻意识到技术宣发与真实工业落地之间的鸿沟。

不可否认，新一代国产推理模型在基准跑分、单 Token 价格以及极限生成速度上都取得了令人瞩目的进步。但在真正的 Coding Agent 工业化落地场景中，它们依然面临着非常实际的工程短板。

给模型厂商的真诚建议：
1. **统一 effort 语义**：同样是 high，不同模型的推理预算相差 10~84 倍，这对平台集成和开发者认知是巨大负担。
2. **开放降级与关闭选项**：开放真正的 token 预算上限控制与 disabled 开关，不要让平台集成和用户失去调控余地。
3. **完善多模态上下文管理**：4 张图硬上限与非 vision 模型的静默丢弃都不是合理的设计，应提供更友好的图片生命周期管理。

而对于身处一线的开发者，在面对“降维打击”、“性价比斩杀线”等社区狂欢词汇时，不妨多保留一份清醒。给自己的 Agent 配好可观测性工具，当遇到光标长时间发呆时，别再对着 Prompt 盲目死磕 —— 果断切换到一个成熟稳定的模型，往往才是最高效的自救方式。
