# slides

Redraws talk slides as 1200×675 SVG in English, from data instead of hand-placed coordinates.

- `slides.py`: the template (`Slide`: section tag, title, wrapping bullets), widgets (`table`, `person`, `block_arrow`), and `check()`.
- `decks/<post>.py`: one function per slide. Each returns the output filename and the SVG.

```bash
python3 tools/slides/decks/switch2.py --check              # every slide in the deck
python3 tools/slides/decks/switch2.py cost-design --check  # one slide
```

`--check` renders each slide in headless Chrome (macOS app path in `CHROME`) and fails if any text leaves the canvas or two text boxes overlap. Run it before committing; the width estimate used for wrapping is only an approximation.

Rules:

- Edit the deck and regenerate. Never hand-edit a generated SVG.
- In `<style>`, set the default text colour as `text:where(:not([fill]))`. A plain `text{fill:...}` rule overrides every `fill` attribute, and `text:not([fill])` outranks single-class rules such as `.note`.
- AWS architecture diagrams belong in `tools/archdiagram/`, not here.
