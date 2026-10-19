# slides

Redraws talk slides as 1200×675 SVG in English, from data instead of hand-placed coordinates. Also holds the checker every slide and diagram goes through.

- `slides.py`: the template (`Slide`: section tag, title, wrapping bullets), widgets (`table`, `person`, `block_arrow`, `step_flow`), and `check()`.
- `decks/<post>.py`: one function per slide. Each returns the output filename and the SVG.
- `fit_marks.py`: sizes highlighter bands in hand-drawn slides to the text they mark.

```bash
python3 tools/slides/decks/switch2.py --check              # every slide in the deck
python3 tools/slides/decks/switch2.py cost-design --check  # one slide
python3 tools/slides/slides.py <svg>... --png <dir>        # check any SVG, and screenshot it for review
```

`check()` renders in headless Chrome (macOS app path in `CHROME`) and fails if any text leaves the canvas or two text boxes overlap. Texts in different `data-frame` groups (animation frames) are not compared. It cannot see text over a shape or an arrow that misses its box, so always look at the screenshot too.

## Rules

- Edit the deck and regenerate. Never hand-edit a generated SVG.
- In `<style>`, set the default text colour as `text:where(:not([fill]))`. A plain `text{fill:...}` rule overrides every `fill` attribute, and `text:not([fill])` outranks single-class rules such as `.note`.
- AWS architecture diagrams belong in `tools/archdiagram/`, which also owns the standard for redrawing a talk (see its README).

## Hand-drawn slides

Some posts (for example the TBS Kustamie one) carry slides drawn by hand in the talk's own style. Keep that style and fix their bugs rather than redrawing them with the template.

- **One line, one `<text>`.** Put coloured, bold or underlined words in `<tspan>`s inside it (`text-decoration="underline"` works on a tspan). Separate `<text>` runs at guessed x positions are what made words overlap or leave gaps.
- **Highlighter bands**: write `<rect data-mark="ID" fill="#fff06a"/>` before the text, give the marked tspan `id="ID"`, and run `python3 tools/slides/fit_marks.py <svg>`. Run it again whenever the text changes.
- **Restore what the photo shows**, such as lines, footnotes and table captions. Read the photo, not the earlier redraw.
