"""Switch 2 GameChat post: P2P mesh vs SFU, with media streams animated along each link."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archdiagram import *  # noqa: E402,F403

OUT = "content/posts/switch-2-gamechat-backend-sfu-dynamodb-consistency/p2p-mesh-vs-sfu-animated.svg"
SENT, FORWARDED = "#1d8102", "#139ad6"

FLOW_CSS = """<style>
  .st{fill:none;stroke-width:3;stroke-dasharray:8 8;stroke-linecap:round;animation:flow 1.2s linear infinite}
  @keyframes flow{to{stroke-dashoffset:-16}}
  @media (prefers-reduced-motion:reduce){.st{animation:none}}
</style>"""


def stream(p, q, color, gap=46, offset=5, gap_end=None):
    """One media stream from p to q: shortened to clear the endpoints, shifted right of its direction."""
    gap_end = gap if gap_end is None else gap_end
    (x1, y1), (x2, y2) = p, q
    d = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / d, (y2 - y1) / d
    nx, ny = -uy * offset, ux * offset
    a = (x1 + ux * gap + nx, y1 + uy * gap + ny)
    b = (x2 - ux * gap_end + nx, y2 - uy * gap_end + ny)
    return f'<path class="st" d="M{a[0]:.0f},{a[1]:.0f} L{b[0]:.0f},{b[1]:.0f}" stroke="{color}"/>'


def panel(x, title, sub, lines):
    s = (f'<rect x="{x}" y="20" width="560" height="560" rx="14" fill="#f7f8f9" stroke="#d5d9de" stroke-width="1.5"/>'
         f'<text x="{x + 280}" y="62" class="title" text-anchor="middle">{title}</text>'
         f'<text x="{x + 280}" y="88" class="note" text-anchor="middle">{sub}</text>')
    for i, (text, bold) in enumerate(lines):
        weight = ' font-weight="700"' if bold else ""
        s += f'<text x="{x + 280}" y="{520 + i * 24}" class="lbl"{weight} text-anchor="middle">{text}</text>'
    return s


b = [FLOW_CSS]

# P2P mesh: every client streams to every other client
b.append(panel(20, "P2P mesh", "every client sends to every other client",
               [("4 clients: 6 links, each sends 3 streams and receives 3", True),
                ("12 clients: 66 links, 11 up and 11 down per client", False)]))
mesh = [(170, 190), (430, 190), (170, 410), (430, 410)]
for p in mesh:
    for q in mesh:
        if p != q:
            b.append(stream(p, q, SENT, gap=50))
for x, y in mesh:
    b.append(switch(x, y, label=False))

# SFU: each client sends once; the SFU forwards the others' streams back
b.append(panel(620, "SFU", "each client sends once; the SFU forwards selectively",
               [("4 clients: 4 links, each sends 1 stream", True),
                ("12 clients: 12 links, still 1 upload per client", False)]))
hub = (900, 300)
spokes = [(900, 130), (690, 300), (1110, 300), (900, 465)]
for c in spokes:
    b.append(stream(c, hub, SENT, gap=44, gap_end=40))
    b.append(stream(hub, c, FORWARDED, gap=40, gap_end=44))
b.append(f'<rect x="868" y="268" width="64" height="64" rx="8" fill="#ffffff"/>')
b.append(icon("ec2", *hub, 56))
b.append(f'<text x="{hub[0] + 40}" y="{hub[1] - 34}" class="lbl" font-weight="700">SFU server</text>')
for x, y in spokes:
    b.append(switch(x, y, label=False))

# legend
for x, color, text in ((330, SENT, "stream sent by a client"), (660, FORWARDED, "stream forwarded by the SFU")):
    b.append(f'<line x1="{x}" y1="612" x2="{x + 44}" y2="612" stroke="{color}" stroke-width="3" stroke-dasharray="8 8" stroke-linecap="round"/>'
             f'<text x="{x + 56}" y="617" class="lbl">{text}</text>')

write(OUT, svg(1200, 640, "P2P mesh vs SFU: connection topology",
               "Animated comparison. In a 4-client P2P mesh every client sends a stream to each of the other three, "
               "6 links in all; with 12 clients that grows to 66 links and 11 uploads per client. With an SFU each "
               "client sends one stream to the server, which forwards the others' streams back: 4 links for 4 "
               "clients, 12 for 12, and still one upload per client.", b))
