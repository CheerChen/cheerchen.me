# AGENTS.md

## Workflow

All changes go through a pull request. Do not push directly to `main`.

- One PR per article (or per logical change). Draft PRs are welcome for work-in-progress.
- CI runs automatically on every PR: Hugo build, front matter consistency, image references, textlint (prh terminology). CI must pass before merge.
- Close the PR if you decide not to publish — no need to delete the branch.
- Branch protection on `main` enforces this: direct pushes are rejected, merges require a passing CI check.

## Blog Writing

When creating or editing blog posts:

1. Read `TAXONOMY.md` before choosing `categories` and `tags`.
2. Front matter must use the language-neutral slugs defined in `TAXONOMY.md` (e.g. `tags = ["architecture"]`), never the translated words.
3. Use the exact same slugs in `index.zh.md`, `index.ja.md` and `index.en.md`.
4. **Never rename a slug** — it changes the public URL and creates 404s. To change wording, edit the `title` in `content/tags/<slug>/_index.<lang>.md` (or `content/categories/...`) instead.
5. When a slug is used in a language for the first time, create `content/tags/<slug>/_index.<lang>.md` with the title from `TAXONOMY.md`.
6. Add a new category only when the post clearly does not fit the existing taxonomy.
7. Tags can be more flexible, but reuse existing slugs/tags when possible.

## Languages

The site is trilingual: `zh` (default, served at the site root), `ja` (`/ja/`), `en` (`/en/`).

- A post exists in a language only if `index.<lang>.md` exists in its bundle. There is no fallback: a missing `index.en.md` simply means no English page.
- Nav icons are conditional on content existing for the active language. The About icon needs at least one page resource under `content/about/` for that language, and the Search icon needs `content/search/_index.<lang>.md`. If an icon is missing in one language, look for a missing stub file before suspecting the template.
- Per-language settings belong under `[languages.<lang>.params]`, not the shared `[params]` block. `jsDateFormat` is the cautionary example: as a global value it forced `yyyy年MM月dd日` onto English pages.
- UI strings live in `i18n/<lang>.toml`; the theme supplies English defaults in `themes/dream/i18n/en.toml`, so only project-specific keys need to be added.
- When a string concatenates with a value, use an i18n placeholder rather than string joining, because word order differs. See `shareOn`: `"分享到 {{ .platform }}"` vs `"{{ .platform }} でシェア"`.
- English strings that get appended to a number need their own leading space (`views = " views"`), following the theme's `minuteRead = " minute read"`.

## Images and Video

Always reference page-bundle media through shortcodes:

```
{{< figure src="screenshot.png" title="optional caption" >}}
{{< vfigure src="demo.mp4" title="optional caption" >}}
```

Never write raw `<figure>`, `<img>` or `<video>` tags, and never use Markdown `![](file.png)`, for bundle-relative files. Hugo publishes each page-bundle file **once**, under the default language path, so a bare relative `src` resolves to `/en/posts/<slug>/foo.png` and 404s. Only the shortcodes resolve through `.Resources`, which yields the single real URL and therefore works in every language.

`title` is the project's caption convention (~250 usages); `alt`/`caption` are not used. An absolute `/images/...` path is the one case where a raw tag is fine.

## Styling

The theme ships a **prebuilt** Tailwind stylesheet at `themes/dream/assets/css/output.css`. Any utility class not already present in that file does nothing at all — edited classes will appear in the HTML and have zero visual effect, which looks exactly like a caching problem. Put new styling in `static/custom.css` with project-specific class names instead.

## Verification

CI runs these checks automatically on every PR:

```bash
hugo --gc --minify --destination /tmp/check          # must report no ERROR/WARN
python3 scripts/check-content.py                    # front matter consistency + image references
npx textlint --config tools/textlint/.textlintrc.json "content/posts/**/*.md"  # prh terminology
```

Run the same commands locally before pushing if you want early feedback.

After adding or translating posts, also confirm:

- Every referenced media file exists in the build output (catches the relative-path trap above).
- `tags` / `categories` are byte-identical to the other languages' files.
- Every translated slug used has a matching `content/{tags,categories}/<slug>/_index.<lang>.md`.
- Shortcode and code-fence counts match the source language.
