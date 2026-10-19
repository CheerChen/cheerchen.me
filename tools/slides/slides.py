"""A slide template for redrawing talk slides as SVG, plus an overflow check.

Text is measured with a per-character width estimate so titles shrink and
bullets wrap before they leave the canvas. `check()` then measures the real
render in headless Chrome, so the estimate never has to be trusted blindly.
"""
import html
import json
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

W, H = 1200, 675
LEFT, RIGHT = 70, 1130
INK = "#232f3e"
DIM = "#5f6b7a"
# Switch palette: charcoal body, Joy-Con red and blue as the two accents.
RED = "#e8412c"          # bullets, emphasis, writes
BLUE = "#139ad6"         # secondary accent, reads
ACCENT = RED
HEADER = "#3a3f46"       # table header
ROW_A, ROW_B = "#f3f4f6", "#e9ebee"
BG = "#ffffff"           # the slide itself
DESK = "#e4e7eb"         # canvas around the slide frame
FONT = "-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"


def measure(text, size, bold=False):
    """Approximate rendered width in px for the system sans font."""
    w = 0.0
    for ch in text:
        if ord(ch) > 0x2E80:
            w += 1.0
        elif ch == " ":
            w += 0.28
        elif ch in "il.,:;|!'":
            w += 0.27
        elif ch.isupper() or ch in "mwMW":
            w += 0.68
        else:
            w += 0.55
    return w * size * (1.06 if bold else 1.0)


def wrap(text, size, max_w, bold=False):
    lines, cur = [], ""
    for word in text.split(" "):
        trial = f"{cur} {word}".strip()
        if cur and measure(trial, size, bold) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


def esc(text):
    return html.escape(text, quote=False)


class Slide:
    def __init__(self, tag, title, page=None, heading=True):
        """heading=False leaves tag and title to the caller, e.g. one per animation frame."""
        self.page = page
        self.parts = []
        self.overlay = []   # drawn after the page badge, e.g. per-frame page numbers
        self.title = title
        if heading:
            self.parts.append(self.heading(tag, title))

    @staticmethod
    def heading(tag, title):
        """The section tag (top right, underlined) and the title, shrunk to fit."""
        size = 44
        while measure(title, size, True) > RIGHT - LEFT and size > 30:
            size -= 2
        return (f'<text x="{RIGHT}" y="62" font-size="20" fill="{DIM}" text-anchor="end" '
                f'text-decoration="underline">{esc(tag)}</text>\n'
                f'<text x="{LEFT}" y="138" font-size="{size}" font-weight="700">{esc(title)}</text>')

    def add(self, fragment):
        self.parts.append(fragment)

    def subtitle(self, text, y=184):
        """A one-line lead under the title."""
        size = 22
        while measure(text, size) > RIGHT - LEFT and size > 16:
            size -= 1
        self.parts.append(f'<text x="{LEFT}" y="{y}" font-size="{size}" fill="{DIM}">{esc(text)}</text>')

    def bullet(self, text, y, level=1, max_x=RIGHT):
        """A bullet with wrapping; returns the y just below it."""
        size = 26 if level == 1 else 22
        x = LEFT + (12 if level == 1 else 52)
        tri = 14 if level == 1 else 11
        lines = wrap(text, size, max_x - x - 28)
        self.parts.append(f'<polygon points="{x},{y - size * 0.62} {x + tri},{y - size * 0.62 + tri * 0.62} '
                          f'{x},{y - size * 0.62 + tri * 1.24}" fill="{ACCENT}"/>')
        for i, line in enumerate(lines):
            fill = "" if level == 1 else f' fill="{DIM}"'
            self.parts.append(f'<text x="{x + 28}" y="{y + i * size * 1.35:.0f}" font-size="{size}"{fill}>{esc(line)}</text>')
        return y + len(lines) * size * 1.35 + (14 if level == 1 else 8)

    def svg(self, desc):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">\n'
                f'  <title id="title">{esc(self.title)}</title>\n  <desc id="desc">{esc(desc)}</desc>\n'
                f'  <style>text{{font-family:{FONT}}}text:where(:not([fill])){{fill:{INK}}}</style>\n'
                f'  <rect width="{W}" height="{H}" fill="{DESK}"/>\n'
                f'  <rect x="16" y="20" width="{W - 32}" height="{H - 32}" rx="14" fill="#c9ced4"/>\n'
                f'  <rect x="14" y="14" width="{W - 28}" height="{H - 30}" rx="14" fill="{BG}" stroke="#cfd4da" stroke-width="1.5"/>\n'
                + "\n".join(self.parts) + "\n" + switch_badge(W - 76, H - 56, self.page) + "\n"
                + "".join(o + "\n" for o in self.overlay) + "</svg>\n")


# ---- widgets ----

def table(x, y, col_w, header, rows, row_h=52, size=20, label_col=False):
    """A slide table: charcoal header, alternating soft rows, centred cells.

    A cell may be a list of lines; its row grows to fit them.
    label_col=True makes the first column bold row labels on a darker band.
    """
    line_h = size * 1.3
    cells = [[c if isinstance(c, list) else [str(c)] for c in row] for row in rows]
    heights = [max(row_h, max(len(c) for c in row) * line_h + 22) for row in cells]
    total, bottom = sum(col_w), y + row_h + sum(heights)
    s = f'<rect x="{x}" y="{y}" width="{total}" height="{row_h}" fill="{HEADER}"/>'
    top = y + row_h
    for r, h in enumerate(heights):
        s += f'<rect x="{x}" y="{top:.0f}" width="{total}" height="{h:.0f}" fill="{ROW_A if r % 2 == 0 else ROW_B}"/>'
        top += h
    if label_col:
        s += f'<rect x="{x}" y="{y + row_h}" width="{col_w[0]}" height="{bottom - y - row_h:.0f}" fill="{ROW_B}"/>'
    top = y + row_h
    for h in heights[:-1]:
        top += h
        s += f'<line x1="{x}" y1="{top:.0f}" x2="{x + total}" y2="{top:.0f}" stroke="#ffffff" stroke-width="3"/>'
    cx = x
    for c, w in enumerate(col_w):
        mid = cx + w / 2
        s += f'<text x="{mid}" y="{y + row_h / 2 + size * 0.36:.0f}" font-size="{size}" font-weight="700" fill="#ffffff" text-anchor="middle">{esc(header[c])}</text>'
        top = y + row_h
        for row, h in zip(cells, heights):
            lines = row[c]
            first = top + h / 2 - (len(lines) - 1) * line_h / 2 + size * 0.36
            bold = ' font-weight="700"' if label_col and c == 0 else ""
            for i, line in enumerate(lines):
                s += f'<text x="{mid}" y="{first + i * line_h:.0f}" font-size="{size}"{bold} text-anchor="middle">{esc(line)}</text>'
            top += h
        if c:
            s += f'<line x1="{cx}" y1="{y}" x2="{cx}" y2="{bottom:.0f}" stroke="#ffffff" stroke-width="3"/>'
        cx += w
    return s


def step_flow(x, y, width, steps, h=190, gap=44, size=20, highlight=None):
    """Numbered step cards in a row joined by chevrons; `highlight` is the index of a card to mark in red."""
    n = len(steps)
    w = (width - gap * (n - 1)) / n
    s = ""
    for i, text in enumerate(steps):
        cx = x + i * (w + gap)
        hl = i == highlight
        stroke = RED if hl else "#cfd4da"
        s += f'<rect x="{cx:.0f}" y="{y}" width="{w:.0f}" height="{h}" rx="12" fill="{ROW_A}" stroke="{stroke}" stroke-width="{2.5 if hl else 1.5}"/>'
        s += (f'<circle cx="{cx + w / 2:.0f}" cy="{y + 40}" r="20" fill="{RED if hl else HEADER}"/>'
              f'<text x="{cx + w / 2:.0f}" y="{y + 47}" font-size="20" font-weight="700" fill="#ffffff" text-anchor="middle">{i + 1}</text>')
        lines = wrap(text, size, w - 28)
        first = y + 82 + (h - 82 - len(lines) * size * 1.3) / 2 + size * 0.8
        for j, line in enumerate(lines):
            s += f'<text x="{cx + w / 2:.0f}" y="{first + j * size * 1.3:.0f}" font-size="{size}" text-anchor="middle">{esc(line)}</text>'
        if i < n - 1:
            ax = cx + w + gap / 2
            s += (f'<path d="M{ax - 7:.0f},{y + h / 2 - 12} L{ax + 6:.0f},{y + h / 2} L{ax - 7:.0f},{y + h / 2 + 12}" fill="none" '
                  f'stroke="{DIM}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>')
    return s


def switch_badge(cx, cy, page=None, scale=1.0, mono=False):
    """The Switch glyph with red / blue Joy-Cons; the page number sits on its screen.

    mono=True draws black Joy-Cons, for a Switch inside slide content, so it never reads as the page badge.
    """
    k = scale
    num = (f'<text x="0" y="6" font-size="17" font-weight="700" text-anchor="middle">{page}</text>'
           if page is not None else "")
    return (f'<g transform="translate({cx},{cy}) scale({k})">'
            f'<rect x="-26" y="-18" width="52" height="36" rx="3" fill="#ffffff" stroke="{INK}" stroke-width="2.5"/>' + num +
            f'<rect x="-40" y="-20" width="14" height="40" rx="7" fill="{INK if mono else BLUE}" stroke="{INK}" stroke-width="2"/>'
            f'<rect x="26" y="-20" width="14" height="40" rx="7" fill="{INK if mono else RED}" stroke="{INK}" stroke-width="2"/>'
            f'<circle cx="-33" cy="-8" r="2.5" fill="#ffffff"/><circle cx="33" cy="6" r="2.5" fill="#ffffff"/></g>')


def person(cx, cy, scale=1.0, color="#8a9199"):
    """The generic user silhouette: head over rounded shoulders."""
    r = 30 * scale
    return (f'<circle cx="{cx}" cy="{cy - 34 * scale}" r="{r}" fill="{color}"/>'
            f'<path d="M{cx - 62 * scale},{cy + 70 * scale} L{cx - 62 * scale},{cy + 34 * scale} '
            f'Q{cx - 62 * scale},{cy + 4 * scale} {cx - 30 * scale},{cy + 4 * scale} L{cx + 30 * scale},{cy + 4 * scale} '
            f'Q{cx + 62 * scale},{cy + 4 * scale} {cx + 62 * scale},{cy + 34 * scale} L{cx + 62 * scale},{cy + 70 * scale} z" fill="{color}"/>')


def block_arrow(x1, x2, y, color, outline=None, thick=14):
    """A flat horizontal block arrow from x1 to x2 (either direction)."""
    d = 1 if x2 > x1 else -1
    head = 26
    body_end = x2 - d * head
    pts = [(x1, y - thick / 2), (body_end, y - thick / 2), (body_end, y - thick), (x2, y),
           (body_end, y + thick), (body_end, y + thick / 2), (x1, y + thick / 2)]
    p = " ".join(f"{px},{py}" for px, py in pts)
    stroke = f' stroke="{outline}" stroke-width="2"' if outline else ""
    return f'<polygon points="{p}" fill="{color}"{stroke} stroke-linejoin="round"/>'


# ---- output and verification ----

def write(rel_path, content):
    (REPO / rel_path).write_text(content)
    print(f"wrote {rel_path}")


_PROBE = """<!doctype html><meta charset="utf-8"><body style="margin:0">%s
<pre id="out"></pre><script>
const svg = document.querySelector('svg'), vb = svg.viewBox.baseVal, out = [];
// rendered boxes (transforms applied), in viewBox units
const o = svg.getBoundingClientRect(), k = vb.width / o.width;
// animation frames share the canvas: texts in different data-frame groups never count as overlapping
const texts = [...svg.querySelectorAll('text')].filter(t => t.textContent.trim()).map(t => {
  const r = t.getBoundingClientRect(), fr = t.closest('[data-frame]');
  return {t: t.textContent, f: fr ? fr.dataset.frame : null,
          b: {x: (r.left - o.left) * k, y: (r.top - o.top) * k, width: r.width * k, height: r.height * k}};
});
for (const {t, b} of texts) {
  if (b.x < 0 || b.y < 0 || b.x + b.width > vb.width || b.y + b.height > vb.height)
    out.push('outside canvas: ' + t);
}
for (let i = 0; i < texts.length; i++) for (let j = i + 1; j < texts.length; j++) {
  if (texts[i].f && texts[j].f && texts[i].f !== texts[j].f) continue;
  const a = texts[i].b, c = texts[j].b;
  const ox = Math.min(a.x + a.width, c.x + c.width) - Math.max(a.x, c.x);
  const oy = Math.min(a.y + a.height, c.y + c.height) - Math.max(a.y, c.y);
  if (ox > 2 && oy > 2) out.push('overlap: "' + texts[i].t + '" / "' + texts[j].t + '"');
}
document.getElementById('out').textContent = JSON.stringify(out);
</script>"""


def check(rel_path):
    """Render in headless Chrome and return a list of text problems (empty means clean)."""
    content = (REPO / rel_path).read_text()
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(_PROBE % content)
    dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--dump-dom", f"file://{f.name}"],
                         capture_output=True, text=True, timeout=60).stdout
    Path(f.name).unlink()
    raw = dom.split('<pre id="out">', 1)[1].split("</pre>", 1)[0]
    return json.loads(html.unescape(raw))


def render(rel_path, out_png):
    """Screenshot an SVG at its own size in headless Chrome, for reviewing what check() cannot see."""
    content = (REPO / rel_path).read_text()
    w, h = (int(float(v)) for v in content.split('viewBox="', 1)[1].split('"', 1)[0].split()[2:4])
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={w},{h}",
                    f"--screenshot={out_png}", f"file://{(REPO / rel_path).resolve()}"],
                   capture_output=True, timeout=60)


if __name__ == "__main__":
    # python3 tools/slides/slides.py <svg>... [--png <dir>]: check any slide or diagram, optionally screenshot it
    import sys
    args, png_dir = sys.argv[1:], None
    if "--png" in args:
        i = args.index("--png")
        png_dir, args = Path(args[i + 1]), args[:i] + args[i + 2:]
        png_dir.mkdir(parents=True, exist_ok=True)
    failed = False
    for p in args:
        problems = check(p)
        print(f"{p}: {'ok' if not problems else ''}")
        for q in problems:
            print(f"  {q}")
        failed |= bool(problems)
        if png_dir:
            render(p, png_dir / (Path(p).stem + ".png"))
    sys.exit(1 if failed else 0)
