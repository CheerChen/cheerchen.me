+++
date = '2025-09-18T12:00:00+09:00'
draft = false
title = 'PR のコンテキストを AI に投入！自作 CLI ツール「pr-dump」の紹介'
seo_description = "GitHub プルリクエストの全コンテキスト（メタデータ、コメント、コード差分）を単一テキストファイルに集約し、AI レビューを効率化する自作 CLI ツール「pr-dump」の開発背景、機能、具体的な使用例を詳細に解説します。"
tags = ["AI", "GitHub", "開発ツール"]
categories = ["AI 協作"]
cover = 'bitbucket411-blog-1200x-branches2.png'
images = ['bitbucket411-blog-1200x-branches2.png']
nolastmod = true
+++

## はじめに

日本の開発チームで働く非ネイティブスピーカーとして、PR のレビューコメントを書くのは毎回ちょっとした挑戦です。技術的な判断だけでなく、日本語で丁寧かつ正確に伝える必要があるからです。

だから AI に下書きを頼むことが多いのですが、毎回 PR のコンテキスト（概要、コメントスレッド、diff）を手作業でコピペするのが、地味に面倒でした。

「この作業、自動化すべきだ」と思い、**`pr-dump`** という小さな CLI ツールを作りました。本記事では、その機能と開発背景、そして具体的な使い方についてご紹介します。

## 📕 `pr-dump` とは？

`pr-dump` は、指定した GitHub プルリクエスト（PR）の全てのコンテキスト（メタデータ、全コメント、コード差分）を、単一のテキストファイルにまとめて出力するコマンドラインツールです。

狙いはシンプルで、GitHub 上に散らばっている情報を 1 枚のテキストに揃えて、AI に渡しやすくすることです。

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

## 🚀 なぜ既存ツールでは不十分だったのか

自作する前に、既存の選択肢を調査しました。

- **PR-Agent**：CI/CD 上で自動レビューを実行する設計で、diff は取得できますが、PR 上の人間同士の議論（タイムラインコメント）はコンテキストに含まれません。しかし今回解決したかった課題は「既存の議論を踏まえて、AI にレビューコメントの下書きを頼む」ことであり、議論が欠落していては使えませんでした。
- **GitHub Copilot Chat**：PR ページ上で質問できますが、出力がチャットの中に閉じており、ローカルの AI（Gemini 等）にコンテキストを渡すことができません。
- **手作業でコピペ**：最も確実ですが、PR のメタデータ・全コメント・diff を揃えるのに毎回 3〜5 分かかります。週に 5 件レビューすれば、年間で 15 時間以上の損失になります。

以上を踏まえて、「PR の全コンテキストを 1 ファイルに集約する」という単機能の CLI を自作する判断をしました。正直に言えば、`pr-dump` は「万人向けのツール」ではなく、「自分の課題を解決するために生まれた個人ツール」です。でも、同じ悩みを持つ方が一人でもいれば、作った甲斐があります。

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

レビューコメントの下書き以外にも、こんな使い方ができます。

1. **コードレビューの高速化**:
    膨大な PR をレビューする必要があるシニアエンジニアが、`pr-dump` で生成したファイルを AI に渡し、「この PR の重要な変更点と潜在的なリスクを要約して」と依頼するだけで、数秒で核心を掴めます。

2. **複雑な PR の迅速な理解**:
    長期間にわたる議論でコメントが数十件に及ぶ PR でも、AI に「この PR の論点は何？最終的なコードで、どの問題が解決された？」と聞くことで、新規参加者でも素早くキャッチアップできます。

3. **リリースノートやドキュメントの自動生成**:
    マージされた PR のコンテキストを元に、「この変更に関するリリースノートの草案を書いて」と AI に依頼すれば、ドキュメント作成の手間が大幅に削減されます。

## 類似ツールとの比較

GitHub エコシステムには他にも AI ツールがあります。それぞれの狙いを理解しておくと使い分けがしやすくなります。

| 比較項目 | pr-dump | PR-Agent | GitHub Copilot Chat |
| :--- | :--- | :--- | :--- |
| **主な目的** | PR 全体のコンテキストを集約し、**人間や AI へのインプットを生成**する | PR プロセスを自動化し、**レビューや説明文生成を代行**する | PR ページ上でコード差分について質問し、**レビューを補助**する |
| **実行環境** | ローカル CLI | GitHub Actions (CI/CD) | GitHub の PR ページ |
| **コンテキスト範囲** | PR 全体（メタデータ、全コメント、差分） | 主に PR のコード差分 | PR 内のコード差分（Copilot が自動で取得する範囲） |
| **最適な用途** | 複雑な PR のレビュー補助、AI への詳細な質問 | 定型的な PR のレビュー自動化、説明文の自動生成 | PR のコード差分に関する具体的な質問、レビューコメントの提案 |
| **コスト** | 無料（OSS） | 無料（OSS だが、裏側で OpenAI 等の API キーが必要） | GitHub Copilot のサブスクリプションが必要 |

他のツールと競合するのではなく、AI に渡す「素材」を作るところに役割を絞っています。

## おわりに

`pr-dump` は自分の困りごとを解消するために作った小さなツールです。同じように PR レビューで AI に下書きを頼みたい方には役に立つかもしれません。

試した感想やフィードバックをいただけると嬉しいです。
