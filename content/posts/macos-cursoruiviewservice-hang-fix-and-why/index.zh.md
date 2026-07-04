+++
date = '2026-07-04T21:00:00+09:00'
draft = false
title = '每一台 M 系列 MacBook 都必定有的内存泄漏问题？macOS 上 CursorUIViewService 的坑'
seo_description = "macOS Sonoma 之后新增的 CursorUIViewService（Caps Lock 与输入法指示器渲染服务）在 Apple Silicon 上会漏 XPC transaction，导致主线程活锁、内存单调堆积到 GB 级、活动监视器标记为「未响应」。给出禁用 redesigned_text_cursor flag 的根治方案与两种应急方案，并从 hiservices runloop watchdog、launchd idle exit 判定与 SIGTERM 卡在残留 transaction 三个层面拆解根因。"
tags = ["macOS", "Apple Silicon", "问题排查", "XPC"]
categories = ["技术分享"]
nolastmod = true
cover = "cover.jpg"
images = ['cover.jpg']
+++

## 背景

自从上一次用 Gemini 排查 Windows 上卡死的问题之后已经过了一年，在这一年间，我还是保留着怀疑一切大公司软件产品的使用习惯。这几天，我又在 macOS 上遇到了一个问题，经过使用 AI Agent 排查和社区确认，发现这是 macOS Sonoma 之后新增的 `CursorUIViewService` 在 Apple Silicon 上的一个内存泄漏问题。

我使用 MacBook 工作基本不关机（谁会在 MacBook 上关机？），偶尔打开活动监视器一看，一个叫 `CursorUIViewService` 的进程标着「未响应」，内存 **3.94 GB**——什么东西能吃这么多内存？

{{< figure src="SCR-20260704-skcy.png" title="活动监视器里 `CursorUIViewService` 内存持续走高（21 天涨到 2.0 GB、30 天涨到 3.94 GB）" >}}

最离谱的是，macOS 的优化又太好，太过无感知，在内存不够的时候，系统会自动压缩内存、回收 page，甚至把一些进程的内存 swap 到 SSD 上。没有经过非常多天的使用堆积，你可能根本不会注意到这个「未响应」的进程。甚至在活动监视器里、如果没有一行红色的进程，我还觉得不太习惯。

于是，还是那句话 —— “我好歹要知道他到底在卡什么，不能这个世界都变成一个草台班子的模样，我不能接受。”

于是我叫出了最近的新朋友 `GLM 5.2`，让他去查这个问题。

他翻了一遍系统日志和苹果开发者论坛，确认这是 macOS Sonoma 引入、Sequoia 到 Tahoe 都还没修完的一个系统 bug，苹果工程师在 Developer Forums 上已经承认了它影响 Apple Silicon。

## TL;DR

如果你也怀疑自己有这个问题，先到活动监视器里确认一下 `CursorUIViewService` 的状态：

- 进程 CursorUIView 内存占用是不是异常高
- 日志里是不是每秒一次 hiservices watchdog

```bash
log show --last 5m --predicate 'process == "CursorUIViewService"' \
  | grep "why is this taking so long" | head
```

判定标准：

| 检查项 | 命中征兆 |
|---|---|
| CursorUIView | 明显 >500 MB（正常 ~30 MB）、已经显示「未响应」 |
| 日志 | 时间戳严格每秒一次、都是同一线程号 |

都命中就直接执行

### 方案 1：临时强杀（应急）

```bash
# 普通 kill 无效，进程退不掉，必须 SIGKILL
sudo kill -9 $(pgrep CursorUIView)
```

- **风险**：Apple 论坛有报告说 kill 运行中实例可能冻 UI 导致强制重启，先保存好手头工作再执行。

`launchd` 会在下次有文本输入需求时自动拉起一个干净的新实例，内存回到 30 MB 上下。

### 方案 2：禁用新版光标 UI（推荐，根治）

找终端，执行：

```bash
sudo defaults write /Library/Preferences/FeatureFlags/Domain/UIKit.plist \
  redesigned_text_cursor -dict-add Enabled -bool NO
```

执行完**重启 Mac** 生效。

**代价**：Caps Lock 的大写指示器小箭头动画没了，Caps Lock 键的实际功能（切换大写状态）不受影响；输入法切换的指示气泡也会退回旧版风格。日常使用几乎无感。

**注意**：macOS 系统更新（不是所有更新，通常是大版本或含 UIKit 变更的补丁）后这个 flag 可能被重置。再执行一遍即可。

需要特别说明的一点：这条命令**不是**把 `CursorUIViewService` 从系统里禁用掉，`launchd` 该拉还是拉。它真正改变的是**运行时行为**——服务不再累积泄漏的 XPC transaction、不再陷入 runloop 超时、能按设计正常 idle exit。所以修复后依然会看到这个进程短暂出现在 `ps` 输出里，属于正常现象。

到这里问题就已经解决了。下面是给感兴趣的人看的——**为什么这个 bug 会以「活锁」而不是「死锁」的方式表现出来。**

## 根因分析

### CursorUIViewService 是什么、为什么存在

`CursorUIViewService` 是 macOS Sonoma（14）引入的新版文本光标 UI 渲染服务。（Caps Lock 与输入法指示器渲染服务）

- 路径：
```sh
/System/Library/PrivateFrameworks/TextInputUIMacHelper.framework/Versions/A/XPCServices/CursorUIViewService.xpc
```
- 由 `launchd` 按需启动的 XPC 服务
- 职责：渲染 Caps Lock 大写指示器、输入法语言指示箭头、以及新版光标周围的辅助 UI 元素
- 设计上应该在 idle 后自动退出

### 为什么苹果要单独拆一个进程做这件事

Sonoma 之前，光标和 Caps Lock 指示器由前台应用自己的进程渲染，风格靠 AppKit 内部的旧代码路径处理。Sonoma 引入「redesigned text cursor」，做了动画化的指示气泡和更 iOS 化的视觉过渡——这些跨应用一致的 UI 元素需要一个统一的 owner，所以拆成 XPC 服务，由系统管着按需拉起。

XPC 服务的设计初衷很清楚：

- **按需启动**：只有当前台应用真的需要显示这些指示器时，`launchd` 才拉起进程
- **idle exit**：空闲一段时间后自动退出，回收内存
- **崩溃隔离**：这个服务挂了不影响宿主应用

问题就出在「idle exit」这一步——设计上应该退，但 bug 让它退不掉。

一句社区的经典吐槽：
>「This service is the world's most over-engineered capslock indicator, and if you toggle caps lock a lot, it loses its mind.」

### 内存为什么会单调堆积

每次 Caps Lock 或输入法切换，客户端（通常是前台文本应用）通过 XPC 向 `CursorUIViewService` 发请求，服务在主线程跑一整套流程——

从实测日志里画成图长这样：

{{< figure src="xpc-transaction-leak.svg" title="一次 Caps Lock / 输入法切换的调用序列与 transaction 计数：应归零的却残留 2 个" >}}

这套流程涉及多次与 SkyLight / WindowServer 的 XPC transaction。

{{< glm >}}

XPC transaction 是 libxpc 提供的一个引用计数机制——服务代码用 `xpc_transaction_begin()` 声明「我正在处理一件不能被打断的事」，处理完调 `xpc_transaction_end()` 归还引用。
`launchd` 根据当前活跃 transaction 数量判断是否允许进程 idle exit。

bug 在于**某些 transaction 未正确 commit 或 abort**—— `Remaining transactions after SIGTERM: 2` 就是铁证：被信号要求退出时仍有 2 个活 transaction。责任在服务端（`CursorUIViewService`）没在所有代码路径上匹配 begin/end——客户端连接断开本身应该触发清理，但服务端 handler 里的某些分支忘了归还引用。

{{< /glm >}}

{{< ask >}}

你说这些细节我不懂，能不能直接告诉我为什么会 leak？

{{< /ask >}}

GLM 说好，直接给画了一个大白话的三格漫画：

{{< figure src="xpc-transaction-leak-story.svg" title="" >}}

{{< glm >}}

便利店 = CursorUIViewService 进程；客人 = 一次 Caps Lock / 输入法切换；便签 = XPC transaction；老板 = launchd；打烊 = idle exit。

堆积链路：

1. 每次切换泄漏少量 XPC transaction（每来一个客人，店员漏撕两张便签）
2. `launchd` 通过 transaction 计数判断是否允许 idle exit —— （老板规矩：墙上有便签 = 还有活没结清 = 不能打烊）
3. 进程被迫常驻，pending 队列随每次切换单调增长（店永远关不了；墙上的便签一路加，只增不减）
4. 主线程每轮 runloop 要处理越来越长的 pending 队列 → （店员每次处理新客人前，都要先把整面墙翻一遍找记录——翻得越来越慢，一单从毫秒级拖到秒级）
5. 关联资源随 pending 累积 → RSS 从 30 MB 一路涨到几百 MB 甚至 GB 级 （每张便签背后还夹着一叠原料清单、订单副本、外部厂商联系条，越堆越占地方）
6. 内存增长是**单调不可逆**的—— 没有回收路径，只能 SIGKILL 重置（老板只能直接把店砸了重开，墙上便签清空）

{{< /glm >}}

### `why is this taking so long?` 是什么

{{< figure src="SCR-20260704-slcb.png" title="log stream 抓到的 hiservices watchdog：同一主线程，每秒抱怨一次" >}}

卡死时系统日志里最迷惑的一条：

```
[com.apple.hiservices:HIRunLoop] fired; why is this taking so long?
```

这条日志来自 `com.apple.hiservices`——**HIToolbox**（Human Interface Toolbox）的一部分。

HIServices runloop 内部挂了一个**秒级 watchdog 定时器**：每秒检查一次「当前这一轮 runloop 迭代是否还在跑」，如果上一轮还没结束就打印一次抱怨。它不会杀进程、不会重启循环，只是打日志。设计上是给苹果工程师用的观测点。

几点特征佐证：

- 时间戳严格每秒一次—— 定时器特征
- 全部来自同一线程（主线程）—— 不是并发问题，是主线程被拖慢
- 显示主线程卡在 `nextEventMatchingMask:` —— 主线程没死锁，还在跑，只是每轮迭代 >1s

所以——**主线程处于持续慢速运行**，watchdog 每秒醒来发现「还在跑上一轮？」，抱怨一次。

### 为什么 CursorUIViewService「未响应」

活动监视器标记「未响应」的判定，是**主线程长时间不响应 WindowServer 的事件 ping**。

WindowServer 会周期性地给它管理的每个 UI 进程发 event tap ping（社区推测阈值在 8s 上下，苹果没公开），进程要在主线程 pop 一下这个事件、回一个 ack。在本案里：

- 主线程还在跑（没死锁），但每轮 `nextEventMatchingMask:` → 处理事件 → 渲染的迭代耗时 >1s
- WindowServer 的事件 ping 排在 pending 队列尾部，要等前面累积的 transaction 处理完
- 当 pending 队列长到一定程度，响应延迟超过判定阈值 → 标记「未响应」
- 键盘输入、Caps Lock 指示器等依赖该服务的功能同步卡顿，但又不是完全死掉——因为主线程还在跑，偶尔能处理完一轮 pending 队列，短暂恢复响应。

**不是进程冻住不动，而是陷入「慢但未死」的活锁**——主线程持续工作但永远追不上队列，watchdog 每秒抱怨一次。

### 为什么必须 `kill -9` 才行

`launchd` 的 idle exit 判定基于 transaction 计数。SIGTERM 触发优雅退出流程时的默认路径：

1. `launchd` 或用户发 SIGTERM
2. 进程收到信号，走注册的 `atexit` handler、AppKit 的 `applicationWillTerminate:` 等清理钩子
3. libxpc 检查活跃 transaction 计数，非零就 defer 退出、等 transaction 收尾
4. 如果 `ExitTimeOut` 内（launchd plist 默认约 20 秒）transaction 都归零，进程正常退出
5. 超时的话 `launchd` 应该发 SIGKILL 兜底

问题是这里第 4 步永远达不到——泄漏的 transaction 没有归还路径。理论上第 5 步应该救场，但实测 `Remaining transactions after SIGTERM: 2` 日志会反复打印几十秒甚至更久，`launchd` 的兜底 SIGKILL 迟迟不发。可能的原因：`CursorUIViewService` 的 job plist 里 `ExitTimeOut` 被设得很长或干脆没设、或者兜底逻辑对 XPC service 走的是不同路径（有些 XPC service plist 里的 `RunAtLoad`、`ThrottleInterval`、`ProcessType` 组合会改变 launchd 行为）。

这也是方案里必须 `kill -9` 而不能只 `kill` 的原因。

## 什么人最容易踩到

### 长时间不重启、用合盖代替关机

日志和 `spindump` 里有一条容易被忽略的线索：

```
turnstile waiting for WindowServer
```

Turnstile 是 Apple 内部的**优先级传播锁调试基础设施**（可以在 Darwin 开源代码里查到相关 API），出现这条信息意味着 `CursorUIViewService` 正在阻塞等待 WindowServer 响应。

Mac 从睡眠中醒来时，图形栈需要重新协商：WindowServer 重建合成上下文、各服务重新申请 CGS connection、Mach port 重新握手。正常情况下这套协商是幂等的，几十毫秒就完成。

但 `CursorUIViewService` 在唤醒时的重连逻辑有问题——之前的 CGS connection 可能已经失效，服务却还在尝试用旧 handle 发消息，超时后不释放、直接排下一轮，导致 pending 队列立刻堆积一批「僵尸 transaction」。

所以这个问题对长时间不重启，用合盖代替关机的用户（比如我）是必定发生的问题。

### 中文 / 多语用户

英文单语用户几乎不会触发这个 bug——他们不切输入法，一天大概按几十次 Caps Lock，服务进程 idle exit 的机会远大于泄漏累积速度。

中文（以及日文、韩文等）用户就完全不同：

- 输入法切换（英↔中、繁↔简、假名↔汉字）频次通常是每分钟数次到数十次
- 每次切换都走一遍 `deactivateInputModeSwitcher` → `activateInputModeSwitcher` 的完整流程
- 每次流程都是一次泄漏 XPC transaction 的机会
- Ctrl+Space / Caps Lock / Shift 触发的切换路径可能命中不同的 handler 分支，泄漏概率不同

如果再叠加：Apple Silicon 机器、长时间不重启（我连续开机 30+ 天）、频繁睡眠唤醒（MacBook 用户日常）——**四个条件全占**，就是这个 bug 最理想的宿主。

### InputSourcePro 用户

自动切换输入源的工具（如 InputSourcePro）会进一步放大这个问题。

InputSourcePro 这类自动切换输入源的工具会把上面的触发条件全部叠满——它们把每次 app 切换、每次浏览器 tab 切换都变成一次输入法切换，单日切换次数比手动使用高一个数量级。

读它的源码可以确认两件事：

1. 切换走的是 Carbon HIToolbox 的 `TISSelectInputSource`——跟系统菜单栏手动切换、跟 Caps Lock 触发的切换是同一条系统路径，CursorUIViewService 照样被通知、照样漏 XPC transaction。
2. 对中日韩越（CJKV）输入源，为了绕过 macOS「切了但没真切」的 bug，工具单次切换可能触发 2–4 次 `TISSelectInputSource` 调用（`temporaryInputWindow` 策略 2 次、`previousInputSourceShortcut` 策略最多 4 次），每次都是一次泄漏机会。

换句话说，InputSourcePro 用户单次自动切换背后的泄漏量，可能等于手动切换的数倍。作者显然自己也踩到了——在 General 设置页里内置了一个叫「Cursor Lag Fix」的开关，执行的命令跟本文方案 2 一字不差。

如果你是 InputSourcePro 用户，建议直接在设置里打开这个开关，省得自己敲命令。

## 社区时间线

- **2023 Q4，macOS Sonoma 14.0**：新版 redesigned text cursor 上线，`CursorUIViewService` 首次出现。Sonoma 14.1、14.2 期间开发者论坛出现零星报告，多数被误归因为「装了什么第三方输入法插件」。
- **2024 上半年，Sonoma 14.4 前后**：Apple Developer Forums 出现明确的技术帖，包括附上 spindump 和 sample 输出的分析。Apple 工程师首次在回复里确认「aware of the issue, tracking internally」。
- **2024 Q3，macOS Sequoia 15.0**：改动了一部分 IME 相关代码路径，一部分用户报告症状减轻，但 XPC transaction 泄漏本身没修，仍能复现。
- **2025，Sequoia 15.x 系列**：多个 point release 都没有直接触及这块代码。
- **2026，macOS Tahoe 26.x**：截至本文写作（26.5.1），bug 依然存在，我三台机器都是在 Tahoe 上复现的。

关注 Apple radar tracker 或 [openradar](https://openradar.appspot.com/) 有时能查到相关 issue，不过通常没 ETA。

考虑到 macOS 的更新节奏和 Sonoma 之后的 UIKit 变动，指望苹果在 Tahoe 之前修复这个问题的可能性不大。我就不费事去给苹果发 radar 了，以后到手的每一台 M 系列 MacBook，我都会先执行一次禁用 redesigned_text_cursor flag 的命令。

## 参考

- [Apple Community — cursoruiviewservice Not Responding](https://discussions.apple.com/thread/255668660)
- [Apple Developer Forums — Urgent: CursorUIViewService & hiservices](https://developer.apple.com/forums/thread/764085)
- [Apple Developer Forums — Severe Lag on MacBook Air](https://developer.apple.com/forums/thread/759802)
- [Mac Observer — cursoruiviewservice Lag Fix](https://www.macobserver.com/mac/cursoruiviewservice-lag-fix/)
- [InputSourcePro — runjuu/InputSourcePro](https://github.com/runjuu/InputSourcePro)
