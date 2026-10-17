"""10x post: how TGIF questions go from a vote to a live answer."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pictogram import *  # noqa: E402,F403

OUT = "content/posts/10x-innovation-culture-program-ask-googler/tgif.svg"
G = 470


def question_card(x, y, votes, line_w):
    return (f'<rect x="{x}" y="{y}" width="190" height="52" rx="10" fill="{WHITE}" stroke="{INK}" stroke-width="3"/>'
            f'<circle cx="{x + 24}" cy="{y + 26}" r="13" fill="{YELLOW}" stroke="{INK}" stroke-width="3"/>'
            f'<text x="{x + 24}" y="{y + 32}" class="h" text-anchor="middle">?</text>'
            f'<rect x="{x + 46}" y="{y + 16}" width="{line_w}" height="8" rx="4" fill="{GRAY}"/>'
            f'<rect x="{x + 46}" y="{y + 30}" width="{line_w * 0.6:.0f}" height="8" rx="4" fill="{GRAY}"/>'
            f'<text x="{x + 178}" y="{y + 32}" class="s" font-weight="700" text-anchor="end">{votes}</text>')


def phone(x, y, w, h):
    """A phone standing upright: ink bezel, white screen, notch and home bar."""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="28" fill="{INK}"/>'
            f'<rect x="{x + 10}" y="{y + 10}" width="{w - 20}" height="{h - 20}" rx="20" fill="{WHITE}"/>'
            f'<rect x="{x + w / 2 - 22}" y="{y + 18}" width="44" height="10" rx="5" fill="{INK}"/>'
            f'<rect x="{x + w / 2 - 30}" y="{y + h - 24}" width="60" height="5" rx="2.5" fill="{INK}"/>')


def vote_row(x, y, top, votes, line_w):
    """One entry in the voting app: upvote arrow and count on the left, question text as grey lines."""
    return (f'<rect x="{x}" y="{y}" width="136" height="50" rx="10" fill="{LGREEN if top else WHITE}" stroke="{INK}" stroke-width="2.5"/>'
            f'<path d="M{x + 22},{y + 10} l9,11 h-18 z" fill="{GREEN if top else GRAY}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>'
            f'<text x="{x + 22}" y="{y + 40}" font-size="13" font-weight="700" text-anchor="middle">{votes}</text>'
            f'<rect x="{x + 46}" y="{y + 15}" width="{line_w}" height="7" rx="3.5" fill="{GRAY}"/>'
            f'<rect x="{x + 46}" y="{y + 29}" width="{line_w * 0.65:.0f}" height="7" rx="3.5" fill="{GRAY}"/>')


def step_label(cx, y, n, text):
    return (number_badge(cx - 9.5 * len(text) / 2 - 26, y - 6, n)
            + f'<text x="{cx}" y="{y}" class="h" text-anchor="middle">{text}</text>')


b = ['<text x="600" y="60" class="title" text-anchor="middle">TGIF: vote, rank, answer live</text>']
b.append(panel(40, 90, 1120, 470))
b.append(ground(70, 1130, G))

# 1. vote ahead
for i, (votes, lw) in enumerate(((128, 90), (96, 76), (41, 84))):
    b.append(question_card(70, 150 + i * 70, votes, lw))
b.append(person(300, G, "raise", YELLOW, hair="long", scale=0.85))
b.append(person(350, G, "raise", GREEN, hair="cap", scale=0.85))
b.append(bubble(290, 290, 56, 40, (306, 362), [("+1", "h")], first_y=27))
b.append(step_label(215, 520, 1, "Vote ahead"))

b.append(arrow(400, 300, 456, 300))

# 2. top questions rise
b.append(phone(510, 120, 180, 340))
b.append('<text x="600" y="176" class="h" text-anchor="middle">Top questions</text>')
for i, (votes, lw) in enumerate(((128, 70), (96, 58), (41, 64), (23, 50))):
    b.append(vote_row(532, 192 + i * 60, i == 0, votes, lw))
b.append(step_label(600, 520, 2, "Top-voted rise"))

b.append(arrow(744, 300, 800, 300))

# 3. answered live on stage
b.append(f'<rect x="830" y="420" width="300" height="50" rx="4" fill="{LGREEN}" stroke="{INK}" stroke-width="3.5"/>')
b.append(person(905, 420, "mic", GREEN))
mx, my = hand(905, 420, "mic")
b.append(mic(mx + 2, my - 4))
b.append(person(1000, 420, "stand", YELLOW, hair="long"))
b.append(sparkle(1060, 330, 9))
b.append(bubble(840, 150, 290, 92, (900, 296), [("Great question.", "h"), ("Here's the honest answer...", "t")], first_y=36))
b.append(step_label(980, 520, 3, "Execs answer live"))

b.append('<text x="600" y="600" class="cap" text-anchor="middle">Asking is all upside. Feedback is a gift.</text>')

write(OUT, svg(1200, 630, "TGIF: vote, rank, answer live",
               "Three steps left to right. Employees vote on question cards ahead of time; a voting app on a phone ranks the "
               "top-voted questions; executives on stage answer them live with a microphone.", b))
