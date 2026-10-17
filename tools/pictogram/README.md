# pictogram

Generates post figures as SVG in one shared style: thick dark-green outline, flat green / yellow fills, round-headed figures, speech bubbles, signboards. Think of Japanese public-information signs.

- `pictogram.py`: palette, figure poses and props (`person`, `bubble`, `spiky`, `station`, `signboard`, `megaphone`, `arrow`, ...).
- `figures/<post>_<name>.py`: one script per figure. Each writes its SVG straight into the post bundle.

```bash
python3 tools/pictogram/figures/10x_what_vs_how.py           # one figure
for f in tools/pictogram/figures/*.py; do python3 "$f"; done  # all of them
```

Rules:

- Edit the script and regenerate. Never hand-edit a generated SVG.
- Text inside figures is English, whatever the post language, so every language version references the same file.
- Diagrams that are structure (trees, hierarchies) stay as diagrams in this palette. Use figures only when the point is a scene or behaviour.
- Check the render before committing. Headless Chrome gives the full canvas, while Quick Look crops to a square:
  `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --hide-scrollbars --window-size=1200,<height> --screenshot=out.png file://$PWD/<svg>`
