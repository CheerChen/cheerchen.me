+++
date = '2025-09-18T12:00:00+09:00'
draft = false
title = '导出 PR 的上下文！介绍自制 CLI 工具 “pr-dump”'
seo_description = "详细介绍自制 CLI 工具 “pr-dump” 的开发背景、功能和具体使用示例，该工具可将单个 GitHub 拉取请求的全部上下文（元数据、评论、代码差异）整合到单个文本文件中，从而提高 AI 审查的效率。"
keywords = ["GitHub", "拉取请求", "AI", "代码审查", "CLI 工具", "pr-dump", "Gemini", "Claude", "自动化", "开发效率"]
tags = ["开发工具", "AI 助手", "生成式 AI", "最佳实践", "GitHub"]
categories = ["技术分享"]
cover = 'bitbucket411-blog-1200x-branches2.png'
images = ['bitbucket411-blog-1200x-branches2.png']
nolastmod = true
+++

## 前言

最近，我越来越多地使用像 Gemini 和 Claude 这样的大型语言模型（LLM）来进行代码审查。但是，在请求 AI 审查之前，“准备上下文”这个步骤总觉得非常麻烦。

PR 的摘要、与同事讨论的评论 Thread，以及实际的代码变更（diff）... 这些信息分散在 GitHub 上，逐一复制粘贴非常繁琐。

为了解决这个问题，我开发了一个名为 **`pr-dump`** 的简单 CLI 工具。本文将介绍其功能、开发背景以及具体的使用方法。

## 📕 什么是 `pr-dump`？

`pr-dump` 是一个命令行工具，可将指定的 GitHub 拉取请求（PR）的所有上下文（元数据、所有评论、代码差异）汇总并输出到单个文本文件中。

该工具的核心价值在于，**它将 GitHub 上分散的多元信息转换为“扁平化”的单一文本，以 AI 最容易理解的形式提供**。

## 🛠️ 安装与使用

使用 **Homebrew (macOS/Linux)** 可以轻松安装。

```bash
# 添加 Formula
brew tap CheerChen/pr-dump

# 安装
brew install pr-dump
```

其他安装方法请参见 [GitHub 仓库](https://github.com/CheerChen/pr-dump)。

### 使用方法

**⚠️ 重要：必须先登录 GitHub CLI。**

```bash
# 1. 移动到包含要审查的 PR 的仓库目录
cd /path/to/your/repository

# 2. 指定 PR 编号并执行
pr-dump 123

# 这样，当前目录下就会生成一个 review.txt 的文件。
```

### 输出示例

生成的文件结构如下：

```plaintext
################################################################################
# PULL REQUEST CONTEXT: #42
################################################################################

--- METADATA ---
PR Title: Add user authentication system
PR Body: This PR implements JWT-based authentication...

--- ALL COMMENTS ---
## Timeline Comments ##
- Timeline comment from @developer1:
  Looks good, but consider adding rate limiting...

## Code Review Comments ##
- Code comment from @reviewer on `auth.go` (line 25):
  This function should handle edge cases...

--- GIT DIFF ---
diff --git a/auth.go b/auth.go
new file mode 100644
index 0000000..abc1234
+++ b/auth.go
@@ -0,0 +1,45 @@
+package auth
...
```

### 主要功能

- **完整的上下文**: 完整获取 PR 的标题、正文、所有审查评论、时间线上的讨论以及 `git diff` 的信息。
- **为 AI 审查优化**: 输出是为 AI 进行代码审查而优化的结构化文本格式。
- **排除噪音**: 默认过滤掉像 `pr-agent` 这样的机器人自动生成的评论，让您可以专注于人工讨论。
- **操作简单**: 只需一个易于记忆的命令，即可瞬间获取所需信息。

## 🚀 为什么创建这个工具

作为一名在日工作的老中，在用日语和英语进行技术讨论时，我经常请求 AI 帮助理解评论并审查 PR。然而，每次都手动收集这些文本，效率实在过于低下。

## 与 Gemini 的协作示例

使用 `pr-dump` 生成的文本文件，在向像 Gemini 这样的对话式 AI 传递上下文时非常有用。

下面，我将展示一个实际使用的例子。

### 1. 使用 `pr-dump` 生成上下文

首先，我们运行 `pr-dump` 生成文本文件。

```sh
P-LMD0001:awesome-project xxx$ pr-dump 573
🚀 Starting context generation for PR #573...
✅ Success! All context has been saved to 'review.txt'.
📄 Text format ready for LLM input.
```

### 2. 将文件附加到 Gemini 并提问

接下来，将这个 `review.txt` 文件附加到 Gemini，并使用如下提示提出具体请求。

> **提示示例：**
>
> 阅读 @review.txt 他问 もしこのテーブルに「説明」や「優先度」などの列を追加して整理したい場合も対応できますが、追加しますか？ 是什么意思?
>

### 3. Gemini 的回答示例

然后，AI 会在理解上下文的基础上，生成准确的回答。

{{< gemini >}}

这个 PR 的作者在变更内容部分创建了一个表格，用于汇总通知类型和对应的通知渠道。他就此向审查者询问：

“もしこのテーブルに「説明」や「優先度」などの列を追加して整理したい場合も対応できますが、追加しますか？”

也就是说，他想确认是否需要在现有表格的基础上，增加一些列来说明每个通知的含义（说明）以及其紧急程度（优先级），从而使表格更易于管理。

{{< /gemini >}}

通过这种方式，可以使与 AI 的对话变得非常顺畅和具体。

### 其他使用场景

这个工具不仅仅是“对话辅助”。在现代开发工作流程中，它扮演着“适配器”的角色，帮助所有开发人员最大限度地利用 AI 的优势。

1. **加快代码审查速度**:
    需要审查大量 PR 的高级工程师，只需将生成的文件交给 AI，并请求“总结这个 PR 的重要变更点和潜在风险”，即可在几秒钟内掌握核心内容。

2. **快速理解复杂的 PR**:
    即使是经过长期讨论、有数十条评论的 PR，也可以通过向 AI 提问“这个 PR 的主要争议点是什么？最终的代码解决了哪些问题？”，让新加入的成员也能快速跟上进度。

3. **自动生成发布说明和文档**:
    基于已合并 PR 的上下文，向 AI 请求“为这个变更写一份发布说明的草稿”，可以大大减少编写文档的工作量。

## 与类似工具的比较

GitHub 生态系统中还有其他优秀的 AI 工具。了解每个工具的设计理念和目的，可以更有效地利用它们。

| 比较项目 | pr-dump | PR-Agent | GitHub Copilot Chat |
| :--- | :--- | :--- | :--- |
| **主要目的** | 汇总 PR 的全部上下文，为**人类或 AI 生成输入** | 自动化 PR 流程，**代为执行审查和生成描述** | 在 PR 页面上就代码差异提问，**辅助审查** |
| **执行环境** | 本地 CLI | GitHub Actions (CI/CD) | GitHub 的 PR 页面 |
| **上下文范围** | 整个 PR（元数据、所有评论、差异） | 主要为 PR 的代码差异 | PR 内的代码差异（Copilot 自动获取的范围） |
| **最佳用途** | 辅助审查复杂 PR、向 AI 提出详细问题 | 自动化审查常规 PR、自动生成描述 | 就 PR 的代码差异提出具体问题、建议审查评论 |
| **成本** | 免费（开源） | 免费（开源，但后端需要 OpenAI 等 API 密钥） | 需要 GitHub Copilot 订阅 |

## 结语

我认为像 `pr-dump` 这样 **为开发者填补现有平台与 AI 之间“鸿沟”的工具** 未来将变得越来越重要。目前它只是一个为解决我个人问题而诞生的小工具，但我相信，在与 AI 共存的现代软件开发中，它有潜力提高许多开发人员的生产力。

欢迎您试用并提供反馈。
