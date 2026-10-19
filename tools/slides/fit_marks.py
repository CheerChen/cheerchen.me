"""Fit highlighter bands to the text they mark, in hand-drawn slide SVGs.

A band is a rect with data-mark="ID"; ID names the tspan (or text) it sits behind:

    <rect data-mark="m1" fill="#fff06a"/>
    <text x="130" y="244">... <tspan id="m1" font-weight="700">リージョンタイプ</tspan> ...</text>

Headless Chrome measures where each marked element really renders, and the rect is moved and sized to
cover it. Run it again after editing the text.

python3 tools/slides/fit_marks.py <slide.svg> [...]
"""
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from slides import CHROME  # noqa: E402

PAD_X, PAD_Y = 4, 3

_PROBE = """<!doctype html><meta charset="utf-8"><body style="margin:0">%s<pre id="out"></pre><script>
const svg = document.querySelector('svg'), vb = svg.viewBox.baseVal, o = svg.getBoundingClientRect(), k = vb.width / o.width;
const out = {};
for (const r of svg.querySelectorAll('[data-mark]')) {
  const t = svg.getElementById(r.dataset.mark);
  if (!t) { out[r.dataset.mark] = null; continue; }
  const b = t.getBoundingClientRect();
  out[r.dataset.mark] = [(b.left - o.left) * k, (b.top - o.top) * k, b.width * k, b.height * k];
}
document.getElementById('out').textContent = JSON.stringify(out);
</script>"""


def fit(path):
    src = Path(path).read_text()
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(_PROBE % src)
    dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--dump-dom", f"file://{f.name}"],
                         capture_output=True, text=True, timeout=60).stdout
    Path(f.name).unlink()
    boxes = json.loads(html.unescape(dom.split('<pre id="out">', 1)[1].split("</pre>", 1)[0]))
    missing = [k for k, v in boxes.items() if v is None]
    if missing:
        sys.exit(f"{path}: no element with id {missing}")

    def place(m):
        tag = m.group(0)
        x, y, w, h = boxes[re.search(r'data-mark="([^"]+)"', tag).group(1)]
        tag = re.sub(r'\s(x|y|width|height)="[^"]*"', "", tag)
        geom = f' x="{x - PAD_X:.1f}" y="{y + PAD_Y:.1f}" width="{w + 2 * PAD_X:.1f}" height="{h - 2 * PAD_Y:.1f}"'
        return tag.replace("<rect", "<rect" + geom, 1)

    out = re.sub(r"<rect\b[^>]*\bdata-mark=\"[^\"]+\"[^>]*/>", place, src)
    Path(path).write_text(out)
    print(f"{path}: fitted {len(boxes)} mark(s)")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        fit(p)
