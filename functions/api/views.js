// Per-post view counter, served by Cloudflare Pages Functions and backed by D1.
//
//   GET  /api/views?key=posts/<slug>   -> { key, views }   (read only)
//   POST /api/views  {"key": "posts/<slug>"} -> { key, views }   (increment, then read)
//
// The key is the post bundle directory, so every language version of a post
// (/posts/foo/, /ja/posts/foo/, /en/posts/foo/) shares one counter.
// Requires a D1 binding named VIEWS_DB; see db/views.sql for the schema.

const KEY_RE = /^posts\/[a-z0-9][a-z0-9-]{0,199}$/;

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}

function missingBinding() {
  return json({ error: "D1 binding VIEWS_DB is not configured" }, 500);
}

export async function onRequestGet({ request, env }) {
  if (!env.VIEWS_DB) return missingBinding();
  const key = new URL(request.url).searchParams.get("key") ?? "";
  if (!KEY_RE.test(key)) return json({ error: "invalid key" }, 400);

  const row = await env.VIEWS_DB.prepare("SELECT count FROM views WHERE key = ?1")
    .bind(key)
    .first();
  return json({ key, views: row ? row.count : 0 });
}

export async function onRequestPost({ request, env }) {
  if (!env.VIEWS_DB) return missingBinding();

  // Only count requests from pages on this site. Browsers always send Origin
  // on a POST fetch; this filters casual cross-site abuse, not a determined bot.
  const origin = request.headers.get("Origin");
  if (!origin || new URL(origin).host !== new URL(request.url).host) {
    return json({ error: "forbidden" }, 403);
  }

  let key;
  try {
    ({ key } = await request.json());
  } catch {
    return json({ error: "invalid body" }, 400);
  }
  if (typeof key !== "string" || !KEY_RE.test(key)) {
    return json({ error: "invalid key" }, 400);
  }

  // Single atomic upsert: no read-modify-write race between concurrent views.
  const row = await env.VIEWS_DB.prepare(
    `INSERT INTO views (key, count) VALUES (?1, 1)
     ON CONFLICT(key) DO UPDATE SET count = count + 1, updated_at = CURRENT_TIMESTAMP
     RETURNING count`,
  )
    .bind(key)
    .first();
  return json({ key, views: row.count });
}
