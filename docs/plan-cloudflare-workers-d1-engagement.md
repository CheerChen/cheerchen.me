# Hugo Blog Engagement: Views & Likes via Cloudflare Workers + D1

## 先质疑，再执行

原方案能表达大方向，但直接开工会踩几个确定会发生的问题。

### 1. 现在的 `slug` 方案在这个仓库里是错的

原文用 `{{ .File.ContentBaseName }}` 当 slug。

这在当前仓库里会失效，因为文章是这样的结构：

```text
content/posts/<post>/index.zh.md
content/posts/<post>/index.ja.md
```

这意味着中日文页面的 `ContentBaseName` 都是 `index`，最终所有文章都会撞到同一个 key。

**结论**：必须改为“跨语言稳定的 page key”，不能用文件名。

### 2. 必须先定义“统计单位”是什么

在多语言博客里，浏览量/点赞到底是：

- 按页面统计：中文和日文分开
- 按文章统计：同一篇文章的多语言版本共用一组数据

对当前站点，我建议默认按“文章”统计，也就是：

- `/posts/foo/` 和 `/ja/posts/foo/` 共享同一个 `page_key`
- 页面展示不同语言，但统计口径合并

原因很简单：当前内容组织本身就是一个 bundle 对应一篇文章的多个语言版本。

### 3. “同 IP 去重”不够好，只能算软限制

原方案里用 `CF-Connecting-IP` 做点赞去重。问题是：

- 同公司/家庭网络会共用出口 IP，容易误伤
- 移动网络和 IPv6 切换会让同一用户重复计数
- 纯 IP 方案容易被误解为“足够防刷”，其实不是

**结论**：可以做轻量防刷，但不要把它定义成强认证系统。

### 4. “浏览量+1”要先定义是 page load 还是近似 unique view

如果每次打开页面都直接 `+1`：

- F5、切换标签页、爬虫、预取都可能放大数据
- 这个数字会更像“请求次数”而不是“人看过多少次”

对个人博客，更合理的是：

- 把 `view` 定义为“同一访客在 12 小时或 24 小时窗口内只记一次”

### 5. 历史浏览量和历史点赞不是一回事

- **历史浏览量**：大概率可以从现有 Google Analytics 导出
- **历史点赞**：如果此前没有独立点赞系统，基本无法准确还原

**结论**：必须把这两个问题拆开处理，不能都写成“后面导入”。

## 修正后的目标

为 Hugo 博客实现一套轻量、低成本、可维护的互动统计：

- 浏览量：近似 unique views，按文章聚合，中日文共享
- 点赞：轻量去重，允许软防刷，不追求强实名
- 历史数据：优先回填已有浏览量，点赞默认从 0 开始

## 推荐方案

### 页面标识策略

定义一个稳定的 `page_key`：

- 优先使用 front matter 中显式声明的 `engagement_id`
- 没有声明时，默认使用文章 bundle 目录，例如 `posts/introducing-pr-dump-for-ai-code-review`

这比 URL 更稳，也比文件名安全。

Hugo 侧建议：

```go-html-template
{{ $pageKey := or .Params.engagement_id (replaceRE "/$" "" .File.Dir) }}
```

对于当前仓库，这样的结果会是：

- `content/posts/introducing-pr-dump-for-ai-code-review/index.zh.md`
- `content/posts/introducing-pr-dump-for-ai-code-review/index.ja.md`

两者都映射成：

```text
posts/introducing-pr-dump-for-ai-code-review
```

### 访客标识策略

不要只依赖 IP。

推荐混合方案：

1. 前端首次访问时生成随机 `visitor_id`，存到 `localStorage`
2. 请求时把 `visitor_id` 发给 Worker
3. Worker 用 secret 做 HMAC / SHA-256，生成 `visitor_hash`
4. 如果前端没有 `visitor_id`，再回退到 `IP 前缀 + UA` 的哈希

这样做的好处：

- 不直接存原始 IP
- 比纯 IP 去重更稳定
- 仍然保持实现简单

但要明确：

- 清理浏览器存储后，用户仍可重复点赞
- 所以这只是“软防刷”，不是投票系统

如果后续真被刷，再加 Cloudflare Turnstile。

## 数据模型

原方案把 views 和 likes 分开放是对的，但还不够。

推荐改成下面四张表：

```sql
CREATE TABLE page_counters (
  page_key TEXT PRIMARY KEY,
  canonical_path TEXT NOT NULL,
  views_seed_total INTEGER NOT NULL DEFAULT 0,
  views_live_total INTEGER NOT NULL DEFAULT 0,
  likes_seed_total INTEGER NOT NULL DEFAULT 0,
  likes_live_total INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE page_view_visitors (
  page_key TEXT NOT NULL,
  visitor_hash TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  PRIMARY KEY (page_key, visitor_hash)
);

CREATE TABLE page_likes (
  page_key TEXT NOT NULL,
  visitor_hash TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (page_key, visitor_hash)
);

CREATE TABLE page_aliases (
  alias_path TEXT PRIMARY KEY,
  page_key TEXT NOT NULL
);

CREATE INDEX idx_page_likes_page_key ON page_likes(page_key);
CREATE INDEX idx_page_view_visitors_page_key ON page_view_visitors(page_key);
CREATE INDEX idx_page_aliases_page_key ON page_aliases(page_key);
```

其中：

- `page_counters` 存总计数和历史回填值
- `page_view_visitors` 负责 view 去重窗口
- `page_likes` 负责点赞去重
- `page_aliases` 负责把多语言路径、历史旧路径映射回同一个 `page_key`

`page_aliases` 不是第一天就必须把所有玩法做满，但它能解决两个后续很常见的问题：

- `/posts/foo/` 和 `/ja/posts/foo/` 需要归到同一个 key
- 将来文章目录改名后，不想把旧数据丢掉

### 为什么要有 `*_seed_total`

这是为了让历史数据导入可重复执行。

- `views_seed_total`：历史回填值
- `views_live_total`：系统上线后的实时增量
- 页面展示时返回两者之和

这样你后面重新导一次 GA 数据，不会把线上增量冲掉。

`likes_seed_total` 也是同理，但默认大概率一直是 0。

## API 设计

原方案是：

- `GET /api/stats`
- `POST /api/view`
- `POST /api/like`

这能跑，但页面首屏至少两次请求，没有必要。

推荐改成：

| Method | Path | 用途 |
|--------|------|------|
| POST | `/api/engagement/view` | 记录 view，并返回最新 `views/likes/liked` |
| POST | `/api/engagement/like` | 点赞，并返回最新 `likes` |
| GET | `/api/engagement/stats?pageKey=...` | 仅用于调试/后台/回归检查 |

### `POST /api/engagement/view`

请求体：

```json
{
  "pageKey": "posts/introducing-pr-dump-for-ai-code-review",
  "canonicalPath": "/posts/introducing-pr-dump-for-ai-code-review/",
  "lang": "zh"
}
```

服务端逻辑：

1. 校验 `pageKey`
2. 生成 `visitor_hash`
3. 确保 `page_counters` 行存在
4. 查询 `page_view_visitors`
5. 如果上次访问早于 12 小时或 24 小时窗口，则：
   - 更新 `last_seen_at`
   - `views_live_total = views_live_total + 1`
6. 查询当前是否已点赞
7. 返回：

```json
{
  "views": 1234,
  "likes": 12,
  "liked": false
}
```

### `POST /api/engagement/like`

请求体：

```json
{
  "pageKey": "posts/introducing-pr-dump-for-ai-code-review"
}
```

服务端逻辑：

1. 生成 `visitor_hash`
2. `INSERT OR IGNORE` 到 `page_likes`
3. 如果本次是新点赞，则 `likes_live_total + 1`
4. 返回最新点赞数和 `liked: true`

### `GET /api/engagement/stats`

这个接口不要作为前端常规加载路径，只保留给：

- 手工检查
- 数据核对
- 后台扩展

## Hugo 集成方式

### 模板插入点

当前站点的文章模板在：

- `layouts/_default/single.html`

因此应该在文章内容之后、上一篇下一篇之前插入互动模块。

### partial 示例

建议新建：

- `layouts/partials/engagement.html`

示例：

```go-html-template
{{ if eq .Type "posts" }}
  {{ $pageKey := or .Params.engagement_id (replaceRE "/$" "" .File.Dir) }}
  <section
    id="post-engagement"
    class="post-engagement"
    data-page-key="{{ $pageKey }}"
    data-page-path="{{ .RelPermalink }}"
    data-lang="{{ .Lang }}"
    data-api-base="{{ site.Params.engagementApiBase }}"
  >
    <span class="view-count">Views: <span data-role="views">-</span></span>
    <button type="button" data-role="like-button">
      Like <span data-role="likes">-</span>
    </button>
  </section>
{{ end }}
```

### 前端 JS

建议新建：

- `static/js/engagement.js`

逻辑：

1. 页面加载后读取 `data-page-key`
2. 生成或读取 `localStorage.visitor_id`
3. `POST /api/engagement/view`
4. 用返回值直接渲染 `views/likes/liked`
5. 点赞按钮点击后调用 `/api/engagement/like`

这样首屏只需要一次主要接口调用。

## 历史数据怎么获得

这是这份方案里最重要、也是最容易被忽略的部分。

### 历史浏览量：优先从 GA4 导出

当前站点已经启用了 Google Analytics，因此历史浏览量的首选来源是 **GA4**。

可行路径有两条：

#### 方案 A：一次性导出，最省事

在 GA4 后台导出：

- 维度：`Page path`
- 指标：`Views`
- 时间范围：站点上线至今

导出 CSV 后，本地做一次转换：

```text
/posts/foo/      -> posts/foo
/ja/posts/foo/   -> posts/foo
```

然后汇总成每个 `page_key` 的 `views_seed_total`。

优点：

- 一次性工作量最小
- 不需要先处理 Google API 权限

缺点：

- 不是自动化流程

#### 方案 B：用 Google Analytics Data API，适合可重复导入

通过 `runReport` 拉取：

- dimension: `pagePath`
- metric: `views`

再按当前仓库的文章目录规则做映射和聚合。

适合在以下场景使用：

- 初次回填
- 以后定期重跑校验
- 想把导入流程脚本化

### 历史浏览量映射规则

建议明确写死映射规则，不要运行时猜。

规则示例：

```text
/posts/<slug>/     -> posts/<slug>
/ja/posts/<slug>/  -> posts/<slug>
```

需要忽略的路径：

- 首页 `/`
- 标签页
- 搜索页
- 404
- 非文章页面

### 历史浏览量导入流程

推荐流程：

1. 从仓库生成“当前文章清单”
2. 从 GA 导出按 `pagePath` 聚合的数据
3. 先用仓库文章清单或 `page_aliases` 把路径归一化成 `page_key`
4. 聚合成 `page_key -> views_seed_total`
5. 生成 SQL：

```sql
INSERT INTO page_counters (page_key, canonical_path, views_seed_total)
VALUES ('posts/foo', '/posts/foo/', 1234)
ON CONFLICT(page_key) DO UPDATE SET
  canonical_path = excluded.canonical_path,
  views_seed_total = excluded.views_seed_total,
  updated_at = CURRENT_TIMESTAMP;
```

6. 用 `wrangler d1 execute --file ... --remote` 导入
7. 随机抽查几篇文章与 GA 后台是否一致

### 历史点赞：大概率拿不到

这里必须说清楚：

- Google Analytics 只能给你页面浏览数据
- 它不能帮你还原“谁点过赞”
- 如果你以前没有单独的点赞系统、数据库或日志，历史点赞无法准确恢复

现实可选项只有三个：

1. **点赞从 0 开始**
2. 如果以前有别的点赞源，人工导入为 `likes_seed_total`
3. 明确告诉自己和读者：点赞是新功能，上线后开始累计

我建议直接选第 1 或第 3。

## CORS 和部署建议

### 域名建议

推荐把 Worker 绑定到单独域名，例如：

```text
https://api.cheerchen.me
```

然后只允许：

```text
https://cheerchen.me
```

必要时再补：

```text
https://www.cheerchen.me
```

不要用 `*`。

### D1 与免费额度判断

对个人博客，这套设计通常足够轻。

但要注意两点：

- D1 是单库串行写，不适合高并发重写场景
- 个人博客的 views/likes 很适合 D1，但不要把它当通用 analytics 平台

如果未来流量明显上来，再考虑：

- 热门数据做缓存
- 批量写入
- 或改成专门 analytics 服务

## 分阶段执行

### Phase 0: 先定三件事

在动手前先确认：

1. 统计口径按“文章聚合”，不是按语言页面分开
2. 浏览量按“12 小时或 24 小时去重 view”
3. 历史点赞不追溯，默认从 0 开始

这三件事不定，后面代码都会反复返工。

### Phase 1: 建 D1 schema 和 Worker

- 建表
- 实现 `/api/engagement/view`
- 实现 `/api/engagement/like`
- 实现严格 CORS
- 配置 `VISITOR_HASH_SALT`

### Phase 2: Hugo 前端接入

- 新增 `layouts/partials/engagement.html`
- 修改 `layouts/_default/single.html`
- 新增 `static/js/engagement.js`
- 只在 `posts` 页面渲染

### Phase 3: 历史浏览量回填

- 从 GA 导出 `pagePath + views`
- 归一化到 `page_key`
- 导入 `views_seed_total`
- 抽样核对

### Phase 4: 上线后观察

- 看 D1 读写量
- 看是否有明显刷赞
- 看是否存在文章 key 错配

## 不建议的做法

- 不要用 `.File.ContentBaseName` 做文章标识
- 不要把“同 IP 去重”写成强防刷能力
- 不要先写前端，再回头补历史数据模型
- 不要把历史点赞恢复当作默认可完成事项

## 最终建议

如果要开始执行，这份方案应以以下决策为准：

- `page_key` 按文章 bundle 目录生成，必要时允许 front matter 显式覆盖
- 页面首屏调用一个 `view` 接口，同时返回当前统计
- 历史浏览量从 GA4 导入到 `views_seed_total`
- 历史点赞默认放弃回填

这套方案比原版本多了一点设计，但能避免后面最麻烦的三类返工：

- 多语言 key 冲突
- 历史数据导入后覆盖线上数据
- 上线后才发现“同 IP 点赞”统计口径不成立

## 参考

- Cloudflare D1 pricing: https://developers.cloudflare.com/d1/platform/pricing/
- Cloudflare D1 limits: https://developers.cloudflare.com/d1/platform/limits/
- Cloudflare D1 import/export: https://developers.cloudflare.com/d1/best-practices/import-export-data/
- Google Analytics Data API `runReport`: https://developers.google.com/analytics/devguides/reporting/data/v1/basics
- GA Data API schema (`pagePath`): https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema
