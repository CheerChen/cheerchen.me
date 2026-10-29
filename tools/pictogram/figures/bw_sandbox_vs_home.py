"""Bitwarden cleanup post: Cloud Sandbox (blocked & queued) vs Home Mac (parallel workers + coordinator)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pictogram import *  # noqa: E402,F403

OUT = "content/posts/bitwarden-cleanup-with-agents/sandbox-vs-home.svg"
G = 470


def stop_gate(x, y):
    """A red-and-white barrier arm blocking the path."""
    return (
        f'<rect x="{x - 10}" y="{y - 88}" width="20" height="88" rx="3" fill="{GRAY}" stroke="{INK}" stroke-width="3.5"/>'
        f'<rect x="{x - 108}" y="{y - 74}" width="112" height="16" rx="4" fill="{RED}" stroke="{INK}" stroke-width="3.5"/>'
        f'<rect x="{x - 84}" y="{y - 74}" width="22" height="16" fill="{WHITE}" stroke="{INK}" stroke-width="2"/>'
        f'<rect x="{x - 40}" y="{y - 74}" width="22" height="16" fill="{WHITE}" stroke="{INK}" stroke-width="2"/>'
        f'<circle cx="{x}" cy="{y - 66}" r="18" fill="{RED}" stroke="{INK}" stroke-width="3.5"/>'
        f'<rect x="{x - 10}" y="{y - 69}" width="20" height="6" rx="2" fill="{WHITE}"/>'
    )


def checklist_board(x, y):
    """A standing board showing [Cleaned] checkboxes."""
    s = signboard(x, y, 134, 102, legs=38)
    s += f'<text x="{x + 67}" y="{y + 26}" class="sign" text-anchor="middle">Bitwarden</text>'
    for i, done in enumerate((True, True, False)):
        ry = y + 40 + i * 19
        fill = GREEN if done else WHITE
        s += f'<rect x="{x + 18}" y="{ry}" width="13" height="13" rx="3" fill="{fill}" stroke="{INK}" stroke-width="2.5"/>'
        s += f'<rect x="{x + 38}" y="{ry + 3}" width="76" height="7" rx="3.5" fill="{INK if done else GRAY}"/>'
    return s


b = ['<text x="600" y="58" class="title" text-anchor="middle">Cloud Sandbox vs. Home Mac</text>']

# Left: Cloud Sandbox
b.append(panel(40, 86, 500, 430, "CLOUD SANDBOX", RED))
b.append(ground(70, 510, G))

for x, shirt, hair in ((98, YELLOW, "short"), (144, GREEN, "long"), (190, YELLOW, "cap")):
    b.append(person(x, G, "stand", shirt, hair=hair, scale=0.85))

b.append(person(288, G, "stressed", GREEN, hair="cap", scale=0.92))
b.append(spiky(270, 326, r=24))
b.append(stop_gate(418, G))
b.append(person(468, G, "stand", RED, flip=True, scale=0.92))

b.append(
    bubble(
        200,
        158,
        296,
        82,
        (456, 362),
        [
            ("Blocked!", "b"),
            ("Password / PII detected.", "t"),
        ],
    )
)

# Right: Home Mac
b.append(panel(580, 86, 580, 430, "HOME MAC", GREEN))
b.append(area(1048, G, 82))
b.append(ground(610, 1130, G))

b.append(checklist_board(612, 330))
b.append(person(782, G, "point", YELLOW, hair="long", scale=0.88))
b.append(
    bubble(
        700,
        178,
        196,
        58,
        (786, 362),
        [
            ("5 at a time!", "b"),
        ],
        first_y=36,
    )
)

b.append(trail(825, 845, 456))
b.append(person(882, G, "walk", GREEN, hair="cap", scale=0.85))
b.append(trail(916, 936, 444))
b.append(person(972, G, "run", GREEN, hair="cap", scale=0.85))
b.append(person(1056, G, "cheer", GREEN, hair="cap", scale=0.88))
b.append(sparkle(1012, 362, 10))
b.append(sparkle(1104, 350, 8))
b.append(highlight(992, 296, 126, 32))
b.append('<text x="1055" y="318" class="h" text-anchor="middle">[Cleaned] ×83</text>')

write(
    OUT,
    svg(
        1200,
        550,
        "Cloud Sandbox vs. Home Mac",
        "Left: in the cloud sandbox, a queue waits behind a single bot stopped at a barrier. Right: on the home Mac, a coordinator checks off Bitwarden while local agents run in parallel.",
        b,
    ),
)
