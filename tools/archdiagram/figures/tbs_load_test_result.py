"""TBS Kustamie post: the E2E load-test result, redrawn from the CloudWatch chart on the 負荷試験と上限緩和 slide.

Only the three values at the cursor are real numbers; the curve shapes are traced from the photo.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archdiagram import *  # noqa: E402,F403

OUT = "content/posts/tbs-kustamie-aws-serverless-large-scale-live-streaming/arch-07-load-test-result.svg"
COUNT, RPS, ERR = "#c9553f", "#e8902c", "#8f5fa8"
X0, X1, Y0, Y1 = 120, 900, 104, 432           # plot box: left, right, top (700k), bottom (0)
vy = lambda k: Y1 - (Y1 - Y0) * k / 700       # thousands -> y
px = lambda f: X0 + (X1 - X0) * f             # fraction of the time span -> x
CURSOR = 0.73

b = ['<text x="40" y="34" class="grp">E2E load test: API calls and 4XX errors</text>',
     note(40, 54, "Redrawn from the CloudWatch chart on the talk slide; curve shapes are approximate, values at the cursor are as shown")]

# axes and gridlines
for k in range(0, 701, 100):
    y = vy(k)
    b.append(f'<line x1="{X0}" y1="{y:.1f}" x2="{X1}" y2="{y:.1f}" stroke="#e6e9ee"/>')
    b.append(note(X0 - 10, y + 4, "0" if k == 0 else f"{k}k", "end"))
b.append(f'<line x1="{X0}" y1="{Y1}" x2="{X1}" y2="{Y1}" stroke="#9aa3ad" stroke-width="1.5"/>')
b.append(note(X1, Y1 + 22, "time →", "end"))
b.append(note(X0 - 10, Y0 - 16, "per minute", "end"))

# the cursor at the moment errors start
cx = px(CURSOR)
b.append(f'<line x1="{cx:.1f}" y1="{Y0 - 6}" x2="{cx:.1f}" y2="{Y1}" stroke="#5f6b7a" stroke-width="1.5" stroke-dasharray="5,4"/>')

# traced curves
b.append(f'<path d="M{px(0.24):.0f},{vy(2):.1f} L{px(0.92):.0f},{vy(2):.1f}" fill="none" stroke="{RPS}" stroke-width="3"/>')
b.append(f'<path d="M{px(0.24):.0f},{vy(0):.1f} C{px(0.42):.0f},{vy(30):.1f} {px(0.62):.0f},{vy(320):.1f} {cx:.1f},{vy(610):.1f} '
         f'C{px(0.76):.0f},{vy(660):.1f} {px(0.79):.0f},{vy(700):.1f} {px(0.82):.0f},{vy(700):.1f} L{px(0.86):.0f},{vy(700):.1f} '
         f'L{px(0.87):.0f},{vy(470):.1f}" fill="none" stroke="{COUNT}" stroke-width="3"/>')
b.append(f'<path d="M{cx:.1f},{vy(0):.1f} C{px(0.76):.0f},{vy(70):.1f} {px(0.79):.0f},{vy(92):.1f} {px(0.81):.0f},{vy(90):.1f} '
         f'C{px(0.83):.0f},{vy(88):.1f} {px(0.84):.0f},{vy(70):.1f} {px(0.85):.0f},{vy(62):.1f}" fill="none" stroke="{ERR}" stroke-width="3"/>')
b.append(f'<circle cx="{cx:.1f}" cy="{vy(610):.1f}" r="5" fill="#ffffff" stroke="{COUNT}" stroke-width="2.5"/>')

# what happened at the cursor
b.append(f'<path d="M{cx - 14:.0f},{vy(610):.0f} L{px(0.5):.0f},{vy(610):.0f}" fill="none" stroke="{RED}" stroke-width="1.5"/>')
b.append(f'<text x="{px(0.5) - 8:.0f}" y="{vy(610) - 8:.0f}" class="lbl" font-weight="700" text-anchor="end" style="fill:{RED}">'
         f'~600,000 requests/min (10,000 RPS on average):</text>')
b.append(f'<text x="{px(0.5) - 8:.0f}" y="{vy(610) + 12:.0f}" class="lbl" font-weight="700" text-anchor="end" style="fill:{RED}">'
         f'4XX errors start</text>')

# value box, as read at the cursor
bx = 930
b.append(f'<rect x="{bx}" y="{Y0}" width="240" height="132" rx="6" fill="#ffffff" stroke="{INK}" stroke-width="1.5"/>')
b.append(f'<text x="{bx + 18}" y="{Y0 + 28}" class="lbl" font-weight="700">At the cursor</text>')
for i, (color, name, value) in enumerate(((COUNT, "Count", "609,946"), (RPS, "RPS", "10,166"), (ERR, "4XXError", "8,820"))):
    y = Y0 + 60 + i * 26
    b.append(f'<circle cx="{bx + 24}" cy="{y - 4}" r="5" fill="none" stroke="{color}" stroke-width="2.5"/>'
             f'<text x="{bx + 38}" y="{y}" class="lbl">{name}</text>'
             f'<text x="{bx + 222}" y="{y}" class="lbl" font-weight="700" text-anchor="end">{value}</text>')

# legend
for i, (color, name, meaning) in enumerate(((COUNT, "Count", "API calls per minute"), (RPS, "RPS", "average requests per second"),
                                            (ERR, "4XXError", "4xx errors"))):
    y = 284 + i * 28
    b.append(f'<line x1="{bx}" y1="{y - 5}" x2="{bx + 26}" y2="{y - 5}" stroke="{color}" stroke-width="3"/>'
             f'<text x="{bx + 36}" y="{y}" class="lbl"><tspan font-weight="700">{name}</tspan> {meaning}</text>')
b.append(note(bx, 390, "Count and 4XXError rise together"))
b.append(note(bx, 408, "from the cursor on."))

write(OUT, svg(1200, 470, "E2E load test: API calls and 4XX errors",
               "Redrawn CloudWatch chart from the E2E load test. API calls per minute climb steeply; at the cursor, "
               "609,946 calls per minute with an average of 10,166 RPS, 4XX errors start (8,820 at that point) and "
               "rise together with the calls, while average RPS stays near the floor of the scale. Curve shapes are "
               "approximate.", b))
