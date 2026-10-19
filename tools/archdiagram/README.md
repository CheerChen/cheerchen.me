# archdiagram

Generates AWS architecture diagrams as SVG, laid out by hand with the official AWS icons. This README is the standard for every AWS architecture diagram in a post.

Reference posts: `switch-2-gamechat-backend-sfu-dynamodb-consistency` and `tbs-kustamie-aws-serverless-large-scale-live-streaming` (their `arch-*.svg`, scripts in `figures/`).

## Files

- `archdiagram.py`: the parts.
  - `icon()`: an official icon with its label.
  - `group()`: AWS group boxes (`cloud`, `region`, `vpc`, `account`).
  - `service_box()`: a dashed box for one service's insides, or a plain group with `key=None`.
  - `box()`: a labelled rectangle for things without an icon (a stage, an environment).
  - `band()` and `role()`: a soft band and a label naming a component's role.
  - `path()` and `line()`: orthogonal connectors.
  - `step()`, `callout()`, `tag()`, `note()`, `switch()`.
- `aws-icons/`: the vendored official icons, see `NOTICE.md`. Add an icon by copying its file from the same package and registering it in `ICONS`.
- `figures/<post>_<name>.py`: one script per figure. Each writes `content/posts/<slug>/arch-NN-<name>.svg`.

```bash
python3 tools/archdiagram/figures/tbs_architecture.py
python3 tools/slides/slides.py content/posts/<slug>/arch-*.svg --png <scratch-dir>   # check + screenshots
```

## When to use it

- Any figure that shows AWS architecture, including diagrams redrawn from a talk's slides: draw it here.
- Do not use Mermaid or other auto-layout tools. They scatter the layout, shrink labels at article width, and have no AWS icons.

## Redrawing from a talk

1. **Start from the photo of the slide**, not from memory or from an older Mermaid version. Keep the slide's spatial layout: what sits inside which group, left to right, top to bottom.
2. **Draw only what the slide shows.**
   - No nodes or labels the slide does not have. Earlier Mermaid versions invented "BFF", "hot reads" and samplers.
   - Check every arrow's direction and target against the photo.
   - Where the photo is unreadable (cut off, blocked by the audience), choose a neutral label and say so when handing the figure over.
3. **One figure per slide-plus-diagram pair.** When a post shows a slide and a diagram of the same thing, merge them into one diagram. Then decide each remaining text-only slide on its own:
   - Keep it.
   - Fold it into a neighbour.
   - Drop it. The prose must already say it.
4. **Highlights survive.** When a figure replaces a slide, the slide's yellow highlights become bold text in the matching sentence of every language version.
5. **Keep a slide whose value is its example**, such as a sample input and output. Fix its bugs instead of redrawing it, and drop any diagram that only repeats the prose.

## Style

- Canvas 1200 px wide, with 13 px labels. Size the height to the content.
- Text is English, so every language version references the same file.
- Groups follow AWS convention: AWS Cloud solid ink, Region dashed teal, VPC solid purple, Account solid pink.
- Name a component's role with a band and a `role()` label ("Group server", "SFU instance manager"); the icon keeps its service name.
- Mark a path or a selected item with `RED` (synchronous, chosen) or `GREEN` (asynchronous), and say what the colour means in a `tag()`.

## Charts

- **Real data**: use `{{< chart >}}`. It only draws horizontal bar charts.
- **Traced from a screenshot, or a concept illustration** (for example the AWS docs' concurrency timeline): draw a static SVG here.
  - Say on the figure which values are real and that the shapes are approximate.
  - Never give traced data an interactive chart; tooltips would present it as measurements.
- **A chart crammed beside a slide's bullets**: split it. The slide keeps its text, and the chart becomes its own full-width figure below the slide.

## Verify before committing

1. Regenerate with the figure script.
2. Run `tools/slides/slides.py` on the output. It fails if text leaves the canvas or two text boxes overlap.
3. **Look at the screenshot** (`--png`). The check cannot see text over a box, an arrow that misses its target, or a label crossing a group border.
4. `hugo server` writes into `public/`, and files deleted from the bundle stay there. Remove stale ones before judging a page, and restart `hugo server` if a page renders stale or garbled.
5. One commit per figure, so a figure can be reverted on its own.

## Pitfalls

- **Colour or font set as an attribute does nothing when a CSS rule targets the element.** A `.note` class rule beats `fill="..."`, and `text{font-family:...}` beats `font-family="..."`. Use an inline `style` (as `note()` and the monospace blocks do), and set default text colour as `text:where(:not([fill]))`.
- **`marker-end` marks only the last point of a `<path>`.** Give each arrow its own path.
- **Never hand-edit a generated SVG.** Edit the script and regenerate.
