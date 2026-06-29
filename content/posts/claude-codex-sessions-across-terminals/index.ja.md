+++
date = '2026-06-19T10:00:00+09:00'
draft = false
title = '2 台の Mac の間で Claude Code / Codex のセッションを引き継ぐ：Syncthing + session-index-viewer'
seo_description = "Raspberry Pi を経由して 2 台の Mac の間で ~/.claude/projects と ~/.codex/sessions を Syncthing で同期し、自作の session-index-viewer で最初の prompt と最後の返信からセッションを検索してワンクリックで resume する構成のまとめ。スター型トポロジーを選んだ理由、パスエンコーディングの罠、append-write 衝突のリスク、viewer の設計について書いています。"
tags = ["Syncthing", "Claude Code", "Codex", "Homelab", "Raspberry Pi"]
categories = ["技術"]
nolastmod = true
cover = 'cover.jpg'
images = ['cover.jpg']
+++

<!-- TODO: カバー画像、後で追加 -->

## 背景

困っていたのはシンプルで、私は MacBook を 2 台持っていて（A と B）、両方で Claude Code と Codex を仕事や Side Project で日常的に使っています。この 2 台の間をシームレスに行き来して、いつでも前のセッションを resume したい、というのが希望でした。

実際の会話履歴はサービス側に保存されていて、インデックスにあたるセッションファイルがローカルに置かれている。つまり、2 台間でセッションファイルが同期できれば、どちらの Mac からでも resume して中断した場所から続けられるはず。まずは同期の問題を解決する、というのが一段目の考え方です。

二つ目の悩みは、`claude --resume` や `codex --resume` で表示される一覧が、それぞれ一行程度のテキストしかなく、どれがどのセッションだったのか目視ではほぼ判別できないこと。これが検索層の問題です。

## なぜクラウド版を直接使わないのか

まず正直に認めておくと、これは完全にクラウドで解ける問題です。Claude.ai/code、Cursor のクラウド chat 同期、GitHub Codespaces 上で Claude Code を動かす、あるいは Devin / Replit Agent / Lovable / v0 のような完全クラウド sandbox。どれもこの記事より短い道筋です。

それでもローカル CLI を選んでいるのは、以下の個人的なこだわりがあるからです：

- Claude Code と Codex の両方を同時に立ち上げて切り替えながら使いたい。クラウド方式だとどれか 1 社にロックインされがち
- 個人プロジェクトが Pi 上の docker daemon、ssh key、`.envrc` などローカル環境に依存していて、クラウドの sandbox では一から再構築する必要がある
- Homelab が好きで、自分の手で問題を解決するのが好き

なので、この記事は「ローカル CLI 派」の方を想定して書いています。

## まずは各ツールの設定ファイル構造

`~/.claude/projects/` 配下は cwd をエンコードしたディレクトリ構造で、その中にその cwd で発生したセッションの jsonl ファイルが入っています：

```~/.claude/projects/
  -Users-cheerchen-Documents-CheerChen-session-sync/
    5a3f8b2c-...jsonl
    8d1e4f7a-...jsonl
  -Users-cheerchen-Documents-CheerChen-other-project/
    1c2d3e4f-...jsonl
```

`~/.codex/sessions/` は日付バケットでディレクトリ分けされていて、その日付下に発生したセッションの jsonl ファイルが入っています：

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

Claude のセッションはパスに紐づき、Codex のセッションはパスと無関係。Claude のセッションは追記書き込み、Codex のセッションは一括書き込みという違いがあります。構造を理解した上で、有効な同期方法とセッションを特定する方法を探していきました。

以下、2 つの層に分けて紹介します。同期層は Syncthing、検索層は自作の小さなツール、その名も session-index-viewer です。

## 同期層の方針

Syncthing で 2 台の Mac の `~/.claude/projects/` と `~/.codex/sessions/` を、家にある Raspberry Pi（以下 Pi）経由で相互に同期します。

トポロジーはスター型：A ↔ Pi ↔ B、A と B は直接ペアリングしません。

<!-- TODO: 図 1 — トポロジー図。A ↔ Pi ↔ B の 3 ノード、Pi に "Receive Only + Staggered Versioning" のラベル、各 Mac 上に viewer の小アイコン。横長レイアウト。 -->

なぜ A↔B 直接ではないか？

MacBook はどちらも閉じたりスリープしたりするので、2 台が同時にオンラインになる時間帯がそもそも短いんです。一方で Pi は常時稼働なので、常に起きている中継ノードとして機能してくれます。A/B のどちらか起きている側が Pi と同期し、オフライン側の状態は Pi が保持。これで A と B が互いに待ち続ける状態を回避できます。

### Pi の役割：Read-Only 中継

Pi 上の Syncthing は **Receive Only** に設定します。A と B からの更新を受け取るだけで、「Pi 側のローカル変更」を逆に push することはしません。

加えて **Staggered File Versioning**（デフォルト 30 日保持）を有効にしておくと、A や B から来た削除や上書きはすべて Pi 上の `.stversions/` に履歴として残ります。

### Pi 上の compose

Pi 上のサービスはすべて `/opt/stacks/<name>/` 配下に統一していて、dockge で管理しています。Syncthing も同じパターン：

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

`network_mode: host` は必須です：Syncthing の LAN ディスカバリは 21027/udp のマルチキャスト、直接同期は 22000 を使います。

Pi 起動後、GUI は `http://<pi-ip>:8384`。`claude-projects` と `codex-sessions` の 2 つの folder を作って、両方とも **Receive Only + Staggered Versioning（30 日）** に設定します。

### A 側（B も同様）

```bash
brew install syncthing
brew services start syncthing
```

`http://127.0.0.1:8384` を開いて、Pi の device ID を Remote Devices に追加。2 つの folder は両方 **Send & Receive** にして、パスはそれぞれ `~/.claude/projects` と `~/.codex/sessions` に向けます。

<!-- TODO: 図 2 — Pi Syncthing GUI のメイン画面スクリーンショット。https://syncthing.cheerchen.me または LAN 内の http://192.168.0.110:8384 にアクセスし、2 つの folder が Up to Date、3 つの device（pi-relay + Mac 2 台）が全部オンラインの全体像を撮る。 -->

### いくつかのポイント

1. `~/.claude/` 全体を Syncthing に入れてはいけません。配下の `projects/` だけを選びます。

`~/.claude/` には他に以下のようなディレクトリがあります：

- `statsig/`: SDK のステートキャッシュ、Claude Code を起動するたびに更新される
- `shell-snapshots/`: セッションごとに生成される
- `todos/`: 内部の task ステートファイル
- `cache/`: 文字どおりキャッシュ

これらの共通点は：高頻度の小さいファイル、ローカル限定のランタイムステート、機器間で共有する意味がない、ということです。`~/.claude/` 全体を同期してしまうと、Syncthing がこれらのディレクトリに振り回されることになります。

2. Claude Code / Codex のパスエンコーディング

`~/.claude/projects/` 配下のサブディレクトリ名は、カレントワーキングディレクトリの絶対パスを `-` でエンコードしたものです：

```
~/Documents/CheerChen/session-sync
  ↓
-Users-cheerchen-Documents-CheerChen-session-sync
```

つまり「実行時のディレクトリ」でセッションのストレージが切り分けられている、ということです。このルールがあるため、同期しても、同じ repo で Claude Code を開くと、セッションファイルはデフォルトでは互いに見えません（All タブに切り替える必要があります）。

私の場合、2 台の Mac のユーザー名が一致していないので、「セッションファイルはパス単位で同期されるが、プロジェクトの意味単位ではない」という結果を受け入れて、別の方法で機器をまたいだ resume の問題を解決します。それが後ほど紹介する session-index-viewer です。

Codex の `~/.codex/sessions/` 配下は `YYYY/MM/DD/<UUID>.jsonl`、日付バケット + UUID ファイル名で、カレントワーキングディレクトリとは無関係です。ただし実際に確かめてみると、Codex のセッションにも cwd 情報は含まれていて、各 jsonl の先頭行に書かれています。

## 検索層の方針

ここまでで、データ同期の問題は解決しました。でも検索の問題はまだ残っています。

セッションをたくさん持っている人なら分かると思いますが、`claude --resume` で出てくる一覧には有効な情報がほとんどありません：

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

この一行表記では「バグ修正に使ったセッション」と「プレゼン資料を相談したセッション」を目視で見分けるのは無理です。

session-index-viewer はこの層のために書いた小さなツールです。リポジトリ：<https://github.com/CheerChen/session-index-viewer>（macOS only、stdlib Python、外部依存なし）。

<!-- TODO: 図 3 — viewer のメイン画面スクリーンショット。リポジトリ内 docs/screenshot.jpg を使うか、ローカルで http://localhost:7333 を開いて、現状のセッション数を反映した版を撮る。 -->

### 何をしているか

- `~/.claude/projects/` と `~/.codex/sessions/` の 2 ディレクトリをスキャン
- 各セッションをパース：最初の prompt（あなたの最初の発話）+ 最後の返信（AI の最後の返答）をカード化
- 上部に source（Claude / Codex）とマシン名のフィルタ
- 各カードの右側にボタン：押すと新しい Terminal ウィンドウを開いて、自動で `cd <cwd> && claude --resume <id>` を実行（Codex も同様）

`server.py` という単一ファイル、標準ライブラリの HTTP server がローカルポート `127.0.0.1:7333` で起動します。`install.sh` で launchd に登録して起動時に自動起動。設定後はメンテナンス不要です。

### いくつかのディテール

1. **マシン名タグは cwd から推測している**

各セッションファイルには当時の cwd が記録されています。viewer は cwd の `/Users/<name>/` または `/home/<name>/` からユーザー名を抜き出して、マシン名タグとしてカードに付けます。

2. **機器をまたいだ resume 時にパスを自動で書き換え**

これはパスエンコーディングの罠とセットで使います。2 台のパスが一致していない（たいてい一致していない）場合、自動で現在のマシンのパスに合わせる。Open Terminal した後の `cd` がちゃんと走るように。

3. **セッションファイル自体が SOT**

viewer は直接ファイルシステムをスキャンします。ファイルシステムを唯一の真実の源（SOT）として扱うことで、「いつインデックスをリビルドするか」という悩みを省いています。mtime キャッシュがあるので、アクセスはミリ秒単位で済みます。個人用のローカルツールとしてはこれで十分です。

## 運用してみての効果

A + Pi + B の 3 台すべて Up to Date、LAN 内で片方の保存が相手に見えるまで大体 15–20 秒（FSEvents → hash → push のリンクオーバーヘッド）。2 つの folder の現状の規模：

| folder | ファイル数 | 容量 |
|---|---|---|
| `~/.claude/projects/` | 249 | 106 MB |
| `~/.codex/sessions/` | 122 | 70 MB |

ローカルで viewer をインストールしたあとは、`http://localhost:7333` で session-index-viewer を開き、会話で出てきそうなキーワードを検索すれば該当セッションが見つかります。カードをクリック → 会話復元、で完了です。

## まとめ

実装して得られた知見をまとめておくと、まず問題を 2 つの層に分割しました：**同期層** と **検索層**、それぞれ Syncthing と session-index-viewer で解決しています。同期層の核心は Raspberry Pi を中継点に置き、A/B を直接ペアリングしないこと。検索層の核心はファイルシステムを SOT とし、最初の prompt + 最後の返信でカード表示することです。
