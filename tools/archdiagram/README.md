# archdiagram

Generates AWS architecture diagrams as SVG, laid out by hand with the official AWS icons. Use it in place of auto-laid-out Mermaid when the original slide's spatial layout matters.

- `archdiagram.py`: icons, AWS group boxes (AWS Cloud, Region), role bands and labels, orthogonal connectors.
- `aws-icons/`: the vendored official icons, see `NOTICE.md`.
- `figures/<post>_<name>.py`: one script per diagram. Each writes its SVG straight into the post bundle.

```bash
python3 tools/archdiagram/figures/switch2_system_architecture.py
```

Rules:

- Text is English in every language version, so all of them reference the same file.
- Edit the script and regenerate. Never hand-edit a generated SVG.
- Keep the canvas 1200px wide so 13px labels stay readable at the article width.
- Check the render with headless Chrome before committing (command in `tools/pictogram/README.md`).
