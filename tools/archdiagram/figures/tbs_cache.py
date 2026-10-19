"""TBS Kustamie post: the three cache tiers, redrawn from the talk's 多段キャッシュの利用 slide."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archdiagram import *  # noqa: E402,F403

OUT = "content/posts/tbs-kustamie-aws-serverless-large-scale-live-streaming/arch-08-cache.svg"
Y = 335                      # request row
MONO = "ui-monospace,SFMono-Regular,Menlo,monospace"

b = [icon("users", 85, Y, 56, label=["Many requests", "~12,000 RPS"])]

# 1. API Gateway: the stage answers GET requests from its cache
b.append(service_box(170, 40, 340, 520, "apigw", "Amazon API Gateway"))
b.append(box(235, 120, 230, 70, ["API cache", "(GET only)"], fill="#e3eff9"))
b.append(step(235, 120, 1))
b.append(box(235, Y - 35, 230, 70, "Stage"))
b.append(path([(350, Y - 35), (350, 192)]))
for dy in (-16, 0, 16):
    b.append(path([(117, Y + dy), (233, Y + dy)]))
b.append(path([(350, Y + 35), (350, 520), (85, 520), (85, 410)], dashed=True))
b.append(note(340, 510, "response on a cache hit", "end"))

# 2. Lambda: globals survive a hot start
b.append(service_box(560, 40, 300, 520, "lambda", "AWS Lambda function"))
b.append(box(590, 100, 240, 60, "Compute environment"))
b.append("".join(f'<circle cx="{710 + dx}" cy="205" r="3" fill="{INK}"/>' for dx in (-12, 0, 12)))
b.append(f'<rect x="590" y="250" width="240" height="280" rx="6" fill="#ffffff" stroke="{INK}" stroke-width="1.5"/>'
         f'<text x="710" y="276" class="lbl" text-anchor="middle">Compute environment</text>')
b.append(f'<rect x="605" y="292" width="210" height="222" rx="4" fill="#e3eff9" stroke="{INK}" stroke-width="1.2"/>')
b.append(step(605, 292, 2))
b.append(f'<text x="710" y="318" class="lbl" font-weight="700" text-anchor="middle">Global variables</text>')
code = ["const ID_TO_USER_NAME = {", '  "abcdef": {', '    "name": "test",', '    "ttl": 1778662763', "  }", "}"]
for i, ln in enumerate(code):
    b.append(f'<text x="617" y="{346 + i * 24}" font-size="12.5" style="font-family:{MONO}" xml:space="preserve">{ln}</text>')
b.append(path([(467, Y), (558, Y)]))

# 3. ECS reads through ElastiCache before RDS
b += [line([(830, 130), (900, 130), (900, 390), (830, 390)]), path([(900, Y), (952, Y)])]
b.append(icon("ecs", 980, Y, label="Amazon ECS"))
b.append(icon("rds", 1120, Y, label="Amazon RDS"))
b.append(icon("elasticache", 980, 150, label="Amazon ElastiCache"))
b.append(step(948, 118, 3))
b += [path([(1008, Y), (1092, Y)]), path([(980, Y - 28), (980, 196)])]

write(OUT, svg(1200, 580, "Multi-tier caching",
               "Three cache tiers on the request path. 1: the API Gateway stage answers GET requests from its API "
               "cache and responds straight back on a hit. 2: global variables in a Lambda compute environment, such "
               "as an ID-to-user-name map with a TTL, survive hot starts. 3: Amazon ECS reads through Amazon "
               "ElastiCache before Amazon RDS.", b))
