+++
date = '2025-09-18T12:00:00+09:00'
draft = false
title = 'PR のコンテキストを AI に投入！自作 CLI ツール「pr-dump」の紹介'
seo_description = "GitHub プルリクエストの全コンテキスト（メタデータ、コメント、コード差分）を単一テキストファイルに集約し、AI レビューを効率化する自作 CLI ツール「pr-dump」の開発背景、機能、具体的な使用例を詳細に解説します。"
keywords = ["GitHub", "プルリクエスト", "AI", "コードレビュー", "CLI ツール", "pr-dump", "Gemini", "Claude", "自動化", "開発効率化"]
tags = ["開発ツール", "AI 助手", "生成式 AI", "最佳実践", "GitHub"]
categories = ["技術分享"]
cover = 'bitbucket411-blog-1200x-branches2.png'
images = ['bitbucket411-blog-1200x-branches2.png']
nolastmod = true
+++

## はじめに

最近、Gemini や Claude のような大規模言語モデル（LLM）を使ってコードレビューを行う機会が増えてきました。しかし、AI にレビューを依頼する前の「コンテキスト準備」に手間がかかる、と感じたことはありませんか？

PR の概要、開発者との議論が交わされたコメントスレッド、そして実際のコード変更（diff）...。これらの情報は GitHub 上で散在しており、一つ一つコピー＆ペーストするのは非常に面倒です。

この課題を解決するため、私は**`pr-dump`**というシンプルな CLI ツールを開発しました。本記事では、その機能と開発背景、そして具体的な使い方についてご紹介します。

## 📕 `pr-dump` とは？

`pr-dump` は、指定した GitHub プルリクエスト（PR）の全てのコンテキスト（メタデータ、全コメント、コード差分）を、単一のテキストファイルにまとめて出力するコマンドラインツールです。

このツールの核心的な価値は、**GitHub 上に散在する多元情報を「フラットな」単一テキストに変換し、AI が最も理解しやすい形で提供する**点にあります。

## 🛠️ インストールと使い方

**Homebrew (macOS/Linux)** を使えば簡単にインストールできます。

```bash
# Formula をタップ
brew tap CheerChen/pr-dump

# インストール
brew install pr-dump
```

その他のインストール方法は [GitHub リポジトリ](https://github.com/CheerChen/pr-dump) をご覧ください。

### 使い方

**⚠️ 重要：事前に GitHub CLI へのログインが必須です 。**

```bash
# 1. レビューしたい PR があるリポジトリに移動
cd /path/to/your/repository

# 2. PR 番号を指定して実行
pr-dump 123

# これだけで、カレントディレクトリに review.txt のようなファイルが生成されます。
```

### 出力サンプル

生成されるファイルは以下のような構成になっています。

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

### 主な機能

- **完全なコンテキスト**: PR のタイトル、本文、全てのレビューコメント、タイムライン上の議論、そして `git diff` の情報を漏れなく取得します。
- **AI レビューに最適化**: 出力は、AI がコードレビューを行うために最適化された構造化テキスト形式です。
- **ノイズの排除**: `pr-agent` のような Bot による自動コメントをデフォルトでフィルタリングし、人間による議論に集中できます。
- **シンプルな操作**: 覚えやすいコマンド一つで、必要な情報を一瞬で取得できます。

## 🚀 なぜこのツールを作ったのか

開発のきっかけは、私自身の経験にあります。非ネイティブスピーカーとして日本語・英語で技術的な議論を行う際、AI にレビューコメントの草案作成をよく依頼していました。しかし、そのたびに手作業でコンテキストを収集するのが非効率だと感じていました。

## Gemini との連携例

`pr-dump` で生成したテキストファイルは、Gemini のような対話型 AI にコンテキストを渡す際に非常に役立ちます。

以下に、実在の PR から生成した `review.txt` を使って、実際にレビューを依頼する例を示します。

### 1. `pr-dump` でコンテキストを生成

まず、`pr-dump` を実行してファイルを生成したとします。

```sh
P-LMD0001:awesome-project xxx$ pr-dump 573
🚀 Starting context generation for PR #573...
✅ Success! All context has been saved to 'review.txt'.
📄 Text format ready for LLM input.
```

### 2. Gemini にファイルを添付して質問

次に、この `review.txt` を Gemini に添付し、以下のようなプロンプトで具体的な依頼をします。

> **プロンプト例：**
>
> read @review.txt he ask もしこのテーブルに「説明」や「優先度」などの列を追加して整理したい場合も対応できますが、追加しますか？ what is he means?
>

### 3. Gemini からの回答例

すると、AI はコンテキストを理解した上で、的確な回答を生成してくれます。

{{< gemini >}}

この PR の作成者は、変更内容のセクションにある通知の種類と通知先チャンネルをまとめたテーブルについて、レビュワーに次のように尋ねています。

「もしこのテーブルに『説明』や『優先度』などの列を追加して、もっと分かりやすく整理したい場合は対応できますが、いかがでしょうか？」

つまり、現在のテーブルに加えて、各通知が何を意味するのか（説明）、そしてどれくらい緊急性が高いのか（優先度）といった情報を列として追加し、より管理しやすくすることができるが、その対応は必要かどうか、という意図を確認しています。

{{< /gemini >}}

{{< gemini >}}

The author of this Pull Request created a table in the description that maps different types of notifications (e.g., "Errors In Check", "Check Timeout") to their corresponding Slack channels.

After presenting this table, the author then asks in Japanese:
> もしこのテーブルに「説明」や「優先度」などの列を追加して整理したい場合も対応できますが、追加しますか？

This sentence translates to:
"If you would like to organize this table by adding columns such as 'Description' or 'Priority', I can do that. Shall I add them?"

In short, the author is offering to improve the table in the PR description by adding more informational columns, such as:

- Description: To explain what each notification is for.
- Priority: To indicate the urgency of each notification.

The author is asking the reviewer whether they think this enhancement is needed to make the table clearer and more organized.

{{< /gemini >}}

このように、`pr-dump` を使うことで、AI との対話が非常にスムーズかつ具体的になります。

### 他の使用シーン

このツールは、単なる「会話のサポート」に留まりません。現代の開発ワークフローにおいて、あらゆる開発者が AI の恩恵を最大限に受けるための「アダプター」としての役割を果たします。

1. **コードレビューの高速化**:
    膨大な PR をレビューする必要があるシニアエンジニアが、`pr-dump` で生成したファイルを AI に渡し、「この PR の重要な変更点と潜在的なリスクを要約して」と依頼するだけで、数秒で核心を掴めます。

2. **複雑な PR の迅速な理解**:
    長期間にわたる議論でコメントが数十件に及ぶ PR でも、AI に「この PR の論点は何？最終的なコードで、どの問題が解決された？」と聞くことで、新規参加者でも素早くキャッチアップできます。

3. **リリースノートやドキュメントの自動生成**:
    マージされた PR のコンテキストを元に、「この変更に関するリリースノートの草案を書いて」と AI に依頼すれば、ドキュメント作成の手間が大幅に削減されます。

## 類似ツールとの比較

GitHub エコシステムには他にも優れた AI ツールが存在します。それぞれのツールの思想と目的を理解することで、より効果的に活用できます。

| 比較項目 | pr-dump | PR-Agent | GitHub Copilot Chat |
| :--- | :--- | :--- | :--- |
| **主な目的** | PR 全体のコンテキストを集約し、**人間や AI へのインプットを生成**する | PR プロセスを自動化し、**レビューや説明文生成を代行**する | PR ページ上でコード差分について質問し、**レビューを補助**する |
| **実行環境** | ローカル CLI | GitHub Actions (CI/CD) | GitHub の PR ページ |
| **コンテキスト範囲** | PR 全体（メタデータ、全コメント、差分） | 主に PR のコード差分 | PR 内のコード差分（Copilot が自動で取得する範囲） |
| **最適な用途** | 複雑な PR のレビュー補助、AI への詳細な質問 | 定型的な PR のレビュー自動化、説明文の自動生成 | PR のコード差分に関する具体的な質問、レビューコメントの提案 |
| **コスト** | 無料（OSS） | 無料（OSS だが、裏側で OpenAI 等の API キーが必要） | GitHub Copilot のサブスクリプションが必要 |

他のツールと競合するのではなく、**開発者が AI を主体的に活用するための「素材」を提供する**という点で、ユニークなポジションを築いています。

## おわりに

`pr-dump` は、私自身の課題を解決するために生まれた小さなツールですが、AI と共存する現代のソフトウェア開発において、多くの開発者の生産性を向上させるポテンシャルを秘めていると信じています。

既存のプラットフォームと AI の間の「溝」を埋めるツールは、今後ますます重要になるでしょう。

ぜひ一度お試しいただき、フィードバックをいただけると嬉しいです。
