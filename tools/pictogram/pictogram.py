"""Building blocks for pictogram-style post figures.

Style: thick dark-green outline, flat green / yellow fills, white trousers,
round heads. Every function returns an SVG fragment string; a figure script
concatenates them and passes the result to `write()`.
"""
import math
from pathlib import Path

INK = "#1f4a33"
INK_DIM = "#6b7f72"
GREEN = "#3e9f3a"
LGREEN = "#d6ecc9"
YELLOW = "#e9c32b"
LYELLOW = "#fbefb6"
RED = "#c4472f"
GRAY = "#c3c7c4"
TRACK = "#eef1ea"
WHITE = "#ffffff"
BG = "#fbfbf7"
FONT = "-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"

REPO = Path(__file__).resolve().parents[2]

STYLE = f"""
    text{{font-family:{FONT};fill:{INK}}}
    .title{{font-size:30px;font-weight:700}}
    .tag{{font-size:14px;font-weight:700;letter-spacing:1.5px}}
    .cap{{font-size:18px;font-weight:600}}
    .b{{font-size:19px;font-weight:700}}
    .h{{font-size:17px;font-weight:700}}
    .t{{font-size:16px}}
    .s{{font-size:14px}}
    .t-dim{{font-size:16px;fill:{INK_DIM}}}
    .s-dim{{font-size:14px;fill:{INK_DIM}}}
    .sign{{font-size:15px;font-weight:700}}
    .num{{font-size:15px;font-weight:700;fill:{WHITE}}}
"""

# Joint coordinates in person space: origin at the feet, head centre at y=-101.
# Each limb is shoulder/hip -> elbow/knee -> hand/foot.
_STAND_LEGS = [[(-5, -46), (-6, -23), (-7, 0)], [(5, -46), (6, -23), (7, 0)]]
_DOWN_L = [(-8, -76), (-14, -60), (-15, -46)]
_DOWN_R = [(8, -76), (14, -60), (15, -46)]
POSES = {
    "stand": dict(arms=[_DOWN_L, _DOWN_R], legs=_STAND_LEGS, lean=0),
    "point": dict(arms=[_DOWN_L, [(8, -76), (24, -82), (40, -94)]], legs=_STAND_LEGS, lean=0),
    "raise": dict(arms=[_DOWN_L, [(8, -76), (16, -96), (18, -116)]], legs=_STAND_LEGS, lean=0),
    "megaphone": dict(arms=[_DOWN_L, [(8, -76), (22, -78), (34, -88)]], legs=_STAND_LEGS, lean=0),
    "mic": dict(arms=[_DOWN_L, [(8, -76), (20, -66), (14, -90)]], legs=_STAND_LEGS, lean=0),
    "stressed": dict(
        arms=[[(-8, -76), (-24, -86), (-13, -104)], [(8, -76), (24, -86), (13, -104)]],
        legs=[[(-5, -46), (-8, -23), (-10, 0)], [(5, -46), (8, -23), (10, 0)]], lean=0),
    "walk": dict(
        arms=[[(-6, -76), (-16, -62), (-22, -52)], [(6, -76), (14, -60), (24, -58)]],
        legs=[[(-3, -46), (-12, -24), (-20, -2)], [(3, -46), (12, -26), (20, -4)]], lean=5),
    "step-up": dict(
        arms=[[(-6, -76), (-16, -62), (-22, -52)], [(6, -76), (14, -60), (24, -58)]],
        legs=[[(-3, -46), (-10, -24), (-14, 0)], [(3, -46), (18, -34), (22, -18)]], lean=5),
    "run": dict(
        arms=[[(-6, -76), (-20, -70), (-26, -82)], [(6, -76), (16, -64), (28, -70)]],
        legs=[[(-3, -46), (-18, -30), (-28, -14)], [(3, -46), (18, -30), (16, -4)]], lean=9),
    "cheer": dict(
        arms=[[(-8, -76), (-20, -94), (-24, -112)], [(8, -76), (20, -94), (24, -112)]],
        legs=[[(-5, -46), (-9, -23), (-13, 0)], [(5, -46), (9, -23), (13, 0)]], lean=0),
}
_CYCLIST_LEGS = [[(-4, -52), (6, -38), (-2, -20)], [(4, -52), (16, -40), (14, -22)]]


def poly(pts):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def limb(pts, color, w=12):
    """An outlined stroke: a wide ink stroke under a narrower colour stroke."""
    d = poly(pts)
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w - 6}" stroke-linecap="round" stroke-linejoin="round"/>')


def person(x, y, pose, shirt, pants=WHITE, flip=False, hair="short", scale=1.0, cyclist=False):
    """A figure standing at (x, y). flip=True faces left. ~130px tall at scale 1."""
    p = POSES[pose]
    lean = p["lean"]
    legs = _CYCLIST_LEGS if cyclist else p["legs"]
    arms = [[(ax + lean * (-ay / 80), ay) for ax, ay in a] for a in p["arms"]]
    out = [limb(legs[0], pants, 14), limb(arms[0], shirt), limb(legs[1], pants, 14)]
    for leg in legs:
        fx, fy = leg[-1]
        out.append(f'<ellipse cx="{fx + 3:.1f}" cy="{fy:.1f}" rx="7" ry="4.5" fill="{INK}"/>')
    out.append(limb([(lean * 0.6, -80), (0, -50)], shirt, 28))
    out.append(limb(arms[1], shirt))
    for a in arms:
        hx, hy = a[-1]
        out.append(f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="4.5" fill="{WHITE}" stroke="{INK}" stroke-width="3"/>')
    hx, hy = lean, -101
    out.append(f'<circle cx="{hx}" cy="{hy}" r="14" fill="{WHITE}" stroke="{INK}" stroke-width="3.5"/>')
    if hair == "short":
        out.append(f'<path d="M{hx - 14},{hy - 1} A14,14 0 0 1 {hx + 14},{hy - 1} Q{hx + 4},{hy - 8} {hx - 14},{hy - 1} z" fill="{INK}"/>')
    elif hair == "long":
        out.append(f'<path d="M{hx - 15},{hy + 10} L{hx - 15},{hy - 2} A15,15 0 0 1 {hx + 15},{hy - 2} '
                   f'Q{hx + 2},{hy - 10} {hx - 7},{hy - 2} L{hx - 8},{hy + 10} z" fill="{INK}"/>')
    elif hair == "cap":
        out.append(f'<path d="M{hx - 14},{hy - 2} A14,14 0 0 1 {hx + 14},{hy - 2} z" fill="{GREEN}" stroke="{INK}" stroke-width="3"/>'
                   f'<line x1="{hx - 14}" y1="{hy - 2}" x2="{hx + 20}" y2="{hy - 2}" stroke="{INK}" stroke-width="3.5" stroke-linecap="round"/>')
    sx = -scale if flip else scale
    return f'<g transform="translate({x},{y}) scale({sx},{scale})">' + "".join(out) + "</g>"


def hand(x, y, pose, flip=False, scale=1.0, which=1):
    """Canvas position of a figure's hand, for attaching props like a megaphone or mic."""
    hx, hy = POSES[pose]["arms"][which][-1]
    lean = POSES[pose]["lean"]
    hx += lean * (-hy / 80)
    return (x + (-hx if flip else hx) * scale, y + hy * scale)


def bubble(x, y, w, h, tail, lines, line_h=28, first_y=36):
    """A speech bubble whose tail points at `tail` (usually just above a head)."""
    tx, ty = tail
    below = ty > y + h
    edge = y + h if below else y
    bx = min(max(tx - 13, x + 22), x + w - 48)
    s = (f'<path d="M{bx},{edge} L{tx},{ty} L{bx + 26},{edge}" fill="{WHITE}" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>'
         f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{WHITE}" stroke="{INK}" stroke-width="3.5"/>'
         f'<path d="M{bx + 2},{edge + (-1.5 if below else 1.5)} L{bx + 24},{edge + (-1.5 if below else 1.5)}" stroke="{WHITE}" stroke-width="5"/>')
    for i, (txt, cls) in enumerate(lines):
        s += f'<text x="{x + 22}" y="{y + first_y + i * line_h}" class="{cls}">{txt}</text>'
    return s


def spiky(cx, cy, r=30, n=14):
    """The grey spiky "..." bubble: someone overwhelmed or silent."""
    pts = []
    for i in range(n * 2):
        a = math.pi * i / n
        rr = r if i % 2 == 0 else r * 0.74
        pts.append((cx + rr * math.cos(a) * 1.25, cy + rr * math.sin(a)))
    dots = "".join(f'<circle cx="{cx + dx}" cy="{cy}" r="4" fill="{INK}"/>' for dx in (-12, 0, 12))
    return f'<path d="{poly(pts)} z" fill="{WHITE}" stroke="{GRAY}" stroke-width="3" stroke-linejoin="round"/>' + dots


def panel(x, y, w, h, tag=None, tag_color=INK):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="{WHITE}" stroke="{INK}" stroke-width="3"/>'
    if tag:
        s += f'<text x="{x + 30}" y="{y + 38}" class="tag" fill="{tag_color}">{tag}</text>'
    return s


def ground(x1, x2, y):
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>'


def area(cx, cy, rx, ry=26):
    """The light-green dotted ellipse that marks a gathering spot."""
    return (f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{LGREEN}" stroke="{GREEN}" '
            f'stroke-width="4" stroke-dasharray="1,9" stroke-linecap="round"/>')


def trail(x1, x2, y):
    return f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{INK}" stroke-width="3" stroke-linecap="round" stroke-dasharray="2,9"/>'


def sparkle(x, y, r=10):
    return (f'<path d="M{x},{y - r} l{r * 0.4},{r * 0.6} l{r * 0.6},{r * 0.4} l{-r * 0.6},{r * 0.4} l{-r * 0.4},{r * 0.6} '
            f'l{-r * 0.4},{-r * 0.6} l{-r * 0.6},{-r * 0.4} l{r * 0.6},{-r * 0.4} z" fill="{YELLOW}" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>')


def arrow(x1, y1, x2, y2, color=YELLOW, w=16):
    """A fat flat arrow like the one on the evacuation signs."""
    ang = math.atan2(y2 - y1, x2 - x1)
    length = math.hypot(x2 - x1, y2 - y1)
    head = w * 1.6
    body = length - head
    pts = [(0, -w / 2), (body, -w / 2), (body, -w), (length, 0), (body, w), (body, w / 2), (0, w / 2)]
    c, s = math.cos(ang), math.sin(ang)
    pts = [(x1 + px * c - py * s, y1 + px * s + py * c) for px, py in pts]
    return f'<path d="{poly(pts)} z" fill="{color}"/>'


def bicycle(x, y):
    return (f'<circle cx="{x - 30}" cy="{y - 17}" r="17" fill="none" stroke="{INK}" stroke-width="4"/>'
            f'<circle cx="{x + 30}" cy="{y - 17}" r="17" fill="none" stroke="{INK}" stroke-width="4"/>'
            f'<path d="M{x - 30},{y - 17} L{x - 6},{y - 50} L{x + 22},{y - 46} L{x + 30},{y - 17} M{x - 6},{y - 50} L{x},{y - 20} L{x + 22},{y - 46}" '
            f'fill="none" stroke="{GREEN}" stroke-width="5" stroke-linejoin="round"/>'
            f'<path d="M{x + 18},{y - 60} L{x + 22},{y - 46}" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>'
            f'<path d="M{x - 14},{y - 54} L{x + 2},{y - 54}" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>')


def station(x, y, name, w=170, h=140, clock=None):
    """A station front with yellow pillars and a name board; clock="7:00" adds a clock on top."""
    s = (f'<rect x="{x}" y="{y - h}" width="{w}" height="{h}" fill="{GRAY}" opacity="0.35"/>'
         f'<rect x="{x - 8}" y="{y - h - 22}" width="{w + 16}" height="26" rx="5" fill="{GRAY}" stroke="{INK}" stroke-width="4"/>')
    for px in (x + 6, x + w - 22):
        s += f'<rect x="{px}" y="{y - h + 4}" width="16" height="{h - 4}" fill="{YELLOW}" stroke="{INK}" stroke-width="3.5"/>'
    s += (f'<rect x="{x + 30}" y="{y - h + 16}" width="{w - 60}" height="30" rx="4" fill="{WHITE}" stroke="{INK}" stroke-width="3"/>'
          f'<rect x="{x + 30}" y="{y - h + 16}" width="14" height="30" fill="{GREEN}" stroke="{INK}" stroke-width="3"/>'
          f'<text x="{x + w / 2 + 7}" y="{y - h + 37}" class="sign" text-anchor="middle">{name}</text>')
    if clock:
        hh, mm = (int(v) for v in clock.split(":"))
        cx, cy = x + w / 2, y - h - 50
        ma = math.radians(mm * 6 - 90)
        ha = math.radians((hh % 12 + mm / 60) * 30 - 90)
        s += (f'<line x1="{cx}" y1="{cy + 22}" x2="{cx}" y2="{y - h - 22}" stroke="{INK}" stroke-width="4"/>'
              f'<circle cx="{cx}" cy="{cy}" r="22" fill="{WHITE}" stroke="{INK}" stroke-width="4"/>'
              f'<line x1="{cx}" y1="{cy}" x2="{cx + 15 * math.cos(ma):.1f}" y2="{cy + 15 * math.sin(ma):.1f}" stroke="{INK}" stroke-width="3.5" stroke-linecap="round"/>'
              f'<line x1="{cx}" y1="{cy}" x2="{cx + 11 * math.cos(ha):.1f}" y2="{cy + 11 * math.sin(ha):.1f}" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>'
              f'<circle cx="{cx}" cy="{cy}" r="3" fill="{INK}"/>')
    return s


def signboard(x, y, w, h, legs=40):
    """A board on two yellow legs; (x, y) is the top-left of the board. Draw content on top."""
    s = ""
    for lx in (x + w * 0.2, x + w * 0.8 - 14):
        s += f'<rect x="{lx}" y="{y + h - 6}" width="14" height="{legs + 6}" fill="{YELLOW}" stroke="{INK}" stroke-width="3.5"/>'
    s += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{WHITE}" stroke="{INK}" stroke-width="5"/>'
    return s


def megaphone(x, y, flip=False):
    """A megaphone held at (x, y), opening to the right (or left if flipped), with sound lines."""
    d = -1 if flip else 1
    s = (f'<path d="M{x},{y - 6} L{x + d * 30},{y - 17} L{x + d * 30},{y + 17} L{x},{y + 6} z" '
         f'fill="{YELLOW}" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>')
    for i, r in enumerate((14, 24)):
        cx = x + d * (38 + i * 8)
        s += (f'<path d="M{cx},{y - r} Q{cx + d * r * 0.6},{y} {cx},{y + r}" fill="none" stroke="{INK}" '
              f'stroke-width="3" stroke-linecap="round"/>')
    return s


def mic(x, y):
    return (f'<line x1="{x}" y1="{y}" x2="{x - 4}" y2="{y + 16}" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>'
            f'<circle cx="{x + 1}" cy="{y - 4}" r="6" fill="{GRAY}" stroke="{INK}" stroke-width="3"/>')


def number_badge(cx, cy, n, color=GREEN):
    return (f'<circle cx="{cx}" cy="{cy}" r="15" fill="{color}" stroke="{INK}" stroke-width="3"/>'
            f'<text x="{cx}" y="{cy + 5}" class="num" text-anchor="middle">{n}</text>')


def highlight(x, y, w, h=34):
    """The yellow band used behind headline text on the signs."""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{YELLOW}"/>'


def svg(w, h, title, desc, body, bg=BG):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">\n'
            f'  <title id="title">{title}</title>\n  <desc id="desc">{desc}</desc>\n'
            f'  <style>{STYLE}  </style>\n  <rect width="{w}" height="{h}" fill="{bg}"/>\n'
            + "\n".join(body) + "\n</svg>\n")


def write(rel_path, content):
    """Write to a path relative to the repo root and report it."""
    path = REPO / rel_path
    path.write_text(content)
    print(f"wrote {rel_path}")
