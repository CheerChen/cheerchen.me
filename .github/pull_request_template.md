## Summary

<!-- What changed and why — 1-3 sentences -->

## Type

- [ ] New post
- [ ] Translation
- [ ] Code / config / layout change

## Self-check

- [ ] `hugo --gc --minify --destination /tmp/check` — no ERROR/WARN
- [ ] `python3 scripts/check-content.py` — front matter consistent, image refs valid
- [ ] `tags` / `categories` are byte-identical across all language versions
- [ ] Images use `{{< figure >}}` / `{{< vfigure >}}` shortcodes (no bare `![]()` for bundle files)
- [ ] New tags/categories are registered in `TAXONOMY.md` with matching `_index.<lang>.md`
- [ ] Shortcode and code-fence counts match across translations
