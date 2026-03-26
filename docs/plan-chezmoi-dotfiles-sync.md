# Dotfiles Sync: Deploying chezmoi Across Devices

## Overview

使用 chezmoi 管理和同步跨设备的配置文件（starship, ghostty, claude 等），通过 GitHub 私有仓库存储。

## Phase 1: 设备 A 初始化（当前设备）

```bash
# 1. 安装
brew install chezmoi

# 2. 初始化（会创建 ~/.local/share/chezmoi 作为 source 目录）
chezmoi init

# 3. 添加要管理的配置文件
chezmoi add ~/.config/starship.toml
chezmoi add ~/.config/ghostty/config
chezmoi add ~/.claude.json              # claude code config
# 根据需要继续添加...

# 4. 确认添加了什么
chezmoi managed

# 5. 关联 GitHub 仓库并推送
chezmoi cd    # 进入 source 目录（~/.local/share/chezmoi）
git remote add origin git@github.com:<user>/dotfiles.git
git add .
git commit -m "Initial dotfiles"
git push -u origin main
```

**注意**：避免添加含敏感信息的文件（token、密码）。如果必须添加，使用 chezmoi 的加密功能（age 或 gpg）。

## Phase 2: 设备 B 部署（已有配置的设备）

### 关键：`chezmoi init --apply` 的行为

`chezmoi init --apply <repo>` 实际上是三步的组合：

| 步骤 | 等价命令 | 行为 |
|------|---------|------|
| 1. clone repo | `chezmoi init <repo>` | 把 repo 克隆到 `~/.local/share/chezmoi`，不动本地文件 |
| 2. 计算差异 | （内部）| 对比 repo 中每个文件与本地现有文件 |
| 3. 覆盖应用 | `chezmoi apply` | **直接用 repo 版本覆盖本地文件，不会提示** |

**结论**：`--apply` 会无条件覆盖。如果设备 B 有你想保留的配置，不要用 `--apply`。

### 安全部署流程（推荐）

```bash
# 1. 安装 chezmoi
brew install chezmoi   # 或 apt/pacman/...

# 2. 只 clone，不 apply
chezmoi init <repo>

# 3. 查看完整差异（最重要的一步）
chezmoi diff

# 输出示例：
# --- a/home/user/.config/starship.toml   (本地现有)
# +++ b/home/user/.config/starship.toml   (repo 版本)
# @@ -1,3 +1,3 @@
# -command_timeout = 300     ← 本地值
# +command_timeout = 500     ← repo 值
```

看完差异后，根据情况选择下面的策略。

### 策略 1：repo 为准，覆盖本地

本地配置不重要，或者已经确认 repo 版本更好。

```bash
chezmoi apply
```

### 策略 2：逐个文件决定

部分文件想用 repo 版本，部分想保留本地。

```bash
# 查看某个文件的差异
chezmoi diff ~/.config/starship.toml

# 这个文件用 repo 版本
chezmoi apply ~/.config/starship.toml

# 这个文件保留本地版本，并更新回 repo
chezmoi re-add ~/.config/ghostty/config
```

### 策略 3：3-way merge 逐个合并

两边都有改动，需要手动合并。

```bash
# 合并所有有差异的文件（会逐个打开 merge 工具）
chezmoi merge-all

# 或合并单个文件
chezmoi merge ~/.config/starship.toml
```

chezmoi 默认使用 vimdiff，可以配置其他工具：

```toml
# ~/.config/chezmoi/chezmoi.toml
[merge]
    command = "code"
    args = ["--diff", "--wait", "{{ .Source }}", "{{ .Target }}"]
```

### 策略 4：备份后覆盖（最保险）

```bash
# 手动备份本地配置
cp -r ~/.config/starship.toml ~/.config/starship.toml.bak
cp -r ~/.config/ghostty ~/.config/ghostty.bak

# 放心覆盖
chezmoi apply

# 出问题随时恢复
cp ~/.config/starship.toml.bak ~/.config/starship.toml
```

## Phase 3: 日常同步工作流

### 修改配置后推送

```bash
# 方式 A：直接编辑 source（推荐）
chezmoi edit ~/.config/starship.toml   # 编辑 source 中的副本
chezmoi apply                          # 应用到本地
chezmoi cd && git add . && git commit -m "update starship" && git push

# 方式 B：本地编辑后同步回 source
vim ~/.config/starship.toml            # 直接改本地文件
chezmoi re-add ~/.config/starship.toml # 把变更同步回 source
chezmoi cd && git add . && git commit -m "update starship" && git push
```

### 其他设备拉取更新

```bash
chezmoi update
# 等价于 git pull + chezmoi apply
# 注意：同样是无条件覆盖，如果本地有未同步的改动会被冲掉
```

安全做法：

```bash
chezmoi git pull                # 只拉取 source
chezmoi diff                    # 看差异
chezmoi apply                   # 确认后再应用
```

## 进阶：多设备差异化配置

当 Mac 和 Linux 需要不同配置时，用模板：

```bash
# 把普通文件转为模板
chezmoi chattr +template ~/.config/starship.toml
```

模板示例（`starship.toml.tmpl`）：

```toml
command_timeout = 500

{{ if eq .chezmoi.os "darwin" -}}
[os.symbols]
Macos = "󰀵"
{{ else if eq .chezmoi.os "linux" -}}
[os.symbols]
Linux = "󰌽"
{{ end -}}
```

## 需要管理的配置文件清单

| 文件 | 路径 | 备注 |
|------|------|------|
| Starship | `~/.config/starship.toml` | |
| Ghostty | `~/.config/ghostty/config` | |
| Claude Code | `~/.claude.json` | 注意排除 token |
| Git | `~/.gitconfig` | 注意排除 credential |
| Zsh | `~/.zshrc` | |

## 总结：冲突处理速查

| 场景 | 命令 |
|------|------|
| 全新设备，无现有配置 | `chezmoi init --apply <repo>` |
| 已有配置，repo 为准 | `chezmoi init <repo>` → `chezmoi diff` → `chezmoi apply` |
| 已有配置，逐个决定 | `chezmoi init <repo>` → `chezmoi diff` → 逐文件 `apply` 或 `re-add` |
| 已有配置，需要合并 | `chezmoi init <repo>` → `chezmoi merge-all` |
| 本地改了想推回 repo | `chezmoi re-add <file>` → push |
| 拉取远端但不确定差异 | `chezmoi git pull` → `chezmoi diff` → `chezmoi apply` |
