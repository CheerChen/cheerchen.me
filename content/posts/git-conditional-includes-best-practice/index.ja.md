+++
date = '2026-07-24T18:00:00+09:00'
draft = false
title = 'コミット名や PR の誤送信を防ぐ：Git includeIf と GitHub CLI (gh) のアカウント自動切替'
seo_description = "Git の includeIf によるコミット名・SSH 鍵の切替と、GitHub CLI (gh) および Claude Code や Devin 等の AI エージェントにおけるディレクトリ別アカウント自動切替（Shell Wrapper）の実践ガイド。"
tags = ["Git", "GitHub", "開発ツール", "Claude Code", "ベストプラクティス"]
categories = ["技術"]
cover = 'git_identity.png'
images = ['git_identity.png']
nolastmod = true
+++

### 背景

複数のプロジェクトを切り替えて作業していると、会社のリポジトリで個人メールアドレスを使ってコミットしてしまったり、逆に個人リポジトリで会社のアカウントを使ってしまったりすることがあります。

先日もミスしてリモートにプッシュしてしまいました。再発を防ぐために設定を見直しました。

---

### 修正方法：プッシュ済みのコミット情報を直す

#### 直近のコミットだけを修正する場合

直近 1 件のコミットだけであれば、`git commit --amend` で修正できます。

```bash
GIT_COMMITTER_NAME="正しいユーザー名" GIT_COMMITTER_EMAIL="正しいメールアドレス" git commit --amend --author="正しいユーザー名 <正しいメールアドレス>" --no-edit
```

修正後、リモートに強制プッシュします。

```bash
git push --force-with-lease
```

#### 過去の複数コミットをまとめて修正する場合

##### 1. 公式推奨ツール（`git-filter-repo`）を使う方法

Git 公式では従来の `git filter-branch` が非推奨となり、高速で安全な **`git-filter-repo`** の使用が推奨されています。

Homebrew などでインストールします。

```bash
brew install git-filter-repo
```

リポジトリのルートで以下を実行し、旧アドレスを新アドレスに置き換えます。

```bash
git filter-repo --email-callback '
return b"正しいメールアドレス@example.com" if email == b"誤った旧メールアドレス@example.com" else email
' --name-callback '
return b"正しいユーザー名" if email == b"誤った旧メールアドレス@example.com" else name
' --force
```

実行後、強制プッシュします。

```bash
git push --force-with-lease
```

##### 2. インタラクティブに修正する方法（`git rebase -i`）

直近数件のコミットを手動で選びたい場合は、`git rebase -i` を使います。

```bash
git rebase -i HEAD~5
```

エディタが開いたら、修正したいコミットの `pick` を `edit`（または `e`）に変更して保存します。該当のコミットで停止したら、以下を実行して進めます。

```bash
git commit --amend --author="正しいユーザー名 <正しいメールアドレス>" --no-edit
git rebase --continue
```

すべて完了したら `git push --force-with-lease` で反映します。

---

### 条件付きインクルード（includeIf）による Git ユーザー情報の自動切り替え

毎回手動で注意するのは限界があるため、ディレクトリ配下ごとに Git ユーザー情報を自動で選択するように設定します。

Git 2.13 以降で利用できる **`includeIf`** 機能を使います。

#### 設定手順

たとえば、以下のようなディレクトリ構成を想定します。

- 仕事用プロジェクト：`~/dev/work/`
- 個人用プロジェクト：`~/dev/personal/`

##### 1. 個別の設定ファイルを作成する

仕事用（`~/.gitconfig-work`）：

```ini
[user]
    name = 会社でのユーザー名
    email = 会社でのメールアドレス@work.com
```

個人用（`~/.gitconfig-personal`）：

```ini
[user]
    name = 個人のユーザー名
    email = 個人のメールアドレス@personal.com
```

##### 2. 全体設定（`~/.gitconfig`）に `includeIf` を追加する

`~/.gitconfig` の末尾に以下を追記します。

```ini
[includeIf "gitdir:~/dev/work/"]
    path = ~/.gitconfig-work

[includeIf "gitdir:~/dev/personal/"]
    path = ~/.gitconfig-personal
```

パスの末尾にスラッシュ `/` を忘れないように注意してください。

---

### SSH 鍵の管理と双方向リダイレクト設定

SSH 鍵も仕事用と個人用で分ける場合、`~/.ssh/config` にホスト別名（Host）を定義します。

```text
Host github.com-work
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_work
  IdentitiesOnly yes

Host github.com-personal
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_personal
  IdentitiesOnly yes
```

次に、それぞれの Git 設定ファイルに `insteadOf` ルールを追加します。

仕事用（`~/.gitconfig-work`）：

```ini
[user]
    name = 会社でのユーザー名
    email = 会社でのメールアドレス@work.com

[url "git@github.com-work:"]
    insteadOf = git@github.com:
```

個人用（`~/.gitconfig-personal`）：

```ini
[user]
    name = 個人のユーザー名
    email = 個人のメールアドレス@personal.com

[url "git@github.com-personal:"]
    insteadOf = git@github.com:
```

これで、`git clone git@github.com:org/repo.git` と標準の URL を指定しても、カレントディレクトリに応じて自動的に `github.com-work` や `github.com-personal` に読み替えられ、正しい SSH 鍵が使われます。

---

### 課題：GitHub CLI (gh) と AI エージェントでのアカウント混同

Git のコミット名や SSH 鍵の自動切り替えはこれで解決しました。しかし、GitHub CLI (`gh`) を使って PR を作成したり、Claude Code や Devin などの AI エージェントに操作させたりする際に、新たな問題が起きました。

個人プロジェクトのディレクトリで AI エージェントに PR 作成を指示したところ、`gh` コマンドが会社のデフォルトアカウントのまま実行され、会社のアカウントで PR が作成されてしまいました。

#### なぜ gh は includeIf を引き継げないのか

Git の `includeIf` は `git` コマンド自体の設定です。一方、`gh` は独立した CLI ツールであり、特定のホスト（`github.com`）に対して 1 つの Active アカウントしか保持できません。

`gh auth status` を実行すると、常に 1 つのアカウントだけが `Active account: true` になっています。カレントディレクトリを判断してアカウントを自動切替する機能は `gh` 自体には用意されていません。

#### プロンプト（指示文）で制御しようとした場合の課題

当初、AI エージェントの設定ファイル（`CLAUDE.md` や `AGENTS.md`）に「`gh` を実行する際は `GH_TOKEN="$(gh auth token --user <user>)" gh ...` と環境変数を付与すること」という指示を書きました。

しかし、実際に運用してみると以下の問題がありました。

1. **人間の手動実行に対応できない**：ターミナルで自分が手動で `gh pr create` を実行する際にはプロンプト指示が機能しません。
2. **コンテキストの浪費**：すべてのツール実行指示に環境変数付与のルールを含めるため、Context Window のトークンを無駄に消費します。
3. **複数ツールの管理コスト**：Claude Code、Devin、Codex、Cursor など、利用する AI ツールごとに設定ファイルを用意して同じルールを書き込む必要があり、メンテナンスが煩雑になります。

---

### 解決策：Shell Wrapper による自動インターセプト

プロンプトで制御するのではなく、Shell の環境変数レイヤーで透明に処理する方針に切り替えました。

#### 1. ラッパースクリプト（`~/bin/gh`）の作成

PATH の優先順位が高いディレクトリ（例：`~/bin/gh`）に、`gh` と同名のスクリプトを作成します。カレントディレクトリ（`$PWD`）を判定し、適切な `GH_TOKEN` をセットして本来の `gh` 二进制ファイルを呼び出します。

```bash
#!/bin/bash
# カレントディレクトリに応じて GitHub アカウントの Token を自動選択する

# Homebrew でインストールされた本物の gh の絶対パス
REAL_GH="/opt/homebrew/bin/gh"

case "$PWD/" in
  *"$HOME/dev/work/"*)
    TARGET_USER="work-user"
    ;;
  *"$HOME/dev/personal/"*)
    TARGET_USER="personal-user"
    ;;
  *)
    TARGET_USER=""
    ;;
esac

if [ -n "$TARGET_USER" ]; then
  TOKEN="$("$REAL_GH" auth token --user "$TARGET_USER" 2>/dev/null)"
  if [ -n "$TOKEN" ]; then
    export GH_TOKEN="$TOKEN"
  fi
fi

exec "$REAL_GH" "$@"
```

実行権限を付与します。

```bash
chmod +x ~/bin/gh
```

#### 2. 注意点：Subshell と Zsh の読み込み順序

ラッパースクリプトを設置する際、Zsh の設定ファイル読み込み順序に注意が必要です。

##### 非対話型 Subshell に対応するため `~/.zshenv` に設定する

Claude Code や Devin などの AI エージェントは、バックグラウンドのサブプロセス（Subshell）でコマンドを実行します。

Zsh の挙動は以下のとおりです。
- **`~/.zshrc`**：対話型シェル（ターミナル画面）でのみ読み込まれる。
- **`~/.zshenv`**：対話型・非対話型を問わず、すべての Zsh 起動時に読み込まれる。

`~/.zshrc` にのみ `PATH` を設定した場合、手動のターミナル操作ではスクリプトが呼ばれますが、AI エージェントのサブプロセス実行時には通過せず、システム標準の `/opt/homebrew/bin/gh` がそのまま使われてしまいます。

そのため、`~/.zshenv` 内で `~/bin` を PATH の先頭に設定します。

```zsh
# ~/.zshenv で PATH の先頭に ~/bin を指定
export PATH="$HOME/bin:$HOME/.local/bin:$PATH"
```

##### Homebrew の `brew shellenv` による PATH 上書きを防ぐ

`~/.zshrc` 内で `eval "$(/opt/homebrew/bin/brew shellenv)"` を呼び出している場合、Homebrew によって `/opt/homebrew/bin` が PATH の先頭に再挿入されることがあります。

`brew shellenv` の実行直後に、再度 `~/bin` を PATH の先頭に配置します。

```zsh
# ~/.zshrc
eval "$(/opt/homebrew/bin/brew shellenv)"

# ~/bin を再優先化
export PATH="$HOME/bin:$HOME/.local/bin:$PATH"
```

---

### 動作検証

設定後、各環境での挙動を確認します。

1. **個人プロジェクトディレクトリでの確認**：
   ```bash
   cd ~/dev/personal/my-repo
   gh api user --jq .login
   # 実行結果: personal-user
   ```

2. **仕事用プロジェクトディレクトリでの確認**：
   ```bash
   cd ~/dev/work/company-repo
   gh api user --jq .login
   # 実行結果: work-user
   ```

3. **AI エージェントのサブプロセス模擬確認**：
   ```bash
   zsh -c "cd ~/dev/personal/my-repo && gh api user --jq .login"
   # 実行結果: personal-user
   ```

手動でのターミナル操作でも、AI エージェントによるバックグラウンド実行でも、ディレクトリに応じたアカウント切り替えが自動で行われるようになりました。

---

### まとめ

1. **コミット履歴の修正**：`git commit --amend` や `git-filter-repo` を利用。
2. **Git コミット名・SSH 鍵**：`~/.gitconfig` の `includeIf` と `insteadOf` による自動切替。
3. **GitHub CLI (gh)・AI エージェント**：`~/bin/gh` ラッパースクリプトと `~/.zshenv` の `PATH` 設定による自動切替。

プロジェクトを適切なディレクトリに配置しておけば、アカウントの取り違えを意識することなく作業を進められます。
