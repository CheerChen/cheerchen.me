"""TBS Kustamie post: Lambda concurrency over time, the AWS-docs illustration from the 負荷指標 slide."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archdiagram import *  # noqa: E402,F403

OUT = "content/posts/tbs-kustamie-aws-serverless-large-scale-live-streaming/arch-03-lambda-concurrency.svg"
INIT, INVOKE, TICK = "#c79bf2", "#8b8cf0", "#3f8a50"

# Request bars as (row, start, init_end or None, end, number), in the slide's own horizontal units;
# None means the request reused a free environment and had no Init.
BARS = [(0, 200, 295, 640, 1), (1, 232, 322, 670, 2), (2, 232, 322, 670, 3), (3, 425, 518, 872, 4), (4, 518, 612, 970, 5),
        (0, 765, None, 1125, 6), (1, 822, None, 1183, 7), (2, 833, None, 1195, 8), (5, 852, 948, 1313, 9), (3, 982, None, 1347, 10)]
TICKS = [("t1", 240), ("t2", 540), ("t3", 655), ("t4", 858), ("t5", 1005), ("t6", 1303)]
X0, X1, TOP, ROW, BH = 190, 1130, 110, 40, 28
sx = lambda v: X0 + (v - 200) * (X1 - X0) / (1347 - 200)
BOTTOM = TOP + 6 * ROW


def busy(t):
    """Environments in Init or Invoke at time t."""
    return sum(1 for _, a, _, b, _ in BARS if a <= t <= b)


b = ['<text x="40" y="34" class="grp">Lambda concurrency over time</text>',
     note(40, 54, "Illustration from the AWS Lambda documentation, as shown on the talk slide")]

# legend
for i, (color, text) in enumerate(((INIT, "Init: a new execution environment starts (cold start)"),
                                   (INVOKE, "Invoke: the function handles the request"))):
    b.append(f'<rect x="{660 + i * 0}" y="{22 + i * 22}" width="22" height="14" rx="2" fill="{color}"/>'
             f'<text x="{690}" y="{34 + i * 22}" class="lbl">{text}</text>')

# time axis and ticks
b.append(path([(X0 - 10, 88), (X1 + 30, 88)], color=INK))
b.append(note(X0 - 18, 92, "time", "end"))
for name, v in TICKS:
    x = sx(v)
    b.append(f'<line x1="{x:.1f}" y1="76" x2="{x:.1f}" y2="{BOTTOM + 14}" stroke="{TICK}" stroke-width="1.5" stroke-dasharray="3,4"/>')
    b.append(f'<text x="{x:.1f}" y="72" class="lbl" font-weight="700" text-anchor="middle" style="fill:{TICK}">{name}</text>')

# the requests
for row, a, ie, e, n in BARS:
    y = TOP + row * ROW
    xa, xe = sx(a), sx(e)
    if ie:
        xi = sx(ie)
        b.append(f'<rect x="{xa:.1f}" y="{y}" width="{xi - xa:.1f}" height="{BH}" fill="{INIT}"/>'
                 f'<text x="{(xa + xi) / 2:.1f}" y="{y + 19}" class="lbl" text-anchor="middle" style="fill:#4a2d73">Init</text>')
        xa = xi
    b.append(f'<rect x="{xa:.1f}" y="{y}" width="{xe - xa:.1f}" height="{BH}" fill="{INVOKE}"/>'
             f'<text x="{(xa + xe) / 2:.1f}" y="{y + 19}" class="lbl" text-anchor="middle" style="fill:#ffffff">Invoke</text>')
    cx = sx(a) - 16
    b.append(f'<circle cx="{cx:.1f}" cy="{y + BH / 2}" r="11" fill="#f2b233"/>'
             f'<text x="{cx:.1f}" y="{y + BH / 2 + 4.5}" class="lbl" font-weight="700" text-anchor="middle" style="fill:#5a3b00">{n}</text>')

# concurrency at each tick, counted from the bars
b.append(f'<line x1="{X0 - 10}" y1="{BOTTOM + 14}" x2="{X1 + 30}" y2="{BOTTOM + 14}" stroke="{TICK}" stroke-width="2"/>')
b.append(f'<text x="{X0 - 18}" y="{BOTTOM + 44}" class="lbl" font-weight="700" text-anchor="end" style="fill:{TICK}">concurrency</text>')
for name, v in TICKS:
    x = sx(v)
    b.append(f'<circle cx="{x:.1f}" cy="{BOTTOM + 39}" r="15" fill="#ffffff" stroke="{TICK}" stroke-width="2"/>'
             f'<text x="{x:.1f}" y="{BOTTOM + 45}" class="role" text-anchor="middle" style="fill:{TICK}">{busy(v)}</text>')

# what to read from it
notes = ["Requests 6, 7, 8 and 10 arrive just after an environment frees up and reuse it, so they skip Init.",
         "Request 9 finds no free environment and cold-starts a new one.",
         "Concurrency is the number of environments busy at that instant (in Init or Invoke), not requests per second."]
for i, text in enumerate(notes):
    b.append(f'<circle cx="54" cy="{BOTTOM + 86 + i * 24}" r="3" fill="{INK}"/>')
    b.append(f'<text x="66" y="{BOTTOM + 91 + i * 24}" class="lbl">{text}</text>')

write(OUT, svg(1200, BOTTOM + 160, "Lambda concurrency over time",
               "Ten requests over time from the AWS Lambda documentation. Requests 1 to 5 and 9 start with an Init "
               "phase, a cold start; requests 6, 7, 8 and 10 reuse an environment that just finished and only Invoke. "
               "Concurrency, the number of busy environments, is 3, 5, 4, 6, 5 and 2 at ticks t1 to t6.", b))
