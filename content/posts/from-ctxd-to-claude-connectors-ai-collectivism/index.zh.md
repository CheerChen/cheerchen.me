+++
date = '2026-05-24T20:00:00+09:00'
draft = false
title = '从 ctxd 到 Claude Code Connectors：AI 时代没有个人英雄'
seo_description = "我把 slack-thread-dump、pr-dump、confluence-dump 三个自用 CLI 合并成了 ctxd，配合 Claude Code 的 skill 自己用得很顺手。但今年 4 月底 Claude Code 上线 Connectors 后，同样的能力被官方端到端地解决了——这篇是一个独立开发者面对 AI 时代「集体主义」的复盘。"
tags = ["AI", "开发工具", "Claude Code", "复盘"]
categories = ["AI 协作"]
nolastmod = true
cover = 'Gemini_Generated_Image_n5paesn5paesn5pa.jpg'
images = ['Gemini_Generated_Image_n5paesn5paesn5pa.jpg']
+++

ctxd 是我为了让 Claude Code 自动读取 Slack / GitHub PR / Confluence / Jira 上下文写的小工具。它很好用，也真实省了我很多时间。但几个月后，Claude Code Connectors 把它 80% 的核心价值官方化了。

这件事让我重新思考：AI 时代个人工具项目的价值到底在哪里。

### ctxd 是怎么长出来的

去年底到今年初，我陆陆续续写过三个 CLI：

- `slack-thread-dump`：把一条 Slack thread 导成 markdown / text；
- `pr-dump`：把一个 GitHub PR 的元数据、评论、diff 打包成单文件，喂给 AI 做 code review（[之前那篇文章](../introducing-pr-dump-for-ai-code-review/) 介绍过）；
- `confluence-dump`：把 Confluence 页面（含子页面 / 图片）导成 markdown，同源再加一个 Jira ticket 的导出。

写到第三个的时候我意识到——这其实是同一类需求：**把分散在 SaaS 里的上下文，拍平成一份 LLM 能直接读的文本**。于是我把三个仓库合并、改名 `ctxd`，把授权信息放到配置文件、统一了输出（`-O` 自动命名，stderr 自动静音），上了 Homebrew tap。

然后我在自己的 `~/.claude/CLAUDE.md` 里加了一条规则：

> 当用户粘贴 Slack / GitHub PR / Confluence / Jira 的链接并要求阅读、总结、翻译、引用时，**立刻通过 Bash 执行 `ctxd <url>`**——不要让用户手动复制内容。

配合这条 skill，整套工作流就闭环了：我把 Slack 链接丢进 Claude Code，它自动 `ctxd` 一下，拿到完整 thread 直接进入对话上下文。日常用得相当顺手。

但我没推广，也没系统地分享给同事用。

### 然后 Claude Code 出了 Connectors

到今年 4 月底 5 月初，Claude Code 端到端上了 Connectors —— Slack / Atlassian (Confluence + Jira) / Microsoft 365 / Asana / Box 等等，全部内置。授权方式从「去 Slack 后台申请 user token 填进 `~/.config/ctxd/config`」变成了「点一下同意」。

我第一次接 Atlassian connector 的时候有点恍惚：

- `mcp__claude_ai_Atlassian__getConfluencePage` 替代了我的 confluence 导出；
- `mcp__claude_ai_Atlassian__getJiraIssue` 替代了我的 Jira 导出；
- `mcp__claude_ai_Slack__slack_read_thread` 替代了 slack-thread-dump；
- GitHub 这块本来就有 `gh` 和官方 MCP，我的 pr-dump 也只是一层胶水。

也就是说，`ctxd` 大约 80% 的价值，被 Connectors 一次性吃掉了。

剩下那 20%——离线导出成本地 markdown 文件、批量递归导 Confluence 子树、自定义 diff 模式——依然有意义，但已经是「**长尾价值**」，而不是当初那种「**没有这个东西我用不了 AI**」的核心价值。

### 但 ctxd 没白做

但回头看，在 5 月初 Connectors 出来之前的那段窗口期，ctxd 给我的回报非常具体：

- **PR 评审**：粘 PR URL，AI 直接给我「这次变更的动机、风险点、应该反问什么」。比一行一行翻 diff 快至少 5 倍。
- **Slack 起草回复**：日企那种「先确认 → 补一句背景 → 一点保留意见 → 但又留一手 → 最后求确认」的多层转折 thread，肉眼读完一遍人就累了。Slack Thread Url 一贴，AI 先帮我理解对话内容，再用日语起草回复一下就完事了。
- **Jira ticket**：直接按照团队内部的 Jira ticket Clone 格式并填一份新的。
- **读同事的 Confluence**：我同事写文档可以写 30 页且引经据典，先让 AI 总结要点 + 解释关键术语，确实轻松不少。

这些都是**真实发生过、真实省下来的时间**，并不因为 Vibe 的东西官方有了就亏了。

而且——这点其实更重要——**我自己独立收敛到的最终形态（「把 URL 直接贴给 LLM」），和 Anthropic 半年后官方提供 Connectors 所达到的对话形态一样**。这不是巧合。它说明我对「什么叫效率」的判断，跟做 Claude Code 的那拨人对齐。在 AI 这种变化速率下，能跟上游产品直觉对齐，本身比「我做了 X」更值钱。

严格地说：ctxd 不是被取代了，是**被验证了**。

### AI 时代是集体主义的，不是个人主义的

前段时间听了姚顺宇那个四小时访谈（[YouTube](https://www.youtube.com/watch?v=ttkd0t5qTD4) / [Apple Podcast](https://podcasts.apple.com/cn/podcast/140-%E5%AF%B9%E5%A7%9A%E9%A1%BA%E5%AE%87%E7%9A%844%E5%B0%8F%E6%97%B6%E8%AE%BF%E8%B0%88-%E8%AF%B7%E5%85%81%E8%AE%B8%E6%88%91%E5%B0%8F%E7%96%AF%E4%B8%80%E4%B8%8B-%E5%9C%A8anthropic%E5%92%8Cgemini%E8%AE%AD%E6%A8%A1%E5%9E%8B-%E6%8A%80%E6%9C%AF%E9%A2%84%E6%B5%8B-%E8%8B%B1%E9%9B%84%E4%B8%BB%E4%B9%89%E5%B7%B2%E8%BF%87%E5%8E%BB/id1634356920?i=1000767107736)），里面有一句话我反复想：

> "AI 的个人英雄主义时代已经结束了，现在都是集体主义，只有英雄集体，但是没有个人英雄，所以要对神话个体的一切叙事保持警惕。"

{{< figure src="2026-05-25 0.18.34.jpg" >}}

ctxd 这件事就是个微缩样本。我一个人写、一个人维护、一个人用，自我感觉良好。但只要这是一个**真实的需求**，就一定有别人也在解决——Anthropic 内部某个产品团队、Slack 官方、Cursor、Cline、若干开源项目……他们的速度、资源、分发能力，是个人项目永远追不上的。

所以在 AI 时代，是真正意义上的“即便你不做，也大把有的是人在做”。

### 做慢了不如不做

任何试图解决 AI 模型原生不足的工具，当你的工具被 Vibe 出来，官方可能已经在内部实现了，未来三到五周就会发布。等到发布完，你的版本反而成了一种「认知负担」（用户反而要学一个即将被淘汰的工具）。

这种时候，**不做反而是个 net positive 的选择**。把那段时间花在非效率工具，或是内容产出可能更持久一些。

当然，这不是说不要造轮子。**为了学习而造、为了自用而造、为了把问题想清楚而造，永远都值**。但要分清楚自己造的目的——是「学习/自用」还是「想推广出去成为某种事实标准」。后者在 AI 时代的成功率，比想象中低很多。

### 附：如果你还是想试 ctxd

如果你看完这篇还是想试 `ctxd`——比如你就是想要项目上下文完全自己控制，只落到本地 markdown 文件，最后可以整理到 Obsidian 之类的——repo 在这里：

[github.com/cheerchen/ctxd](https://github.com/cheerchen/ctxd)

但有一点比工具本身更重要：**先把 skill 放进你的 `~/.claude/CLAUDE.md`**（或者做成一个独立的 Claude Code Skill）。没有这条规则，ctxd 只是一个普通 CLI；有了这条规则，Claude Code 才会在你粘贴链接的瞬间自动调用它。

````markdown
## Tool: ctxd — auto-fetch context from URLs
`ctxd` is installed at `/opt/homebrew/bin/ctxd` (v0.3.0+). It's a unified context dumper for Slack / GitHub PR / Confluence / Jira URLs.

**Rule:** When the user pastes a URL from any of these sources and asks you to read / summarize / translate / reference it, **run `ctxd <url>` via Bash immediately** — do not ask the user to paste content manually.

Supported URL patterns:
- `https://*.slack.com/archives/...` — Slack threads
- `https://github.com/*/pull/*` — GitHub PRs
- `https://*.atlassian.net/wiki/...` — Confluence pages
- `https://*.atlassian.net/browse/...` — Jira issues

Common usage:
```
ctxd <url>              # markdown to stdout (default — works for all 4 sources)
ctxd <url> -f text      # plain text
ctxd --help             # full options
```

Note: `ctxd` auto-silences stderr progress when stderr isn't a TTY (i.e. when invoked by Claude Code / captured by a wrapper). No need to pass `-q`. In an interactive terminal, progress still shows — pass `-q` manually to silence there.

Confluence — expansion flags (opt-in, require `-o <dir>`):
- `-r` recursive export of child pages
- `-i` download referenced images
- `--all-attachments` download every attachment
Default Confluence behavior is single-page to stdout; only reach for these when the user explicitly wants a tree or image export.

Fallback: if ctxd fails or URL isn't a supported source, use WebFetch.
````

工具是给 Agent 用的，不是给人用的。**让 Agent 知道这个工具存在**，比工具本身更重要。

### 结语

总之，ctxd 这个项目本身我完全不后悔做——窗口期里它替我赚回了大量时间，最终又被官方验证了方向。技术副产品（统一抽象的练习、PR / Slack / Confluence API 的踩坑）是顺手的。

这件事最后给我的提醒不是「个人项目没意义」，而是「个人项目要清楚自己在和谁赛跑」。为学习、自用、验证判断而做，永远有价值；但如果目标是占住一个 AI 工作流入口，那速度和分发本身就是产品的一部分。
