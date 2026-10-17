"""10x post: a manager with 10+ KRs watches the top two and handles the rest by type."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pictogram import *  # noqa: E402,F403

OUT = "content/posts/10x-innovation-culture-program-ask-googler/kr-focus.svg"

b = ['<text x="600" y="60" class="title" text-anchor="middle">Watch the top 2. Let the rest run.</text>']

# Left: KRs sorted by weight
b.append(panel(40, 90, 600, 510, "10+ KRs, SORTED BY WEIGHT", INK))
base, x0, bw, gap = 520, 190, 34, 10
heights = [190, 160, 80, 70, 60, 52, 45, 38, 30, 24]
for i, h in enumerate(heights):
    x = x0 + i * (bw + gap)
    top2 = i < 2
    b.append(f'<rect x="{x}" y="{base - h}" width="{bw}" height="{h}" rx="6" fill="{GREEN if top2 else GRAY}" '
             f'stroke="{INK}" stroke-width="3"/>')
    weight = ' font-weight="700"' if top2 else ""
    b.append(f'<text x="{x + bw / 2}" y="{base + 22}" class="{"s" if top2 else "s-dim"}" text-anchor="middle"{weight}>KR{i + 1}</text>')
b.append(ground(70, 610, base))
# focus marker over the top two
b.append(f'<path d="M{x0},{base - 205} V{base - 215} H{x0 + 2 * bw + gap} V{base - 205}" fill="none" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>')
b.append(highlight(x0 - 6, base - 252, 108, 30))
b.append(f'<text x="{x0 + 39}" y="{base - 230}" class="h" text-anchor="middle">Focus</text>')
b.append(sparkle(x0 + 2 * bw + gap + 34, base - 236, 9))
# the rest
rx1, rx2 = x0 + 2 * (bw + gap), x0 + 9 * (bw + gap) + bw
b.append(f'<path d="M{rx1},{base + 34} V{base + 44} H{rx2} V{base + 34}" fill="none" stroke="{INK_DIM}" stroke-width="3" stroke-linejoin="round"/>')
b.append(f'<text x="{(rx1 + rx2) / 2}" y="{base + 66}" class="s-dim" text-anchor="middle">the rest: handled by type, see right</text>')

b.append(person(110, base, "point", GREEN))
b.append(bubble(60, 270, 128, 76, (112, 390), [("These two", "t"), ("matter most.", "t")], line_h=24, first_y=32))

# arrows to the right column
b.append(arrow(612, 215, 676, 215, w=14))
b.append(arrow(612, 470, 676, 470, w=14))

# Right top: quantitative
b.append(panel(680, 90, 480, 230, "QUANTITATIVE KRs", GREEN))
b.append('<text x="710" y="160" class="t">Just watch the number</text>')
b.append(f'<rect x="710" y="178" width="420" height="118" rx="12" fill="{BG}" stroke="{INK}" stroke-width="3"/>')
pts = [(730, 270), (770, 258), (810, 262), (850, 240), (890, 244), (930, 222), (970, 214), (1010, 200)]
b.append(f'<path d="{poly(pts)}" fill="none" stroke="{GREEN}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>')
b.append(f'<circle cx="1010" cy="200" r="7" fill="{YELLOW}" stroke="{INK}" stroke-width="3"/>')
b.append('<text x="1110" y="240" font-size="34" font-weight="700" text-anchor="end">68%</text>')
b.append('<text x="1110" y="266" class="s-dim" text-anchor="end">on track</text>')

# Right bottom: qualitative
b.append(panel(680, 340, 480, 260, "QUALITATIVE KRs", INK))
b.append('<text x="710" y="404" class="t">Confirm at the regular check-in</text>')
b.append(ground(710, 1130, 580))
b.append(person(790, 580, "point", GREEN, scale=0.75))
b.append(person(1040, 580, "stand", YELLOW, hair="long", scale=0.75, flip=True))
b.append(bubble(710, 426, 230, 48, (796, 489), [("Anything blocking you?", "s")], first_y=30))
b.append(bubble(960, 426, 150, 48, (1036, 489), [("All good!", "s")], first_y=30))

b.append('<text x="600" y="634" class="cap" text-anchor="middle">Managers track key results, not the process.</text>')

write(OUT, svg(1200, 660, "Watch the top 2 KRs, let the rest run",
               "A manager's 10 key results sorted by weight. The two heaviest are marked as the focus. The rest are "
               "split by type: quantitative ones are tracked by their number, qualitative ones are confirmed in a "
               "short check-in conversation.", b))
