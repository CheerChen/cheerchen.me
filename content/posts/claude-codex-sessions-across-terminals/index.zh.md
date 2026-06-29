+++
date = '2026-06-19T10:00:00+09:00'
draft = false
title = '在两台 Mac 之间让 Claude Code / Codex session 接力：Syncthing + session-index-viewer'
seo_description = "利用树莓派在两台 Mac 之间用 Syncthing 同步 ~/.claude/projects 和 ~/.codex/sessions，再用自制的 session-index-viewer 按首条 prompt + 最后一条回复来检索和一键 resume。讲清楚星型拓扑的选型理由、路径编码陷阱、append-write 撞车风险，以及 viewer 在做什么。"
tags = ["Syncthing", "Claude Code", "Codex", "Homelab", "树莓派"]
categories = ["技术"]
nolastmod = true
cover = 'cover.jpg'
images = ['cover.jpg']
+++

<!-- TODO: 封面图，待补 -->

## 背景

痛点很简单，我有两台 MacBook（A 和 B），两边都在高强度使用 Claude Code 和 Codex 进行工作或者 Side Project，我希望在两台机器之间无缝切换，随时 resume 之前的会话。

既然他们的真实会话都在远端存着，索引的会话文件在本地保存。那么只要两边的 session 文件能互相同步，从任意一台电脑直接 resume 就可以随时从中断的地方继续。首先解决同步的问题，这是第一层想法。

第二个麻烦的地方是：`claude --resume` 和 `codex --resume` 的列表，都只有一行左右的文本，根本猜不出来哪条是哪条，哪条才是我想要找的会话？这是检索层的问题。

## 为什么不直接用云端

这里要先承认一个事实：这件事其实有完全云端的解法。Claude.ai/code、Cursor 的云端 chat 同步、GitHub Codespaces 里跑 Claude Code，或者 Devin / Replit Agent / Lovable / v0 这些全云端 sandbox——已经是更好的路径。

我的个人偏好是：

- 喜欢同时挂 Claude Code 和 Codex 两套工具来回切，云端方案基本会锁死一家
- 个人项目跑在 pi 的 docker daemon、ssh key、`.envrc` 这些环境里，云沙箱里要重新拉一遍
- 喜欢 homelab，喜欢自己动手解决问题

所以整个文章预设是给"偏好本地 CLI"的人看的。

## 先看看各自的配置文件结构

`~/.claude/projects/` 下是按 cwd 编码的目录，每个目录里是这个 cwd 下的 session jsonl 文件：

```~/.claude/projects/
  -Users-cheerchen-Documents-CheerChen-session-sync/
    5a3f8b2c-...jsonl
    8d1e4f7a-...jsonl
  -Users-cheerchen-Documents-CheerChen-other-project/
    1c2d3e4f-...jsonl
```
`~/.codex/sessions/` 下是按日期分桶的目录，每个目录里是这个日期下的 session jsonl 文件：

```~/.codex/sessions/
  2026/
    06/
      19/
        5a3f8b2c-...jsonl
        8d1e4f7a-...jsonl
  2026/
    06/
      18/
        1c2d3e4f-...jsonl
```

其中 claude 的 session 跟路径绑定，codex 的 session 跟路径无关。claude 的 session 是追加写的，codex 的 session 是一次性写入的。理解了结构之后，我开始寻找一个有效的同步思路和定位 Session 的方法。

下面分开介绍：同步层用 Syncthing，检索层用一个自己写的小工具，叫 session-index-viewer。

## 同步层方案

Syncthing 把两台 Mac 的 `~/.claude/projects/` 和 `~/.codex/sessions/` 通过家里一台树莓派（Pi）互相同步。

拓扑是星型：A ↔ Pi ↔ B，A 和 B 不直接配对。

<!-- TODO: 图 1 — 拓扑图。A ↔ Pi ↔ B 三个节点，Pi 节点标注 "Receive Only + Staggered Versioning"，每台 Mac 上画一个 viewer 小图标。横向布局。 -->

为什么不直接 A↔B？

考虑到 MacBook 都要合盖或休眠，两边同时在线的窗口很短。而 Pi 永远开机，当一个总是醒着的中转节点，A/B 哪一端醒着就跟 Pi 同步，离线那端的状态由 Pi 暂存。这样不会出现 A 和 B 互等。

### Pi 在拓扑里的角色：只读中继

Pi 上 Syncthing 设成 **Receive Only**——只接收来自 A 和 B 的更新，不主动把"本地修改"推回去。

再加上 **Staggered File Versioning**（默认保留 30 天），任何来自 A 或 B 的删除和覆盖在 Pi 上都进 `.stversions/` 留底。

### Pi 上的 compose

Pi 上所有服务统一在 `/opt/stacks/<name>/` 下，由 dockge 管理。Syncthing 也走这套路径：

```yaml
# /opt/stacks/syncthing/compose.yaml
services:
  syncthing:
    image: syncthing/syncthing:latest
    container_name: syncthing
    hostname: pi-relay
    restart: unless-stopped
    # host mode is required: LAN discovery (21027/udp multicast) and
    # direct LAN sync (22000) don't work cleanly through bridge NAT.
    network_mode: host
    environment:
      - PUID=1000
      - PGID=1000
      # Pin version via image tag; prevent self-upgrade inside container.
      - STNOUPGRADE=1
    volumes:
      - ./config:/var/syncthing/config
      - ./data/claude-projects:/var/syncthing/claude-projects
      - ./data/codex-sessions:/var/syncthing/codex-sessions
```

`network_mode: host` 是必须的：Syncthing 的局域网发现走 21027/udp 多播，直连同步走 22000。

Pi 启动后 GUI 在 `http://<pi-ip>:8384`，建两个 folder：`claude-projects` 和 `codex-sessions`，都设成 **Receive Only + Staggered Versioning（30 天）**。

### A 侧（B 同理）

```bash
brew install syncthing
brew services start syncthing
```

打开 `http://127.0.0.1:8384`，把 Pi 的 device ID 加进 Remote Devices，两个 folder 都设成 **Send & Receive**，路径分别指向 `~/.claude/projects` 和 `~/.codex/sessions`。

<!-- TODO: 图 2 — Pi Syncthing GUI 主界面截图。访问 https://syncthing.cheerchen.me 或局域网 http://192.168.0.110:8384，截一张显示两个 folder 都 Up to Date、三台 device（pi-relay + 两台 mba）都在线的总览图。 -->

### 几个要点

1. `~/.claude/` 整个目录不能塞进 Syncthing。** 只挑下面的 `projects/`。

`~/.claude/` 下还有这些目录：

- `statsig/` —— SDK 用的状态缓存，每次打开 Claude Code 都在改
- `shell-snapshots/` —— 每次会话都在生成
- `todos/` —— 内部 task 状态文件
- `cache/` —— 顾名思义

这些目录的共性都一样：高频小文件、本机运行时状态、跨机器不需要共享。如果整个 `~/.claude/` 一起同步，Syncthing 会被这些目录刷屏。

2. Claude Code / Codex 的路径编码

`~/.claude/projects/` 下的子目录名是把当前工作目录的绝对路径用 `-` 编码出来的：

```
~/Documents/CheerChen/session-sync
  ↓
-Users-cheerchen-Documents-CheerChen-session-sync
```

说明他按"运行时所在目录"切分 session 存储。有这个规则，即便同步了，在相同 repo 打开 Claude Code，session 文件也默认互不可见。（需要切换到 All 选项卡）

我自己的情况是两台 Mac 用户名都不一致——接受"session 文件按路径同步、不按项目语义同步"这个结果。用别的方法来解决跨机器 resume 的问题。这就是后面要讲的 session-index-viewer。

Codex：`~/.codex/sessions/` 下是 `YYYY/MM/DD/<UUID>.jsonl`，按时间分桶 + UUID 文件名，跟当前工作目录无关。但是实际测试下来，Codex 的 session 也有 cwd 信息，存储在每条 jsonl 的首行里。

## 检索层方案

走到这里，数据同步问题解决了。但检索问题还没解决。

有大量 Session 会话的人都知道，`claude --resume` 给的列表几乎没有多少有效信息：

```
  ❯ Complete three tickets and prepare staging masking
    2 weeks ago · develop · 676.6KB

    commit & push
    2 weeks ago · feature/INFRA-999 · 269.4KB · xxx/xxx-masking-platform#93

    Review xxx-masking-platform PR #63 feedback
    2 weeks ago · feature/INFRA-999 · 819.9KB · xxx/xxx-masking-platform#63

    Review S3 lifecycle policy changes
    2 weeks ago · feature/INFRA-999 · 99KB

    ...
```

这种行肉眼根本认不出"修 bug 用的 session"和"讨论演讲 Slides"分别是哪条。

session-index-viewer 就是为这一层写的小工具。仓库：<https://github.com/CheerChen/session-index-viewer>（macOS only，stdlib Python，无外部依赖）。

<!-- TODO: 图 3 — viewer 主界面截图。可以直接用仓库里 docs/screenshot.jpg，也可以本机打开 http://localhost:7333 截一张当前 session 数更真实的版本。 -->

### 它做了什么

- 扫 `~/.claude/projects/` 和 `~/.codex/sessions/` 两个目录
- 把每个 session 解析出来：首条 prompt（你说的第一句）+ 最后一条回复（AI 的最后一句）做成卡片
- 顶部按来源（Claude / Codex）和机器筛选
- 每张卡片右边一个按钮：点一下打开新 Terminal 窗口，自动 `cd <cwd> && claude --resume <id>`（Codex 同理）

单文件 `server.py`，标准库 HTTP server 跑在本地端口 `127.0.0.1:7333`。`install.sh` 用 launchd 注册成开机自启，装完就不需要维护了。

### 几个细节

1. **第一，机器标签是从 cwd 推断出来的**

每个 session 文件里都记着它当时的 cwd。viewer 从 cwd 的 `/Users/<name>/` 或 `/home/<name>/` 里把用户名作为机器标签挂在卡片上。

2. **第二，跨机 resume 时自动适配路径**

这条是和路径编码陷阱配套用的。两端的路径不一致（大概率不一致），就自动适配到当前机器的路径，保证 Open Terminal 后 `cd` 能正确启动会话。

3. **第三，session 文件就是 SOT**

viewer 直接扫文件系统。直接以文件系统为唯一真源，省掉"什么时候重建索引"的烦恼。访问因为有 mtime 缓存都是毫秒级。对一个个人本地工具来说够用了。

## 实施效果

A + Pi + B 三端全部 Up to Date，局域网内一次保存到对端可见大约 15–20 秒（FSEvents → hash → push 的链路开销）。两个 folder 当前规模：

| folder | 文件数 | 体积 |
|---|---|---|
| `~/.claude/projects/` | 249 | 106 MB |
| `~/.codex/sessions/` | 122 | 70 MB |

在本地安装好 viewer 之后，访问 `http://localhost:7333` 直接打开 session-index-viewer，搜索对话可能提到的关键词就能定位，点击卡片->恢复会话。

## 收尾

总结一下实施的心得，首先拆分了两层问题：**同步层** 和 **检索层**，分别用 Syncthing 和 session-index-viewer 解决。同步层的核心是树莓派做中转站，保持 A/B 不直接配对；检索层的核心是以文件系统为 SOT ，按首条 prompt + 最后一条回复做卡片展示。
