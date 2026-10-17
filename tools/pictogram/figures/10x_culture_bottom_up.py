"""10x post: pushing a culture top-down versus growing it bottom-up."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pictogram import *  # noqa: E402,F403

OUT = "content/posts/10x-innovation-culture-program-ask-googler/culture-bottom-up.svg"


def lightbulb(cx, cy):
    return (f'<circle cx="{cx}" cy="{cy}" r="13" fill="{YELLOW}" stroke="{INK}" stroke-width="3"/>'
            f'<rect x="{cx - 6}" y="{cy + 11}" width="12" height="8" rx="2" fill="{GRAY}" stroke="{INK}" stroke-width="3"/>'
            + "".join(f'<line x1="{cx + dx * 18}" y1="{cy + dy * 18}" x2="{cx + dx * 25}" y2="{cy + dy * 25}" '
                      f'stroke="{INK}" stroke-width="3" stroke-linecap="round"/>'
                      for dx, dy in ((-1, 0), (1, 0), (-0.7, -0.7), (0.7, -0.7), (0, -1))))


def step_label(x, y, n, text):
    return number_badge(x + 15, y - 6, n) + f'<text x="{x + 38}" y="{y}" class="h">{text}</text>'


b = ['<text x="600" y="60" class="title" text-anchor="middle">Grow the culture bottom-up</text>']
G = 500

# Left: top-down
b.append(panel(40, 90, 400, 520, "TOP-DOWN", RED))
b.append(ground(70, 410, G))
b.append(f'<rect x="88" y="440" width="84" height="60" rx="4" fill="{GRAY}" stroke="{INK}" stroke-width="3.5"/>')
b.append(person(130, 440, "megaphone", GREEN))
mx, my = hand(130, 440, "megaphone")
b.append(megaphone(mx - 2, my))
b.append(bubble(70, 210, 270, 60, (138, 318), [("Everyone, do it this way!", "t")], first_y=37))
for x, shirt, hair in ((270, YELLOW, "long"), (325, GREEN, "cap"), (380, YELLOW, "short")):
    b.append(person(x, G, "stand", shirt, hair=hair, flip=True, scale=0.85))
b.append(spiky(330, 350))
b.append('<text x="240" y="548" class="h" text-anchor="middle">The leader decides, everyone executes</text>')
b.append('<text x="240" y="576" class="s-dim" text-anchor="middle">Quick to announce, rarely sticks</text>')

# Right: bottom-up
b.append(panel(480, 90, 680, 520, "BOTTOM-UP", GREEN))
b.append(highlight(510, 142, 620, 40))
b.append('<text x="820" y="169" class="b" text-anchor="middle">Start from Purpose: why are we doing this?</text>')
b.append(ground(510, 1130, G))

# 1. pull in volunteers
b.append(signboard(510, 384, 110, 76, legs=40))
b.append('<text x="565" y="417" class="sign" text-anchor="middle">Volunteers</text>')
b.append('<text x="565" y="440" class="sign" text-anchor="middle">wanted!</text>')
b.append(person(650, G, "raise", YELLOW, hair="long", scale=0.85))
b.append(person(690, G, "raise", GREEN, hair="cap", scale=0.85))
b.append(step_label(510, 548, 1, "Pull in volunteers"))

# 2. create the trigger
b.append(f'<rect x="812" y="478" width="80" height="22" rx="3" fill="{LGREEN}" stroke="{INK}" stroke-width="3.5"/>')
b.append(person(760, G, "point", GREEN, scale=0.85))
b.append(person(852, 478, "stand", YELLOW, scale=0.85))
b.append(lightbulb(852, 345))
b.append(bubble(722, 280, 150, 46, (764, 394), [("Give it a try!", "s")], first_y=29))
b.append(step_label(740, 548, 2, "Create the trigger"))

# 3. amplify the wins
b.append(person(990, G, "megaphone", GREEN, scale=0.85))
mx, my = hand(990, G, "megaphone", scale=0.85)
b.append(megaphone(mx - 2, my))
b.append(person(1095, G, "cheer", YELLOW, hair="long", scale=0.85))
b.append(sparkle(1060, 395, 9))
b.append(sparkle(1130, 380, 7))
b.append(bubble(942, 280, 186, 46, (994, 394), [("Look what they did!", "s")], first_y=29))
b.append(step_label(950, 548, 3, "Amplify the wins"))

b.append('<text x="600" y="660" class="cap" text-anchor="middle">Be a catalyst and an amplifier, not a commander.</text>')

write(OUT, svg(1200, 700, "Grow the culture bottom-up",
               "Left: a leader on a podium with a megaphone orders everyone to do it one way, and the team goes quiet. "
               "Right: under a banner asking what the purpose is, a leader recruits volunteers, gives one of them a "
               "chance to try an idea, and then uses a megaphone to celebrate what they did.", b))
