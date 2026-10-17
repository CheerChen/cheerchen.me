"""10x post: OKRs cascading from the company to each person (a tree, no figures)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pictogram import *  # noqa: E402,F403

OUT = "content/posts/10x-innovation-culture-program-ask-googler/okr-cascade.svg"


def node(cx, y, w, h, label):
    return (f'<rect x="{cx - w / 2}" y="{y}" width="{w}" height="{h}" rx="12" fill="{WHITE}" stroke="{INK}" stroke-width="3"/>'
            f'<text x="{cx}" y="{y + h / 2 + 6}" class="h" text-anchor="middle">{label}</text>')


def edge(d):
    return f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'


def more(cx, y):
    return "".join(f'<circle cx="{cx + dx}" cy="{y}" r="3.5" fill="{INK_DIM}"/>' for dx in (-12, 0, 12))


def member(x, y, name, krs):
    s = f'<rect x="{x}" y="{y}" width="240" height="160" rx="14" fill="{WHITE}" stroke="{INK}" stroke-width="3"/>'
    s += f'<text x="{x + 20}" y="{y + 30}" class="h">{name}</text>'
    for i, (label, weight, must) in enumerate(krs):
        ty = y + 58 + i * 34
        s += (f'<text x="{x + 20}" y="{ty}" class="s">{label}</text>'
              f'<text x="{x + 220}" y="{ty}" class="s" font-weight="700" text-anchor="end">{weight}%</text>'
              f'<rect x="{x + 20}" y="{ty + 7}" width="200" height="10" rx="5" fill="{TRACK}"/>'
              f'<rect x="{x + 20}" y="{ty + 7}" width="{weight * 2}" height="10" rx="5" fill="{GREEN if must else YELLOW}" '
              f'stroke="{INK}" stroke-width="2"/>')
    return s


b = ['<text x="60" y="60" class="title">OKRs cascade like a tree</text>',
     f'<text x="60" y="90" class="t-dim">From the CEO down to every employee, each level aligns with the one above</text>']

for label, y in (("COMPANY", 150), ("DEPARTMENT", 264), ("TEAM", 372), ("INDIVIDUAL", 480)):
    b.append(f'<text x="60" y="{y}" class="tag" fill="{INK_DIM}">{label}</text>')

b += [edge("M600,178 V204 H280 V232"), edge("M600,178 V232"), edge("M600,204 H920 V232"),
      edge("M600,288 V314 H490 V342"), edge("M600,314 H710 V342"),
      edge("M490,394 V420 H360 V452"), edge("M490,420 H620 V452")]

b.append(f'<rect x="460" y="114" width="280" height="64" rx="14" fill="{INK}"/>')
b.append(f'<text x="600" y="143" class="b" fill="{WHITE}" text-anchor="middle" style="fill:{WHITE}">Company OKR</text>')
b.append(f'<text x="600" y="164" class="s" text-anchor="middle" style="fill:{LGREEN}">set by top leadership</text>')
b += [node(280, 232, 200, 56, "Department A"), node(600, 232, 200, 56, "Department B"),
      node(920, 232, 200, 56, "Department C"), more(280, 326), more(920, 326),
      node(490, 342, 180, 52, "Team 1"), node(710, 342, 180, 52, "Team 2"), more(710, 432)]

b.append(member(240, 452, "Member A", [("KR1 · must-do", 40, True), ("KR2 · must-do", 35, True), ("KR3 · own idea", 25, False)]))
b.append(member(500, 452, "Member B", [("KR1 · must-do", 50, True), ("KR2 · own idea", 30, False), ("KR3 · own idea", 20, False)]))

# legend
lx, ly = 800, 466
b += [f'<text x="{lx}" y="{ly}" class="h">Inside each OKR</text>',
      f'<rect x="{lx}" y="{ly + 20}" width="28" height="12" rx="6" fill="{GREEN}" stroke="{INK}" stroke-width="2"/>',
      f'<text x="{lx + 40}" y="{ly + 31}" class="s">Must-do items</text>',
      f'<text x="{lx + 40}" y="{ly + 51}" class="s-dim">passed down, higher weight</text>',
      f'<rect x="{lx}" y="{ly + 74}" width="28" height="12" rx="6" fill="{YELLOW}" stroke="{INK}" stroke-width="2"/>',
      f'<text x="{lx + 40}" y="{ly + 85}" class="s">Items the person adds</text>',
      f'<text x="{lx + 40}" y="{ly + 105}" class="s-dim">so it is not 100% top-down</text>',
      f'<text x="{lx}" y="{ly + 140}" class="s-dim">Bar length = weight</text>']

# transparency banner
b.append(f'<rect x="60" y="648" width="1080" height="56" rx="14" fill="{LYELLOW}" stroke="{INK}" stroke-width="3"/>')
b.append(f'<g transform="translate(94,676)" fill="none" stroke="{INK}" stroke-width="3">'
         f'<path d="M-17,0 C-8,-12 8,-12 17,0 C8,12 -8,12 -17,0 z" fill="{WHITE}"/><circle r="5" fill="{INK}" stroke="none"/></g>')
b.append('<text x="126" y="682" class="h">Every OKR is open to the whole company: anyone can read their manager\'s, '
         'and their manager\'s manager\'s.</text>')

write(OUT, svg(1200, 740, "How OKRs cascade from the company to each person",
               "A tree from the company OKR through departments and teams to individuals. Each person's OKR mixes "
               "must-do key results with a high weight, passed down from above, and key results they add themselves. "
               "Every OKR is visible to the whole company.", b))
