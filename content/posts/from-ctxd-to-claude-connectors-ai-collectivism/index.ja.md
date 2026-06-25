+++
date = '2026-05-24T20:00:00+09:00'
draft = false
title = 'ctxd から Claude Code Connectors へ：AI 時代に個人ヒーローはいない'
description = "自作 3 つの CLI を ctxd に統合して快適に使っていたら、Claude Code の Connectors が一気に 8 割の価値を吸い取った話。AI 時代の「集合主義」と「遅くやるくらいなら、やらない方がマシ」についての振り返り。"
seo_description = "slack-thread-dump、pr-dump、confluence-dump という自作 3 つの CLI を ctxd に統合し、Claude Code の skill と組み合わせて快適に使っていた。しかし 2026 年 4 月末、Claude Code が Connectors をリリースし、同じ機能が公式にエンドツーエンドで提供されるようになった。AI 時代の「集合主義」に直面した個人開発者としての振り返り。"
tags = ["AI", "開発ツール", "Claude Code", "振り返り"]
categories = ["AI 協作"]
nolastmod = true
cover = 'Gemini_Generated_Image_n5paesn5paesn5pa.jpg'
images = ['Gemini_Generated_Image_n5paesn5paesn5pa.jpg']
+++

ctxd は、Claude Code が Slack / GitHub PR / Confluence / Jira のコンテキストを自動で読めるようにするために作った小さなツールです。実際にかなり便利で、かなりの時間を節約してくれました。ただ数か月後、Claude Code Connectors がその中核価値の 8 割を公式機能として持っていきました。

この出来事をきっかけに、AI 時代における個人ツールプロジェクトの価値とは何なのかを、もう一度考えることになりました。

### ctxd はどう生まれたか

去年末から今年初めにかけて、私は 3 つの CLI を順番に作っていました。

- `slack-thread-dump`：Slack のスレッドを markdown / text にエクスポート；
- `pr-dump`：GitHub PR のメタデータ・コメント・diff を 1 ファイルにまとめ、AI コードレビューに食わせる（[以前の記事](../introducing-pr-dump-for-ai-code-review/) で紹介済み）；
- `confluence-dump`：Confluence ページ（子ページ・画像含む）を markdown にエクスポート、同じ認証で Jira チケットも対応。

3 つ目を書いている途中で気づきました。これは全部同じ種類の課題だと。SaaS に散らばったコンテキストを、LLM がそのまま読める平坦なテキストに落とす、ということです。3 つのリポジトリを統合・改名して `ctxd` にし、認証（`~/.config/ctxd/config`）も出力（`-O` で自動命名、stderr 自動 quiet）も統一、Homebrew tap で配布しました。

そして `~/.claude/CLAUDE.md` に次のルールを追加しました：

> ユーザーが Slack / GitHub PR / Confluence / Jira の URL を貼って「読んで」「要約して」「翻訳して」「引用して」と言ってきたら、即座に Bash で `ctxd <url>` を実行する。内容を手動で貼ってもらわない。

この skill と組み合わせると、ワークフローが閉じます。Slack のリンクを Claude Code に投げると、自動で `ctxd` が走り、完全なスレッドが対話コンテキストに入る。日常的にかなり快適に使っていました。

ただし、宣伝もしなかったし、同僚に体系的に共有することもしませんでした。

### そして Claude Code が Connectors をリリースした

2026 年 4 月末〜5 月頭、Claude Code が Connectors をエンドツーエンドで搭載しました。Slack / Atlassian (Confluence + Jira) / Microsoft 365 / Asana / Box などが全部内蔵。認証は「Slack の管理画面で user token を取って `~/.config/ctxd/config` に書く」から「OK を押すだけ」に変わりました。

初めて Atlassian connector を繋いだとき、少し呆然としました：

- `mcp__claude_ai_Atlassian__getConfluencePage` が私の Confluence エクスポートを置き換え；
- `mcp__claude_ai_Atlassian__getJiraIssue` が私の Jira エクスポートを置き換え；
- `mcp__claude_ai_Slack__slack_read_thread` が slack-thread-dump を置き換え；
- GitHub は元々 `gh` と公式 MCP があり、pr-dump はただの薄いラッパーでした。

つまり、`ctxd` の価値のおよそ 8 割が、Connectors に一気に吸収されました。

残りの 2 割（オフラインで markdown ファイルとして書き出す、Confluence の子ツリーを再帰一括エクスポート、独自の diff モード）は今でも意味があります。ただそれは「ロングテールの価値」であって、当初の「これがないと AI を使えない」という中核的な価値ではなくなりました。

### でも ctxd は無駄ではなかった

Connectors に 8 割の価値を吸収されたからといって、この半年が無駄だったわけではありません。5 月初めに Connectors が出るまでの期間、ctxd はかなり具体的なリターンを返してくれました。

- **PR レビュー**：PR URL を貼るだけで、AI が「この変更の動機、リスク、確認すべき質問」を出してくれる。diff を 1 行ずつ読むより少なくとも 5 倍は速かった。
- **Slack の返信草案**：日本企業によくある「まず確認 → 背景を一言 → 少し留保 → でも逃げ道も残す → 最後に確認依頼」のような多層的なスレッドは、読むだけで疲れます。Slack thread URL を貼れば、AI がまず会話を理解し、そのまま日本語の返信案まで作ってくれました。
- **Jira ticket**：チーム内部の Jira ticket clone フォーマットに沿って、新しいチケットをそのまま 1 本作れる。
- **同僚の Confluence を読む**：同僚のドキュメントが 30 ページあって引用も多い、という場面で、先に AI に要点整理と重要語句の説明をさせるだけでかなり楽になりました。

これらはすべて**実際に起きたことであり、実際に節約できた時間**です。後から公式機能が出たからといって、その価値が消えるわけではありません。

そして、むしろこちらの方が重要なのですが、**私が一人で収束した最終形（「URL をそのまま LLM に貼る」）は、Anthropic が数か月後に Connectors で提供した対話形態と同じでした**。これは偶然ではないと思います。「何が効率なのか」という私の判断が、Claude Code を作っている人たちの直感と揃っていたということです。AI のように変化の速い領域では、上流プロダクトの直感と揃っていること自体が、「私は X を作った」以上に価値があります。

厳密に言えば、ctxd は置き換えられたのではなく、**検証された**のです。

### AI 時代は集合主義であり、個人主義ではない

最近、姚順宇（Yao Shunyu）の 4 時間インタビュー（[YouTube](https://www.youtube.com/watch?v=ttkd0t5qTD4) / [Apple Podcast](https://podcasts.apple.com/cn/podcast/140-%E5%AF%B9%E5%A7%9A%E9%A1%BA%E5%AE%87%E7%9A%844%E5%B0%8F%E6%97%B6%E8%AE%BF%E8%B0%88-%E8%AF%B7%E5%85%81%E8%AE%B8%E6%88%91%E5%B0%8F%E7%96%AF%E4%B8%80%E4%B8%8B-%E5%9C%A8anthropic%E5%92%8Cgemini%E8%AE%AD%E6%A8%A1%E5%9E%8B-%E6%8A%80%E6%9C%AF%E9%A2%84%E6%B5%8B-%E8%8B%B1%E9%9B%84%E4%B8%BB%E4%B9%89%E5%B7%B2%E8%BF%87%E5%8E%BB/id1634356920?i=1000767107736)）を聞いていて、何度も反芻している一節があります（中国語、私訳）：

> 「AI における個人ヒーロー主義の時代はすでに終わった。今はすべて集合主義で、ヒーロー集団はあっても個人ヒーローはいない。だから個人を神話化するあらゆる物語に対して警戒すべきだ。」

{{< figure src="2026-05-25 0.18.34.jpg" >}}

ctxd という事例は、その縮図です。一人で書いて、一人でメンテして、一人で使って、自己満足していた。でもそれが本物の課題である限り、他にも誰かが必ず解いている。Anthropic 社内のどこかのチーム、Slack 公式、Cursor、Cline、いくつかの OSS プロジェクト……彼らのスピードもリソースも配布力も、個人プロジェクトでは永遠に追いつけません。

だから AI 時代においては、文字通りの意味で「あなたがやらなくても、やる人は山ほどいる」のです。

### 遅くやるくらいなら、やらない方がマシ

前節で書いた「検証された」というのは、個人としては幸運な話です。ただ、より一般的な規則として見るなら、次のことは変わりません。

AI モデルの素の欠点を埋めようとするツールというのは、あなたが vibe で作っている間に、公式がすでに社内で実装済みで、3〜5 週間後にはリリースされてくる可能性が高い。リリースが出た瞬間、あなたの版はむしろ「認知負荷」になります（ユーザーが間もなく淘汰されるツールを学ばないといけない）。

こういうとき、**作らないことが net positive な選択になり得る**。その時間を効率化ツール以外の何かに、あるいはコンテンツ産出に充てた方が、もう少し長持ちするかもしれません。

もちろん「車輪を再発明するな」と言いたいわけではありません。学ぶために、自分で使うために、問題を考え抜くために作る。これは常に価値があります。ただ自分の目的をはっきりさせる必要がある。「学習 / 自用」なのか、それとも「広く配って事実上の標準にしたい」なのか。AI 時代における後者の成功確率は、想像よりずっと低い。

### 付録：それでも ctxd を試したい場合

この記事を読んで、それでも `ctxd` を試したい場合（たとえばコンテキストを完全に自分の手で握りたい、ローカルの markdown ファイルにだけ落としたい）、repo はこちら：

[github.com/cheerchen/ctxd](https://github.com/cheerchen/ctxd)

ただし、ツール本体より大事なことが 1 つあります：**先ほどの skill を `~/.claude/CLAUDE.md` に入れること**（あるいは独立した Claude Code Skill にすること）。このルールがないと、ctxd はただの CLI のままです。ルールが入ってはじめて、リンクを貼った瞬間に Claude Code が自動的に呼んでくれます。

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

ツールは人間が使うものではなく、Agent が使うもの。**ツールの存在を Agent に教えること**の方が、ツール本体より重要です。

### おわりに

結局のところ、ctxd というプロジェクト自体はまったく後悔していません。あの期間に大量の時間を取り返してくれたし、最終的には公式に方向性を検証された。副産物として、抽象化を揃える練習にもなり、PR / Slack / Confluence API の落とし穴も一通り踏めました。

この出来事が最後に教えてくれたのは、「個人プロジェクトには意味がない」ということではありません。「個人プロジェクトは、自分が誰と競走しているのかを理解する必要がある」ということです。学ぶため、自分で使うため、自分の判断を検証するために作るなら、常に価値があります。ただし、AI ワークフローの入口を取りにいくつもりなら、スピードと配布力そのものがプロダクトの一部になります。
