"""Building blocks for AWS architecture diagrams laid out by hand.

Icons come from the official AWS Architecture Icons package (see aws-icons/NOTICE.md).
Every function returns an SVG fragment string; a figure script concatenates them
and passes the result to `write()`.
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

INK = "#232f3e"          # AWS squid ink: text, AWS Cloud border, arrows
DIM = "#5f6b7a"
REGION = "#00a4a6"       # AWS Region group colour
VPC = "#8c4fff"          # AWS VPC group colour
ACCOUNT = "#e7157b"      # AWS Account group colour
RED = "#d13212"          # highlights: the selected / synchronous path
GREEN = "#1d8102"        # highlights: the asynchronous path
FONT = "'Amazon Ember',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"

# Light role bands, matching the soft fills on the original slides.
BAND = {"purple": "#f1eef8", "blue": "#e3eff9", "pink": "#f6edf5", "gray": "#f2f3f3"}

ICONS = {
    "cloudfront": "Arch_Amazon-CloudFront_48",
    "alb": "Arch_Elastic-Load-Balancing_48",
    "fargate": "Arch_AWS-Fargate_48",
    "sqs": "Arch_Amazon-Simple-Queue-Service_48",
    "apigw": "Arch_Amazon-API-Gateway_48",
    "dynamodb": "Arch_Amazon-DynamoDB_48",
    "ec2": "Arch_Amazon-EC2_48",
    "transcribe": "Arch_Amazon-Transcribe_48",
    "xray": "Arch_AWS-X-Ray_48",
    "document": "Res_Document_48_Light",
    "source-code": "Res_Source-Code_48_Light",
    "json": "Res_JSON-Script_48_Light",
    "ddb-table": "Res_Amazon-DynamoDB_Standard-Access-Table-Class_48",
    "sdk": "Res_SDK_48_Light",
    "app": "Res_Generic-Application_48_Light",
    "aws-cloud": "AWS-Cloud-logo_32",
    "region": "Region_32",
    "vpc": "Virtual-private-cloud-VPC_32",
    "account": "AWS-Account_32",
    "lambda": "Arch_AWS-Lambda_48",
    "ecs": "Arch_Amazon-Elastic-Container-Service_48",
    "elasticache": "Arch_Amazon-ElastiCache_48",
    "rds": "Arch_Amazon-RDS_48",
    "ivs": "Arch_Amazon-Interactive-Video-Service_48",
    "users": "Res_Users_48_Light",
}

STYLE = f"""
    text{{font-family:{FONT}}}
    text:where(:not([fill])){{fill:{INK}}}
    .title{{font-size:26px;font-weight:700}}
    .lbl{{font-size:13px}}
    .grp{{font-size:14px;font-weight:600}}
    .role{{font-size:14px;font-weight:700}}
    .note{{font-size:13px;fill:{DIM}}}
"""


def _icon_body(key):
    """Inner markup of an icon file, with ids and titles dropped so it can be inlined many times."""
    raw = (HERE / "aws-icons" / f"{ICONS[key]}.svg").read_text()
    vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', raw)
    body = raw[raw.index(">", raw.index("<svg")) + 1:raw.rindex("</svg>")]
    body = re.sub(r"<title>.*?</title>", "", body, flags=re.S)
    body = re.sub(r'\s+id="[^"]*"', "", body)
    return int(vb.group(1)), " ".join(body.split())


def icon(key, cx, cy, size=48, label=None):
    """A service icon centred on (cx, cy); label is one string or a list of lines under it."""
    vb, body = _icon_body(key)
    s = size / vb
    out = f'<g transform="translate({cx - size / 2},{cy - size / 2}) scale({s:.4f})">{body}</g>'
    if label:
        lines = [label] if isinstance(label, str) else label
        for i, line in enumerate(lines):
            out += f'<text x="{cx}" y="{cy + size / 2 + 18 + i * 16}" class="lbl" text-anchor="middle">{line}</text>'
    return out


def group(x, y, w, h, kind, label):
    """AWS group box. kind: "cloud" (solid ink), "region" (dashed teal), "vpc" (solid purple) or "account" (solid pink)."""
    color, dash, glyph = {"cloud": (INK, "", "aws-cloud"), "region": (REGION, ' stroke-dasharray="6,4"', "region"),
                          "vpc": (VPC, "", "vpc"), "account": (ACCOUNT, "", "account")}[kind]
    border = f'stroke="{color}" stroke-width="1.5"{dash}'
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" {border}/>'
            + icon(glyph, x + 14, y + 14, 28)
            + f'<text x="{x + 36}" y="{y + 19}" class="grp" style="fill:{color}">{label}</text>')


def service_box(x, y, w, h, key, label):
    """A dashed box standing for one service's insides, its icon on the top-left corner."""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="none" stroke="{DIM}" stroke-width="1.5" stroke-dasharray="6,5"/>'
            + icon(key, x, y, 36)
            + f'<text x="{x + 30}" y="{y + 22}" class="grp">{label}</text>')


def box(x, y, w, h, lines, fill="#ffffff"):
    """A plain labelled rectangle for something that has no AWS icon (a stage, an environment)."""
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{INK}" stroke-width="1.5"/>'
    lines = [lines] if isinstance(lines, str) else lines
    top = y + h / 2 - (len(lines) - 1) * 9 + 5
    for i, line in enumerate(lines):
        s += f'<text x="{x + w / 2}" y="{top + i * 18:.0f}" class="lbl" text-anchor="middle">{line}</text>'
    return s


def band(x, y, w, h, color):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{BAND[color]}"/>'


def role(x, y, text):
    """A rounded label naming a component's role, e.g. "Group server"."""
    w = 9 * len(text) + 28
    return (f'<rect x="{x}" y="{y}" width="{w}" height="30" rx="8" fill="#ffffff" stroke="{INK}" stroke-width="1.5"/>'
            f'<text x="{x + w / 2}" y="{y + 20}" class="role" text-anchor="middle">{text}</text>')


def switch(cx, cy, label=True):
    """A plain Switch-shaped glyph (screen with a Joy-Con on each side), optionally labelled below."""
    s = (f'<rect x="{cx - 26}" y="{cy - 18}" width="52" height="36" rx="3" fill="#ffffff" stroke="{INK}" stroke-width="2.5"/>'
         f'<rect x="{cx - 40}" y="{cy - 20}" width="14" height="40" rx="7" fill="{INK}"/>'
         f'<rect x="{cx + 26}" y="{cy - 20}" width="14" height="40" rx="7" fill="{INK}"/>'
         f'<circle cx="{cx - 33}" cy="{cy - 8}" r="2.5" fill="#ffffff"/><circle cx="{cx + 33}" cy="{cy + 6}" r="2.5" fill="#ffffff"/>')
    if label:
        s += (f'<text x="{cx}" y="{cy + 42}" class="lbl" text-anchor="middle">Nintendo</text>'
              f'<text x="{cx}" y="{cy + 58}" class="lbl" text-anchor="middle">Switch 2</text>')
    return s


def step(cx, cy, n, color=INK):
    """A numbered circle for ordered flows."""
    return (f'<circle cx="{cx}" cy="{cy}" r="11" fill="{color}"/>'
            f'<text x="{cx}" y="{cy + 4.5}" font-size="13" font-weight="700" fill="#ffffff" text-anchor="middle">{n}</text>')


def note(x, y, text, anchor="start", color=None, bold=False):
    # inline style: a fill attribute would lose to the .note class rule
    fill = f' style="fill:{color}"' if color else ""
    weight = ' font-weight="700"' if bold else ""
    return f'<text x="{x}" y="{y}" class="note"{fill}{weight} text-anchor="{anchor}">{text}</text>'


def callout(x, y, w, lines, title=None, highlight=None):
    """A white box listing items; `highlight` is the index of a line to mark in red."""
    h = 16 + (24 if title else 0) + 20 * len(lines)
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#ffffff" stroke="{INK}" stroke-width="1.5"/>'
    ty = y + 22
    if title:
        s += (f'<text x="{x + w / 2}" y="{ty}" class="lbl" font-weight="700" text-anchor="middle">{title}</text>'
              f'<line x1="{x}" y1="{ty + 8}" x2="{x + w}" y2="{ty + 8}" stroke="{INK}" stroke-width="1"/>')
        ty += 24
    for i, line in enumerate(lines):
        hl = i == highlight
        fill = f' fill="{RED}" font-weight="700"' if hl else ""
        s += f'<text x="{x + 14}" y="{ty + i * 20}" class="lbl"{fill}>{line}</text>'
    return s


def tag(x, y, text, color):
    """A coloured outlined label marking a path, e.g. "auth, synchronous"."""
    w = 7.6 * len(text) + 22
    return (f'<rect x="{x}" y="{y}" width="{w:.0f}" height="26" rx="6" fill="#ffffff" stroke="{color}" stroke-width="2"/>'
            f'<text x="{x + w / 2:.0f}" y="{y + 18}" class="lbl" font-weight="700" fill="{color}" text-anchor="middle">{text}</text>')


DEFS = ("<defs>" + "".join(
    f'<marker id="ah{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
    f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>' for k, c in (("", INK), ("-red", RED), ("-green", GREEN)))
    + "</defs>")
_MARK = {INK: "ah", RED: "ah-red", GREEN: "ah-green"}


def path(pts, dashed=False, both=False, color=INK, width=1.6):
    """An orthogonal (or straight) connector through pts, arrowhead at the end (and start if both)."""
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    dash = ' stroke-dasharray="6,5"' if dashed else ""
    m = _MARK[color]
    start = f' marker-start="url(#{m})"' if both else ""
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash}{start} '
            f'marker-end="url(#{m})" stroke-linejoin="round"/>')


def line(pts, dashed=False, color=INK):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    dash = ' stroke-dasharray="6,5"' if dashed else ""
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6"{dash} stroke-linejoin="round"/>'


def svg(w, h, title, desc, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">\n'
            f'  <title id="title">{title}</title>\n  <desc id="desc">{desc}</desc>\n'
            f'  <style>{STYLE}  </style>\n  {DEFS}\n  <rect width="{w}" height="{h}" fill="#ffffff"/>\n'
            + "\n".join(body) + "\n</svg>\n")


def write(rel_path, content):
    (REPO / rel_path).write_text(content)
    print(f"wrote {rel_path}")
