# Blog Taxonomy

This file is the single source of truth for categories and tags.

## How the system works

- Front matter uses **language-neutral slugs** (ASCII, lowercase, hyphenated), e.g. `tags = ["architecture"]`.
- The same slug is used in both `index.zh.md` and `index.ja.md`. Hugo generates one stable URL per slug (`/tags/architecture/`, `/ja/tags/architecture/`).
- Display names per language live in `content/tags/<slug>/_index.zh.md` and `_index.ja.md`. Changing a display name never changes the URL.
- Tags that are identical English strings in both languages (e.g. `AWS`, `Claude Code`) are written directly in front matter — no slug or `_index` file needed.
- **Never rename a slug.** Renaming breaks URLs (404s in Google). To change wording, edit the `title` in the `_index.<lang>.md` files instead.
- When a slug is used in a language for the first time, create `content/tags/<slug>/_index.<lang>.md` with the title from the tables below (same for categories).

## Categories

| Slug | 中文 | 日本語 |
|---|---|---|
| `tech` | 技术 | 技術 |
| `ai-collab` | AI 协作 | AI協働 |
| `career-learning` | 职业与学习 | キャリアと学習 |

Keep categories broad and stable. A new category should usually be useful for more than one future post.

- `tech`: Cloud, architecture, engineering practice, development tools, troubleshooting, infrastructure, and technical conference reports.
- `ai-collab`: AI-assisted work, LLM collaboration, coding agents, prompt and workflow design, and AI tool reflections.
- `career-learning`: Career development, learning methods, personal study notes, and non-core engineering learning.

## Tag Families

### Translated concepts (use the slug)

| Slug | 中文 | 日本語 |
|---|---|---|
| `architecture` | 架构设计 | アーキテクチャ設計 |
| `cloud-native` | 云原生 | クラウドネイティブ |
| `dev-tools` | 开发工具 | 開発ツール |
| `best-practices` | 最佳实践 | ベストプラクティス |
| `troubleshooting` | 问题排查 | トラブルシューティング |
| `retrospective` | 复盘 | 振り返り |
| `realtime` | 实时通信 | リアルタイム通信 |
| `game-dev` | 游戏开发 | ゲーム開発 |
| `generative-ai` | 生成式 AI | 生成AI |
| `raspberry-pi` | 树莓派 | Raspberry Pi |
| `primer` | 扫盲 | 入門 |
| `career` | 职业发展 | キャリア |
| `toolchain` | 工具链 | ツールチェーン |
| `frontend` | 前端 | フロントエンド |
| `options` | 期权 | オプション取引 |

### Language-neutral tags (write directly)

- Cloud / infra: `AWS`, `Kubernetes`, `Serverless`, `DynamoDB`, `Amazon IVS`, `WebRTC`
- AI / agents: `AI`, `Claude`, `Claude Code`, `Codex`, `Gemini`
- Tools: `Git`, `GitHub`, `Docker`, `Homelab`, `Syncthing`
- Languages / frontend: `JavaScript`, `TypeScript`, `Go`, `Rust`, `Bun`, `Vite`
- Platforms / hardware: `macOS`, `Apple Silicon`, `Linux`, `webOS`, `LG`, `Chrome`, `XPC`, `Jellyfin`, `Syncthing`, `Docker`
- Events / domains: `AWS Summit Japan 2025`, `AWS Summit Japan 2026`, `Nintendo`, `Switch 2`

## LLM Editing Notes

When generating or editing a post:

1. Read this file before choosing categories and tags.
2. Prefer one existing category; use its slug, not the translated word.
3. Add a new category only when the article does not naturally fit the existing ones.
4. Tags may be added more freely, but reuse existing slugs/tags where possible.
5. For bilingual posts, use the exact same tag and category slugs in `index.zh.md` and `index.ja.md`.
6. Never invent a second spelling for an existing concept — check the tables above first.
