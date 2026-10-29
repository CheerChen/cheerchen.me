"""Bitwarden cleanup post: local Mac parallel workers + remote coordinator architecture."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pictogram import *  # noqa: E402,F403

OUT = "content/posts/bitwarden-cleanup-with-agents/local-agent-pipeline.svg"


def box(x, y, w, h, fill=WHITE, rx=12, stroke_w=3, dashed=False):
    dash = ' stroke-dasharray="6,6"' if dashed else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{INK}" stroke-width="{stroke_w}"{dash}/>'


def line_arrow(x1, y1, x2, y2, color=INK, dashed=False):
    ang = math.atan2(y2 - y1, x2 - x1)
    hl = 10
    p1 = (x2 - hl * math.cos(ang - 0.45), y2 - hl * math.sin(ang - 0.45))
    p2 = (x2 - hl * math.cos(ang + 0.45), y2 - hl * math.sin(ang + 0.45))
    dash = ' stroke-dasharray="5,5"' if dashed else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="3" stroke-linecap="round"{dash}/>'
            f'<path d="M{p1[0]:.1f},{p1[1]:.1f} L{x2:.1f},{y2:.1f} L{p2[0]:.1f},{p2[1]:.1f}" '
            f'fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')


def ortho_arrow(pts, color=INK, dashed=False):
    d = poly(pts)
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    hl = 10
    p1 = (x2 - hl * math.cos(ang - 0.45), y2 - hl * math.sin(ang - 0.45))
    p2 = (x2 - hl * math.cos(ang + 0.45), y2 - hl * math.sin(ang + 0.45))
    dash = ' stroke-dasharray="5,5"' if dashed else ""
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"{dash}/>'
            f'<path d="M{p1[0]:.1f},{p1[1]:.1f} L{x2:.1f},{y2:.1f} L{p2[0]:.1f},{p2[1]:.1f}" '
            f'fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')


def worker_row(x, y, idx, site, state, state_fill):
    s = box(x, y, 420, 52, fill=TRACK, rx=10, stroke_w=2.5)
    s += number_badge(x + 26, y + 26, idx, GREEN)
    s += f'<text x="{x + 52}" y="{y + 32}" class="h">{site}</text>'
    s += f'<rect x="{x + 298}" y="{y + 10}" width="108" height="32" rx="8" fill="{state_fill}" stroke="{INK}" stroke-width="2"/>'
    s += f'<text x="{x + 352}" y="{y + 31}" class="s" font-weight="700" text-anchor="middle">{state}</text>'
    return s


def file_pill(x, y, name, fill=LYELLOW):
    s = box(x, y, 176, 52, fill=fill, rx=10, stroke_w=2.5)
    s += f'<text x="{x + 88}" y="{y + 32}" class="h" text-anchor="middle">{name}</text>'
    return s


b = ['<text x="600" y="56" class="title" text-anchor="middle">Local Mac Workers + Remote Coordinator</text>']

# Left panel: Local Mac
b.append(panel(40, 86, 690, 420, "LOCAL MAC", GREEN))

b.append(box(68, 140, 200, 54, fill=LGREEN))
b.append('<text x="168" y="173" class="h" text-anchor="middle">Bitwarden CLI (600)</text>')

b.append(box(290, 140, 200, 54, fill=WHITE))
b.append('<text x="390" y="173" class="h" text-anchor="middle">task-template.md</text>')

b.append(line_arrow(168, 194, 168, 224))
b.append(line_arrow(390, 194, 390, 224))

# Parallel workers container
b.append(box(68, 230, 448, 246, fill=WHITE, rx=14, dashed=True))
b.append('<text x="86" y="258" class="tag" fill="#3e9f3a">PARALLEL AGENTS + EGO-BROWSER</text>')
b.append(worker_row(82, 272, 1, "Worker 1", "page.fill", LGREEN))
b.append(worker_row(82, 338, 2, "Worker 2", "wait OTP", LYELLOW))
b.append(worker_row(82, 404, 3, "Worker 3", "done", LGREEN))

# File pills
b.append(file_pill(538, 272, "need-otp.json", LYELLOW))
b.append(file_pill(538, 338, "otp.txt", LGREEN))
b.append(file_pill(538, 404, "result.json", WHITE))

b.append(line_arrow(502, 298, 536, 298))
b.append(line_arrow(536, 364, 502, 364))
b.append(line_arrow(502, 430, 536, 430))

# Right panel: Remote Server + Human
b.append(panel(770, 86, 390, 420, "REMOTE GROK BOT + HUMAN", INK))

b.append(box(798, 156, 334, 72, fill=LGREEN))
b.append('<text x="965" y="198" class="h" text-anchor="middle">Bot Inbox + Email Routine</text>')

b.append(box(798, 266, 334, 72, fill=LYELLOW))
b.append('<text x="965" y="308" class="h" text-anchor="middle">Human (SMS &amp; Decisions)</text>')

b.append(box(798, 376, 334, 96, fill=WHITE))
b.append('<text x="965" y="410" class="h" text-anchor="middle">Coordinator → Bitwarden</text>')
b.append(f'<rect x="828" y="426" width="274" height="30" rx="6" fill="{INK}"/>')
b.append(f'<text x="965" y="446" class="s" font-weight="700" text-anchor="middle" style="fill:{WHITE}">[Cleaned] · [Closed] · [Skip]</text>')

# Cross-panel arrows
b.append(ortho_arrow([(714, 298), (744, 298), (744, 184), (796, 184)], color=INK, dashed=True))
b.append(ortho_arrow([(796, 206), (758, 206), (758, 354), (714, 354)], color=GREEN))
b.append(ortho_arrow([(796, 302), (758, 302), (758, 374), (714, 374)], color=YELLOW))
b.append(line_arrow(714, 430, 796, 430, color=INK))

write(
    OUT,
    svg(
        1200,
        540,
        "Local Mac Workers and Remote Coordinator",
        "Local Mac runs parallel agents with Bitwarden CLI and task-template.md, exchanging need-otp.json, otp.txt, and result.json with the remote Grok Bot and human.",
        b,
    ),
)
