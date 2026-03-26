# Hugo Blog Engagement: Views & Likes via Cloudflare Workers + D1

## Overview

为 Hugo 静态博客实现浏览量和点赞功能，使用 Cloudflare Workers 作为 API 后端，D1 作为数据库，零成本部署。

## Architecture

```
┌──────────────┐     fetch      ┌──────────────────┐     SQL     ┌──────────┐
│  Hugo Blog   │  ──────────►   │  Cloudflare      │  ────────►  │    D1    │
│  (静态页面)   │  ◄──────────   │  Worker (API)    │  ◄────────  │ (SQLite) │
│  JS fetch    │   JSON resp    │  /api/view       │   query     │          │
│              │                │  /api/like       │             │ views    │
│              │                │  /api/stats      │             │ likes    │
└──────────────┘                └──────────────────┘             └──────────┘
```

## Prerequisites

- Cloudflare 账号（已有）
- `wrangler` CLI（`npm install -g wrangler`）
- Hugo 站点已部署（Pages 或其他）

## Database Schema (D1)

```sql
-- 浏览量表
CREATE TABLE page_views (
    slug TEXT PRIMARY KEY,
    count INTEGER DEFAULT 0
);

-- 点赞表
CREATE TABLE page_likes (
    slug TEXT NOT NULL,
    ip_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (slug, ip_hash)
);

-- 点赞计数视图（方便查询）
CREATE VIEW like_counts AS
SELECT slug, COUNT(*) as count FROM page_likes GROUP BY slug;
```

**说明**：
- `ip_hash` 存 IP 的 SHA-256 哈希，不存原始 IP，兼顾去重和隐私
- 用复合主键 `(slug, ip_hash)` 天然防重复点赞

## Worker API Design

### Endpoints

| Method | Path | 功能 | 请求体 | 返回 |
|--------|------|------|--------|------|
| POST | `/api/view` | 浏览量+1 | `{ "slug": "my-post" }` | `{ "views": 42 }` |
| POST | `/api/like` | 点赞 | `{ "slug": "my-post" }` | `{ "likes": 7, "liked": true }` |
| GET | `/api/stats?slug=my-post` | 获取统计 | - | `{ "views": 42, "likes": 7, "liked": false }` |

### Key Implementation Details

1. **CORS**：Worker 需返回正确的 CORS headers，允许博客域名跨域请求
2. **IP 去重**：从 `request.headers.get('CF-Connecting-IP')` 获取访客 IP，SHA-256 后存储
3. **liked 状态**：`/api/stats` 根据当前访客 IP 判断是否已点赞，前端据此展示不同 UI
4. **防刷**：同一 IP + slug 的 view 可以按时间窗口限频（如 30 分钟内只计一次）

### Worker Project Structure

```
blog-stats-worker/
├── wrangler.toml       # Worker 配置，绑定 D1
├── src/
│   └── index.js        # Worker 入口，路由 + 处理逻辑
└── schema.sql          # D1 建表语句
```

### wrangler.toml 关键配置

```toml
name = "blog-stats"
main = "src/index.js"
compatibility_date = "2024-01-01"

[[d1_databases]]
binding = "DB"
database_name = "blog-stats"
database_id = "<创建后填入>"
```

## Worker Code Outline

```js
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // CORS preflight
    if (request.method === 'OPTIONS') return handleCORS();

    // 路由
    if (url.pathname === '/api/view' && request.method === 'POST') {
      return handleView(request, env.DB);
    }
    if (url.pathname === '/api/like' && request.method === 'POST') {
      return handleLike(request, env.DB);
    }
    if (url.pathname === '/api/stats' && request.method === 'GET') {
      return handleStats(request, env.DB);
    }

    return new Response('Not Found', { status: 404 });
  }
};

// handleView: INSERT OR REPLACE into page_views, count+1
// handleLike: INSERT OR IGNORE into page_likes (重复则忽略)
// handleStats: SELECT count from both tables + check liked
```

## Hugo Integration

### 1. 创建 partial 模板

`layouts/partials/engagement.html`：在文章底部渲染浏览量和点赞按钮。

```html
<div class="post-engagement" data-slug="{{ .File.ContentBaseName }}">
    <span class="view-count">👁 <span id="views">-</span> views</span>
    <button class="like-btn" id="like-btn">
        ♡ <span id="likes">-</span>
    </button>
</div>
```

### 2. 前端 JS

`static/js/engagement.js`：页面加载时 fetch stats，点击点赞时 POST like。

核心逻辑：

```
页面加载 → GET /api/stats?slug=xxx → 渲染浏览量和点赞数
         → POST /api/view (slug) → 浏览量+1
点击点赞 → POST /api/like (slug) → 更新点赞数 + 切换按钮状态
```

### 3. 在文章模板中引入

在 `layouts/posts/single.html`（或主题对应位置）中加入 partial 和 JS。

## Deployment Steps

```bash
# 1. 初始化 Worker 项目
wrangler init blog-stats-worker

# 2. 创建 D1 数据库
wrangler d1 create blog-stats

# 3. 执行建表
wrangler d1 execute blog-stats --file=schema.sql

# 4. 开发调试
wrangler dev

# 5. 部署
wrangler deploy

# 6. 在 Hugo 站点中集成前端代码，部署站点
```

## Free Tier Limits（个人博客绰绰有余）

| 资源 | 免费额度 | 日均 1000 PV 预估用量 |
|------|---------|---------------------|
| Workers 请求 | 10万/天 | ~3000 次（view + stats + like） |
| D1 行读取 | 500万/天 | ~3000 次 |
| D1 行写入 | 10万/天 | ~1000 次 |
| D1 存储 | 5 GB | 几 MB |

## Future Enhancements（可选）

- **Rate limiting**：Workers 内置 `request.cf` 信息，可做更精细的限频
- **Analytics dashboard**：加一个 `/api/admin/stats` 接口，列出所有文章的排名
- **评论系统**：在同一个 Worker + D1 上扩展，加 `comments` 表 + Turnstile 验证
- **缓存优化**：用 Workers KV 缓存热门文章的统计数据，减少 D1 读取
