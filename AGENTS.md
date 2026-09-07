# AGENTS.md

## Blog Writing

When creating or editing blog posts:

1. Read `TAXONOMY.md` before choosing `categories` and `tags`.
2. Front matter must use the language-neutral slugs defined in `TAXONOMY.md` (e.g. `tags = ["architecture"]`), never the translated words.
3. Use the exact same slugs in `index.zh.md` and `index.ja.md`.
4. **Never rename a slug** — it changes the public URL and creates 404s. To change wording, edit the `title` in `content/tags/<slug>/_index.<lang>.md` (or `content/categories/...`) instead.
5. When a slug is used in a language for the first time, create `content/tags/<slug>/_index.<lang>.md` with the title from `TAXONOMY.md`.
6. Add a new category only when the post clearly does not fit the existing taxonomy.
7. Tags can be more flexible, but reuse existing slugs/tags when possible.
