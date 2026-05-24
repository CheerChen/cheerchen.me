+++
date = '2026-05-22T22:00:00+09:00'
draft = false
title = '当 AI 反问你：从一道误读的算法题，看 Claude 与 Codex 的对齐哲学'
seo_description = "同一道东大创造情报学的图算法题、同一个我误读的 prompt，Codex 顺着我做下去，Claude 反过来 quote 题目原文质疑我的起点假设。这不是谁更聪明的问题，而是两家公司对齐目标的不同——一篇关于 prompt 忠诚 vs 题意忠诚的实证记录。"
tags = ["AI", "Claude", "Codex"]
categories = ["AI 协作"]
cover = 'Gemini_Generated_Image_w38fstw38fstw38f.jpg'
images = ['Gemini_Generated_Image_w38fstw38fstw38f.jpg']
nolastmod = true
+++

### 把 10 年前的 Python2 代码翻出来重做

最近自己的 vibe 项目暂时停了，没什么新东西要 ship，反倒把过去准备**东京大学创造情报学**入学考试编程题的代码翻出来重做。打开一看，文件还是 Python2 写的，`print` 没有括号，`dict.iteritems()` 还在那里—— 10 年前的我留下的。

10 年前谁能想到，写算法题可以一行代码都不用写。我先让 Claude（Opus 4.7） 和 Codex（GPT-5.5） 把代码适配成 Python3，重新跑数据。两个 session 平行开着，本意只是看哪个跑得顺。

中途 Claude 那边卡了一段时间（thinking 模式下偶尔会这样），我就把结果核验让 Codex 接手。我们吭哧吭哧地改了算法，拿新写的 DFS 算了一通，结果跑出来没啥问题，Problem Solved。

后来 Claude 那边起来，我顺手把同一道题丢给它"再验算一下" ——翻车了。

### “再读一次题目”

题目大致是这样的（**东大创造情报学 2010 年冬*，原题日英对照）：

> 给定一张时变有向图，边集随时间变化（`u -> v` 表示在时刻 t 添加边，`!u -> v` 表示在时刻 t 删除边）。定义 `R(t)` 为 root-set，由顶点 `v_0` 和**从 `v_0` 出发在时刻 t 可达的所有顶点**组成。求若干时刻下 `R(t)` 的大小。

但我自己读题时根本没看——更准确说，10 年前的我也没好好看题。看示例就往以前做过的图论题上套。

{{< ask >}}
我：好，那么 2-2 他说把 b.txt 的所有操作对 G0（我知道是图）进行了以后得到了一个完整图 Gb 路径合集 Rb 求 Rb 的大小

我：那么我从哪一个点出发？跟他的题目有什么关系？
{{< /ask >}}

{{< claude >}}

起点不是你选的，起点是 R 的定义本身写死的。再读一次题目的 R(t) 定义：

> Let R(t) be a root-set: the set of vertices consisting of the vertex v_0 and all reachable vertices from v_0 at time t.
{{< /claude >}}

注意这里有个关键细节：Claude 没有顺着我已经做的代码答，它直接**重新 quote 了题目原文**，告诉我"起点不是你可以选的，是 R 的定义里写死的"。

这是一个 meta 层的纠正——不是回答"从哪出发"，是质疑"你为什么认为可以选起点"。我一直都用"输入第一条边的源顶点"作为起点。

{{< figure src="2026-05-22 23.04.41.png" title="" >}}

### problem fidelity（题意忠诚）

起点假设错只是这道题暴露的第一层 problem fidelity。后面还有一层更深的术语陷阱：题目里的 `R(t)` 是 **root-set**（从根顶点 v_0 长出来的可达顶点集合），但中文/英文混着读，我一度把 `R` 自动联想成 "route"，把 `|R(t)|` 误解为"路径总数"，进而把 Q2-3 的"|R(t)| 在 1000 上下穿越的所有时刻"想成"路径数穿越 1000"，整个算法思路被带偏。

Claude 在我犯这个错时的处理也很值得记一笔——它不是一次性纠正完就过，是在我后续每次试图绕开（"BFS 时每个新 reachable 点都相当于路径 +R(t-1)?"）时**反复 quote 原定义**把我拉回"R 是顶点集合，不是路径计数"。这种**持续锚定到原文**的行为，跟一次性反问起点错是同一种对齐倾向的延伸——

**problem fidelity 是整段对话里持续拒绝"用户脑补的版本"压过"题目定义的版本"的能力**。

### prompt fidelity（Prompt 忠诚）

{{< ask >}}
我：你这个坑货，Claude 发现我们做的前提就是错的，题目要求我们从 "0" 出发，你实现的 `first_source` 错了。
{{< /ask >}}

{{< chatgpt >}}
你说得对。这个前提如果题目指定从 0 出发，那 `first_source()` 就是错的，不是实现细节问题，而是题意入口点错了。我现在把 v2 改成显式默认从 "0" 出发，并去掉"第一条边起点"这个假设。
{{< /chatgpt >}}

也就是说，Codex 接受了我的误读 prompt，得到了一个**前提错了、但内部自洽**的答案。数值上这个答案跟真实答案差一个数量级——Q2-2 的 `|R_b|` 用 `first_source` 起点算出来是 7 或 1，正确答案是 357。但只看程序输出，看不出哪里错。

更糟的是题目本身给的两个示例第一行**都恰好是** `0->1`，所以 `first_source()` 在示例数据上巧合等于 `"0"`，输出全对——这条 bug 10 年没暴露，一半要归功于示例数据的偶然。

{{< figure src="2026-05-22 23.04.54.png" title="" >}}

### Prompt 忠诚 vs 题意忠诚 —— 对齐目标的差异

最容易得出的浅结论是"Claude 更聪明"或者"Opus 4.7 完胜 GPT 5.5"。但这条结论的问题在于：

- 它会随版本失效（半年后 GPT-6 或 Sonnet 5 一出，结论就废了）；
- 它没有解释**为什么**会有这种差异，只是把现象贴上一个模型优劣标签；
- 它跟那些"Claude Code 隐藏功能 / 这一行 env 让 Codex 提速 3 倍"的姿态没本质区别——都是不解释机制的 claim。

我更感兴趣的是机制。两个模型展示的不是不同的智力，是**不同的优先级**：

**Codex 倾向 prompt fidelity——以用户给的 prompt 为优先 ground truth。**
你说 `first_source` 是起点，那 `first_source` 就是起点。你的 prompt 是合同，模型负责高质量地执行合同。

**Claude 倾向 problem fidelity——以问题本身的定义为优先 ground truth，必要时质疑用户。**
即使你 prompt 里说起点是 `first_source`，但题目原文里 `R(t)` 的定义把起点写死了，那 Claude 会先指出你和题目原文不一致，再决定怎么做。

这两种倾向都是**有意为之**的对齐选择，不是 bug。OpenAI 的 coding 产品线（Codex CLI、GPT-5 系的 coding 角色）面向"执行力"场景——你已经知道要做什么，模型负责高质量地把它做出来。Anthropic 的对齐里"必要时反向 push back 用户"的权重明显更高，Claude 在面对模糊 / 矛盾 / 可能误读的 input 时倾向先停下来确认。

这不是 Anthropic 比 OpenAI 高明，是两家公司**在 prompt 忠诚 vs 题意忠诚的 trade-off 上选择了不同的 default**。这条选择会比任何一个具体的版本号活得久。

### 同样的 push back，在不同场景下是 feature 还是 bug

这是我写这篇文章想说的最重要的一点，也是绝大多数"模型对比"文章会跳过的部分。

**在算法题、数学题、形式化任务里，Claude 的 push back 几乎一定是 feature。** 因为这类任务有一个客观的 problem definition——题目原文、数学公式、形式化规范——它存在于用户的 prompt 之外，且不会因为用户的误读而改变。模型对照原始定义来质疑用户，永远是对的。这次的图论可达性问题就是这种场景：题目原文就在那里，`v_0 = "0"` 写得清清楚楚。

**但在生产代码、产品工程、业务需求场景下，Claude 的 push back 不一定是 feature，甚至常常是 friction。** 原因是这些场景里**根本不存在一个客观的"题目原文"**——业务需求本身就是 underspecified 的，用户给的 prompt 就是当下最权威的 spec。一个总是质疑你 prompt 的 Claude，在这种场景下会反复打断节奏，用模型自己想象的"更合理"的需求来挑战你刚说出口的需求。

举个具体的例子：你跟 Claude 说"帮我把这个按钮改成红色"，一个高 push back 倾向的模型可能回"你确定要红色吗？根据可用性原则，警告色不应该用在主要 CTA 上"——这在算法题语境里是好习惯，在产品迭代语境里是 friction。Codex 那种 prompt fidelity 强的执行调性反而更省事：你说红色，那就红色，下一个 task。

所以**这次实验的结论不能直接外推**。"Claude 在算法题上更会 push back" 是 robust 的观察；"Claude 在所有 coding 场景都更好用" 是错的延伸。哪一个 default 更适合你，取决于你做的 task 类别——你是在写 spec 清晰的算法 / 形式化任务，还是在写 spec 模糊的业务代码？

### 一个 workflow takeaway：单模型可能永远不发现这种错

**如果我只用一个模型，这种"前提就错了的正确答案"很可能永远不会浮出来**。我自己读题就读错了，跟我读错的方向一致的模型自然不会 catch 出来。我能 catch 是因为：

- 用了两个模型，刚好其中一个对齐倾向是 push back；
- 跨模型把工作传递了一次，触发了"换个角度看"的自然检查；
- 用了相对低成本的"再验算一下"作为 default 行为。

所以当：**关键问题（spec 严格 / 错了代价大 / 自己不确定）默认用 dual-model cross-check **是更好实践。一个模型作为执行者，另一个模型在最后阶段作为 reviewer——尤其当 reviewer 那一方对齐里有 push back 倾向时，价值最大。

这不是说要把所有 task 都跑两遍——大部分日常 task 不值得。但 spec 严格的任务、错了不容易发现的任务、自己 prompt 本身可能误读的任务，多花一次 cross-check 的成本远低于一次 silent fail 的成本。

### 边界与诚实

写到这里我必须停一下，明确**不能证明什么**：

- 这次只跑了一道题。**单个 sample 不构成评测**。
- 模型版本一直在变。这次的具体表现差异下一个版本可能就反过来，或者两边都进化到同样的 push back 倾向。
- 算法题是高度结构化的场景，**结论不能外推到所有 coding 任务**。前面已经说过，业务代码场景下 push back 反而可能是 friction。
- 我自己读题就读错了。这次能 catch 是因为题目原文里有可被 quote 的客观定义。如果是一个 spec 本身就模糊的 task，Claude 的 push back 也没有 anchor 可以指向。
- 这次 catch 出来的不是一个 fresh prompt 上 Codex 临时犯的错，是我 10 年前就写进 v0、v1 一直没人质疑的旧 bug 沿袭进了 prompt。换句话说，**Codex 没有"犯错"——它高质量地按我给的（错的）spec 实现了**。问题在我提供的 spec 本身错了，而 Claude 的对齐倾向让它没有照单全收。这正是 prompt fidelity 跟 problem fidelity 真实差异的体现，但也意味着如果题目原文本身没有可对照的定义，Claude 也 catch 不出来。

我希望这篇文章能跟 X 上那些"这一行 env 让 Codex 提速 3 倍 / Claude Code 隐藏功能"的姿态形成对比——那种姿态的问题不是它说得对不对，是它**永远不标 scope，永远不贴证据，永远不说自己结论的边界**。

所以这次实验的诚实结论是：

> 在一道有客观 problem definition 的算法题上，同一个我误读的 prompt，Codex 接受了误读并按它执行，Claude quote 题目原文反问我的前提。这是 prompt fidelity 与 problem fidelity 的对齐目标差异，不是聪明程度差异。这一差异在算法题场景下倾向于让 Claude 占优。

仅此而已。

### 结尾：invariant 比版本号活得久

模型版本会变，benchmark 会过期，"谁完胜"的结论会随每一次 release 翻篇。但**两家公司在 prompt 忠诚 vs 题意忠诚上的 default 选择**这件事，反映的是更深一层的产品哲学——执行器还是协作者，按合同做还是必要时挑战合同。这层东西不会因为一次模型升级就消失，最多在不同方向上变得更清晰。

下次有人在 X 上甩出一个"X 模型完胜 Y 模型"的结论，**值得停下来问的不是"是不是真的"，是"它是在哪个对齐维度上完胜，那个维度跟我做的工作匹配吗"**。

如果半年后 GPT-6 在同样的误读 prompt 下也 push back 了，这篇文章里 invariant 的部分仍然成立——只是说明 OpenAI 在这个维度上的 default 选择变了，而不是这个 trade-off 不存在了。