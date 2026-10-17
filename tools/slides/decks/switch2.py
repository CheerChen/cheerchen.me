"""Switch 2 GameChat post: talk slides redrawn in English.

python3 tools/slides/decks/switch2.py [slide-name ...] [--check]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "archdiagram"))
from slides import *  # noqa: E402,F403
from archdiagram import icon as aws_icon  # noqa: E402

POST = "content/posts/switch-2-gamechat-backend-sfu-dynamodb-consistency"


def p2p_vs_sfu():
    s = Slide("System architecture", "WebRTC: P2P vs SFU", page=6)
    s.subtitle("WebRTC carries real-time audio and video over UDP, in one of two topologies.")
    s.add(table(70, 236, [300, 380, 380], ["", "P2P", "SFU"],
                [["Media path", ["Direct between clients", "(lowest latency)"], ["Relayed by a server", "(adds relay latency)"]],
                 ["Streams per client", "Many", "Few"],
                 ["Encodes / decodes", "Many", "Few"]], size=22, label_col=True))
    return "slide-06-p2p-sfu.svg", s.svg(
        "WebRTC carries real-time audio and video over UDP in one of two topologies. P2P sends media directly between "
        "clients with the lowest latency, but each client handles many streams and many encodes and decodes. SFU "
        "relays media through a server, adding relay latency, but each client handles few streams and few encodes "
        "and decodes.")


def globe(cx, cy, r, user, server, rtt, color, others=()):
    """A plain globe with a Switch (user) linked to an SFU server (EC2 icon); `others` are faded SFUs elsewhere."""
    s = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#eaf4fb" stroke="{DIM}" stroke-width="1.5"/>'
    for rx in (r * 0.35, r * 0.7):
        s += f'<ellipse cx="{cx}" cy="{cy}" rx="{rx:.0f}" ry="{r}" fill="none" stroke="#c9d6e0" stroke-width="1.2"/>'
    for dy in (-r * 0.5, 0, r * 0.5):
        half = (r * r - dy * dy) ** 0.5
        s += f'<line x1="{cx - half:.0f}" y1="{cy + dy:.0f}" x2="{cx + half:.0f}" y2="{cy + dy:.0f}" stroke="#c9d6e0" stroke-width="1.2"/>'
    (ux, uy), (sx, sy) = user, server
    s += f'<line x1="{ux}" y1="{uy}" x2="{sx}" y2="{sy}" stroke="{color}" stroke-width="3" stroke-dasharray="7,5"/>'
    for ox, oy in others:
        s += f'<g opacity="0.35">{aws_icon("ec2", ox, oy, 30)}</g>'
    s += switch_badge(ux, uy, scale=0.5, mono=True) + aws_icon("ec2", sx, sy, 36)
    s += f'<text x="{cx}" y="{cy + r + 40}" font-size="26" font-weight="700" fill="{color}" text-anchor="middle">{rtt}</text>'
    return s


def multi_region():
    s = Slide("Multi-region operation", "Why run multiple regions?", page=9)
    y = s.bullet("Real-time calls need low-latency connections to the server", 210)
    s.bullet("SFU servers run in multiple AWS Regions; each user connects to the nearest", y)
    for x, label in ((110, "Single region"), (690, "Multi-region")):
        s.add(f'<rect x="{x}" y="296" width="400" height="290" rx="12" fill="{ROW_A}"/>'
              f'<text x="{x + 200}" y="330" font-size="20" font-weight="700" text-anchor="middle">{label}</text>')
    s.add(globe(310, 436, 92, (258, 446), (366, 396), "RTT 500 ms", RED))
    s.add(globe(890, 436, 92, (838, 446), (882, 426), "RTT 50 ms", BLUE, others=[(944, 380), (930, 492)]))
    s.add(f'<path d="M585,410 L615,440 L585,470" fill="none" stroke="{DIM}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
    s.add(f'<text x="{LEFT}" y="622" font-size="14" fill="{DIM}">Server locations and latency figures are illustrative, '
          f'not actual data centers or measurements.</text>')
    return "slide-09-multi-region.svg", s.svg(
        "Real-time calls need low-latency server connections, so SFU servers run in multiple AWS Regions and each "
        "user connects to the nearest one. With a single region, a Switch far from the only SFU server sees a round "
        "trip of about 500 ms; with SFU servers in several regions, the nearest one cuts it to about 50 ms. The "
        "numbers are illustrative.")


def cost_design():
    s = Slide("Design priorities", "Designing for cost efficiency", page=19)
    s.bullet("Key-value store", 212)
    # the client reads cheaply and writes expensively
    s.add(person(180, 382))
    s.add(block_arrow(470, 280, 352, "#cfe9f6", outline=BLUE, thick=12))
    s.add(block_arrow(280, 470, 424, ACCENT, thick=14))
    s.add(f'<text x="375" y="330" font-size="18" fill="{DIM}" text-anchor="middle">read</text>')
    s.add(f'<text x="375" y="402" font-size="18" fill="{DIM}" text-anchor="middle">write</text>')
    s.add(f'<text x="375" y="476" font-size="22" font-weight="700" fill="{ACCENT}" text-anchor="middle">Writes cost more</text>')
    s.add(table(530, 248, [200, 170, 200], ["Partition Key", "Sort Key", "Value"],
                [["Key01", 0, "Value01"], ["Key02", 0, "Value02"], ["Key03", 0, "Value03"], ["Key03", 1, "Value04"]]))
    s.bullet("Consumed capacity units vary with access type and item size", 582)
    return "slide-19-cost-design.svg", s.svg(
        "DynamoDB is a key-value store. A user reads from and writes to a table of partition keys, sort keys and "
        "values; the write arrow is marked as the more expensive one. Consumed capacity units vary with access "
        "type and item size.")


def usecase_driven():
    s = Slide("Design priorities", "Use-case-driven design", page=20)
    s.subtitle("The approach taken this time")
    s.add(step_flow(70, 250, 1060, ["Draft a provisional RDB data model", "Design the APIs", "List the use cases",
                                     "Derive access patterns from the use cases",
                                     "Choose keys and facets to fit the access patterns"], highlight=4))
    s.add(f'<text x="600" y="530" font-size="22" font-weight="700" text-anchor="middle">'
          f'Know how the system reads before deciding how it stores.</text>')
    return "slide-20-usecase-driven.svg", s.svg(
        "Five steps in a row: draft a provisional RDB data model, design the APIs, list the use cases, derive access "
        "patterns from the use cases, and choose keys and facets to fit the access patterns. Know how the system "
        "reads before deciding how it stores.")


def state_circle(cx, cy, r, label, current=False):
    if current:
        return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#e7f3fb" stroke="{BLUE}" stroke-width="4"/>'
                f'<text x="{cx}" y="{cy + 8}" font-size="22" font-weight="700" text-anchor="middle">{label}</text>')
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#ffffff" stroke="#b9c0c8" stroke-width="3" stroke-dasharray="9,7"/>'
            f'<text x="{cx}" y="{cy + 8}" font-size="22" fill="{DIM}" text-anchor="middle">{label}</text>')


def chevron(x, y):
    return (f'<path d="M{x - 9},{y - 16} L{x + 7},{y} L{x - 9},{y + 16}" fill="none" stroke="{DIM}" stroke-width="4" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def state_api_race():
    s = Slide("State transitions and eventual consistency", "Server state and API access", page=26)
    cy, r = 452, 80
    s.add(state_circle(300, cy, r, "Reserved"))
    s.add(chevron(450, cy))
    s.add(state_circle(600, cy, r, "Authenticated", current=True))
    s.add(chevron(750, cy))
    s.add(state_circle(900, cy, r, "Connected"))
    s.add(f'<text x="600" y="352" font-size="18" font-weight="700" fill="{BLUE}" text-anchor="middle">server state</text>')
    # the client already shows the chat screen
    s.add(f'<rect x="800" y="176" width="200" height="112" rx="8" fill="#ffffff" stroke="{INK}" stroke-width="2.5"/>'
          f'<rect x="812" y="188" width="176" height="56" rx="4" fill="#dbe9f4"/>'
          + "".join(f'<rect x="{812 + i * 46}" y="252" width="38" height="26" rx="3" fill="{ROW_B}"/>' for i in range(4))
          + f'<line x1="900" y1="288" x2="900" y2="302" stroke="{INK}" stroke-width="2.5"/>')
    s.add(switch_badge(900, 324, scale=0.8, mono=True))
    s.add(f'<text x="782" y="236" font-size="18" font-weight="700" fill="{INK}" text-anchor="end">client UI:</text>'
          f'<text x="782" y="260" font-size="18" fill="{DIM}" text-anchor="end">already in the chat</text>')
    s.add(f'<rect x="790" y="552" width="220" height="44" rx="8" fill="{RED}"/>'
          f'<text x="900" y="581" font-size="20" font-weight="700" fill="#ffffff" text-anchor="middle">API access denied!</text>')
    s.add(f'<line x1="900" y1="532" x2="900" y2="552" stroke="{RED}" stroke-width="3"/>')
    return "slide-26-state-api-race.svg", s.svg(
        "Three states in order: reserved, authenticated, connected. The server state is authenticated, while the "
        "client UI already shows the chat screen as if connected. An API call that needs the connected state is "
        "denied.")


def consistent_read():
    s = Slide("Read inconsistency on extra invites", "Consistent Read", page=27)
    y = s.bullet("Setting it gives strongly consistent reads", 220, max_x=600)
    y = s.bullet("Always consistent, but consumes more capacity units", y, max_x=600)
    y = s.bullet("This time, design work made eventual consistency acceptable", y, max_x=600)
    s.add(f'<text x="{LEFT + 40}" y="{y + 12:.0f}" font-size="26" font-weight="700" fill="{RED}" '
          f'text-decoration="underline">so it was not adopted</text>')
    # DynamoDB replicates across three AZs; only the strong read is pinned to the leader copy
    s.add(f'<rect x="650" y="350" width="470" height="210" rx="8" fill="none" stroke="{DIM}" stroke-width="1.5" stroke-dasharray="6,5"/>')
    s.add(aws_icon("dynamodb", 650, 350, 36))
    s.add(aws_icon("fargate", 885, 240, 56))
    azs = [(735, "AZ1"), (885, "AZ2"), (1035, "AZ3")]
    for x, name in azs:
        s.add(f'<text x="{x}" y="424" font-size="17" fill="{DIM}" text-anchor="middle">{name}</text>')
        s.add(aws_icon("ddb-table", x, 474, 56))
    for (x1, _), (x2, _) in zip(azs, azs[1:]):
        s.add(f'<line x1="{x1 + 40}" y1="474" x2="{x2 - 40}" y2="474" stroke="{DIM}" stroke-width="2"/>')
    s.add(f'<path d="M735,512 Q885,560 1035,512" fill="none" stroke="{DIM}" stroke-width="2"/>')
    s.add(f'<line x1="905" y1="270" x2="1003" y2="402" stroke="{DIM}" stroke-width="2"/>')
    s.add(f'<line x1="885" y1="270" x2="885" y2="402" stroke="{DIM}" stroke-width="2"/>')
    s.add(f'<line x1="860" y1="268" x2="775" y2="402" stroke="{RED}" stroke-width="3.5"/>')
    s.add(f'<line x1="848" y1="262" x2="762" y2="398" stroke="{RED}" stroke-width="3.5"/>')
    s.add(f'<text x="790" y="300" font-size="18" font-weight="700" fill="{RED}" text-anchor="end">strongly consistent</text>')
    return "slide-27-consistent-read.svg", s.svg(
        "Consistent Read gives strongly consistent reads: always consistent, but it consumes more capacity units. "
        "The diagram shows an application reading DynamoDB, which replicates across three Availability Zones; the "
        "strongly consistent read goes to AZ1. This time, design work made eventual consistency acceptable, so "
        "Consistent Read was not adopted.")


def flow_box(x, y, w, h, text, strong=False):
    stroke, fill = (BLUE, "#e7f3fb") if strong else ("#b9c0c8", "#ffffff")
    weight = ' font-weight="700"' if strong else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="{3 if strong else 2}"/>'
            f'<text x="{x + w / 2}" y="{y + h / 2 + 8}" font-size="22"{weight} text-anchor="middle">{esc(text)}</text>')


def plus(x, y):
    return (f'<path d="M{x - 14},{y} H{x + 14} M{x},{y - 14} V{y + 14}" stroke="{DIM}" stroke-width="4.5" '
            f'stroke-linecap="round"/>')


def invite_inconsistency():
    s = Slide("Read inconsistency on extra invites", "Handling the read inconsistency", page=29)
    xs, w, h = (110, 440, 770), 260, 70
    s.bullet("A normal invite round-trips through the client", 220)
    for x, text in zip(xs, ("Friend selection", "Join processing", "Send notification")):
        s.add(flow_box(x, 250, w, h, text))
    s.add(chevron(405, 285) + chevron(735, 285))
    s.bullet("An extra invite completes inside the server", 400)
    for x, text in zip(xs, ("Chat in progress", "Friend selection", "Send notification")):
        s.add(flow_box(x, 430, w, h, text, strong=True))
    s.add(plus(405, 465) + chevron(735, 465))
    s.add(f'<text x="110" y="550" font-size="18" fill="{DIM}">The member list comes from the chat the initiator is already in, '
          f'so the server skips a possibly stale read.</text>')
    return "slide-29-invite-inconsistency.svg", s.svg(
        "Two flows. A normal invite round-trips through the client: friend selection, join processing, send "
        "notification. An extra invite completes inside the server: the chat in progress plus friend selection, then "
        "send notification. The member list comes from the chat the initiator is already in, so the server skips a "
        "possibly stale read.")


def lesson_card(x, y, w, h, title, items, color):
    clip = f"card-{x}-{y}"
    s = (f'<clipPath id="{clip}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12"/></clipPath>'
         f'<g clip-path="url(#{clip})"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{ROW_A}"/>'
         f'<rect x="{x}" y="{y}" width="8" height="{h}" fill="{color}"/></g>'
         f'<text x="{x + 32}" y="{y + 44}" font-size="24" font-weight="700" fill="{color}">{esc(title)}</text>')
    ty = y + 88
    for item in items:
        lines = wrap(item, 20, w - 76)
        s += f'<circle cx="{x + 40}" cy="{ty - 7}" r="4" fill="{color}"/>'
        for i, line in enumerate(lines):
            s += f'<text x="{x + 56}" y="{ty + i * 28}" font-size="20">{esc(line)}</text>'
        ty += len(lines) * 28 + 18
    return s


def dynamodb_reflection():
    s = Slide("Lessons learned", "What building on DynamoDB taught us", page=30)
    s.add(lesson_card(70, 196, 505, 236, "What worked",
                      ["Designing for DynamoDB from the start delivered the expected performance and scalability "
                       "from day one"], BLUE))
    s.add(lesson_card(625, 196, 505, 236, "Watch out",
                      ["When use cases change, processing order or displayed information shifts, a redesign may be needed",
                       "It does not suit a phase where the UX still needs trial and error"], RED))
    s.add(f'<rect x="70" y="470" width="1060" height="58" rx="10" fill="#fff6d6"/>'
          f'<text x="600" y="507" font-size="23" font-weight="700" text-anchor="middle">'
          f'Choose the database that fits the system and how it is being built.</text>')
    return "slide-30-DynamoDB-reflection.svg", s.svg(
        "What worked: designing for DynamoDB from the start delivered the expected performance and scalability from "
        "day one. Watch out: when use cases change, processing order or displayed information shifts, a redesign may "
        "be needed, and DynamoDB does not suit a phase where the UX still needs trial and error. Choose the database "
        "that fits the system and how it is being built.")


FRAME_CSS = """<style>
  .fr{opacity:0;animation:12s linear infinite}
  .fr-0{animation-name:fr0}.fr-1{animation-name:fr1}.fr-2{animation-name:fr2}.fr-3{animation-name:fr3}
  @keyframes fr0{0%,22%{opacity:1}25%,100%{opacity:0}}
  @keyframes fr1{0%,22%{opacity:0}25%,47%{opacity:1}50%,100%{opacity:0}}
  @keyframes fr2{0%,47%{opacity:0}50%,72%{opacity:1}75%,100%{opacity:0}}
  @keyframes fr3{0%,72%{opacity:0}75%,97%{opacity:1}100%{opacity:0}}
  @media (prefers-reduced-motion:reduce){.fr{animation:none}.fr-3{opacity:1}}
</style>"""


def arrow_line(pts, color=INK, label=None, label_at=None, anchor="start"):
    """An orthogonal connector with an arrowhead at the last point, optionally labelled."""
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    ux, uy = (x2 > x1) - (x2 < x1), (y2 > y1) - (y2 < y1)
    head = [(x2, y2), (x2 - ux * 12 - uy * 6, y2 - uy * 12 + ux * 6), (x2 - ux * 12 + uy * 6, y2 - uy * 12 - ux * 6)]
    s = (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>'
         f'<polygon points="{" ".join(f"{x},{y}" for x, y in head)}" fill="{color}"/>')
    if label:
        lx, ly = label_at
        s += f'<text x="{lx}" y="{ly}" font-size="18" fill="{color}" text-anchor="{anchor}">{esc(label)}</text>'
    return s


def screen(x, y, w, h, kind):
    """A simplified Switch screen: a friend list, a chat with video tiles, or a notification."""
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#ffffff" stroke="{INK}" stroke-width="2"/>'
    if kind == "friends":
        for i in range(3):
            s += (f'<circle cx="{x + 22}" cy="{y + 20 + i * 22}" r="7" fill="#c9d6e0"/>'
                  f'<rect x="{x + 36}" y="{y + 16 + i * 22}" width="{w * 0.5:.0f}" height="8" rx="4" fill="{ROW_B}"/>')
    elif kind == "chat":
        s += f'<rect x="{x + 8}" y="{y + 8}" width="{w - 16}" height="{h * 0.5:.0f}" rx="3" fill="#dbe9f4"/>'
        tw = (w - 16 - 9) / 4
        for i in range(4):
            s += f'<rect x="{x + 8 + i * (tw + 3):.0f}" y="{y + h * 0.5 + 14:.0f}" width="{tw:.0f}" height="{h * 0.3:.0f}" rx="3" fill="{ROW_B}"/>'
    else:
        s += (f'<rect x="{x + 10}" y="{y + 12}" width="{w - 20}" height="26" rx="13" fill="#e7f3fb" stroke="{BLUE}" stroke-width="1.5"/>'
              f'<circle cx="{x + 24}" cy="{y + 25}" r="6" fill="{BLUE}"/>'
              f'<rect x="{x + 36}" y="{y + 21}" width="{w * 0.45:.0f}" height="8" rx="4" fill="#c9d6e0"/>')
    return s


def start_flow():
    s = Slide("", "GameChat start flow", heading=False)
    s.add(FRAME_CSS)
    Y, R = 330, 64
    nodes = {"friends": (150, "box", "Friend selection"), "reserved": (370, "circle", "Reserved"),
             "auth": (560, "circle", "Authenticated"), "connected": (750, "circle", "Connected"),
             "notify": (968, "box", "Send notification")}

    def node(key, style):
        cx, shape, label = nodes[key]
        stroke, fill, dash, width, weight = {
            "plain": (INK, "#ffffff", "", 2, ""),
            "idle": ("#b9c0c8", "#ffffff", ' stroke-dasharray="8,6"', 2.5, ""),
            "on": (BLUE, "#e7f3fb", "", 4, ' font-weight="700"'),
        }[style]
        tf = "" if style != "idle" else f' fill="{DIM}"'
        if shape == "box":
            g = f'<rect x="{cx - 90}" y="{Y - 34}" width="180" height="68" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="{width}"{dash}/>'
        else:
            g = f'<circle cx="{cx}" cy="{Y}" r="{R}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"{dash}/>'
        size = 18 if label == "Authenticated" else 20
        return g + f'<text x="{cx}" y="{Y + 7}" font-size="{size}"{weight}{tf} text-anchor="middle">{label}</text>'

    base = "".join(chevron(x, Y) for x in (264, 467, 655, 856))
    base += f'<rect x="292" y="248" width="536" height="164" rx="16" fill="none" stroke="{INK}" stroke-width="2"/>'
    base += (f'<rect x="490" y="398" width="140" height="30" rx="8" fill="#ffffff" stroke="{INK}" stroke-width="2"/>'
             f'<text x="560" y="419" font-size="17" font-weight="700" text-anchor="middle">Group server</text>')
    s.add(base)

    def frame(i, tag, title, body, on=()):
        """One animation frame: heading, every node (highlighted ones in `on`), extras, and its page number."""
        nodes_svg = "".join(node(k, "on" if k in on else ("plain" if i == 0 else "idle")) for k in nodes)
        s.add(f'<g class="fr fr-{i}" data-frame="{i}">{Slide.heading(tag, title)}{nodes_svg}{body}</g>')
        s.overlay.append(f'<g class="fr fr-{i}" data-frame="{i}"><text x="{W - 76}" y="{H - 50}" font-size="17" '
                         f'font-weight="700" text-anchor="middle">{22 + i}</text></g>')

    sw_l, sw_r = (150, 470), (965, 470)
    host = switch_badge(*sw_l, scale=0.9, mono=True)
    sfu = (aws_icon("ec2", 560, 540, 44)
           + f'<text x="560" y="586" font-size="17" font-weight="700" text-anchor="middle">SFU server</text>')

    frame(0, "Development case study", "GameChat start flow", "")
    frame(1, "GameChat start flow", "From friend selection to a chat reservation",
          host + screen(80, 498, 140, 82, "friends")
          + arrow_line([(196, 470), (540, 470), (540, 430)], BLUE, "sends member info", (240, 458)), on=("friends",))
    frame(2, "GameChat start flow", "Changing state to connected",
          host + screen(80, 498, 140, 82, "chat") + sfu
          + arrow_line([(560, 514), (560, 430)], BLUE, "connection established", (574, 490))
          + arrow_line([(500, 428), (500, 460), (196, 460)], INK), on=("auth",))
    frame(3, "GameChat start flow", "Sending notifications asynchronously",
          host + screen(80, 498, 140, 82, "chat") + sfu
          + switch_badge(*sw_r, scale=0.9, mono=True) + screen(895, 498, 140, 82, "notice")
          + arrow_line([(560, 514), (560, 430)], INK, "reports the connection", (574, 490))
          + arrow_line([(500, 428), (500, 460), (196, 460)], INK, "chat connected", (240, 450))
          + arrow_line([(965, 364), (965, 446)], BLUE, "invitee is notified", (978, 412)), on=("connected", "notify"))
    return "slide-22-25-state-machine.svg", s.svg(
        "Animated, four frames, slides 22 to 25. The GameChat start flow runs friend selection, reserved, "
        "authenticated, connected, send notification; the group server owns the three middle states. Frame 2: the "
        "Switch 2 sends the member info to the group server. Frame 3: the SFU server reports the established "
        "connection and the host's Switch 2 enters the chat. Frame 4: the state is connected, the host's chat is "
        "connected, and the invitee is notified asynchronously.")


def denormalization():
    s = Slide("Design priorities", "Denormalization", page=21)
    s.add(table(570, 176, [190, 170, 200], ["Partition Key", "Value", "List"],
                [["Key01", "Value01", ["User01 - Mario", "User02 - Bowser", "User03 - Yoshi"]],
                 ["Key02", "Value02", ["User01 - Mario", "User02 - Bowser"]]]))
    y = s.bullet("Skip normalization: keep lists and similar data inside the item as-is", 480)
    s.bullet("Shape items so a single query returns everything you need", y)
    return "slide-21-denormalization.svg", s.svg(
        "A table whose items hold a list of users inline: Key01 lists Mario, Bowser and Yoshi, Key02 lists Mario and "
        "Bowser. Lists are kept inside the item instead of being normalized, so one query returns everything needed.")


SLIDES = {"p2p-vs-sfu": p2p_vs_sfu, "multi-region": multi_region, "state-api-race": state_api_race, "consistent-read": consistent_read, "cost-design": cost_design, "start-flow": start_flow, "invite-inconsistency": invite_inconsistency, "dynamodb-reflection": dynamodb_reflection, "usecase-driven": usecase_driven, "denormalization": denormalization}

if __name__ == "__main__":
    names = [a for a in sys.argv[1:] if not a.startswith("--")] or list(SLIDES)
    failed = False
    for name in names:
        filename, content = SLIDES[name]()
        out = f"{POST}/{filename}"
        write(out, content)
        if "--check" in sys.argv:
            problems = check(out)
            for p in problems:
                print(f"  {name}: {p}")
            failed |= bool(problems)
    sys.exit(1 if failed else 0)
