"""TBS Kustamie post: the participation API split into a sync and an async path, from the 非同期化 slide."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archdiagram import *  # noqa: E402,F403

OUT = "content/posts/tbs-kustamie-aws-serverless-large-scale-live-streaming/arch-09-async.svg"
Y = 170
SPLIT = 800                  # sync | async boundary


def brace(x1, x2, y, label):
    """A bracket under a span of the flow, labelled below its middle."""
    mid = (x1 + x2) / 2
    return (f'<path d="M{x1},{y - 10} V{y} H{x2} V{y - 10} M{mid},{y} V{y + 10}" fill="none" stroke="{INK}" stroke-width="1.6"/>'
            f'<text x="{mid}" y="{y + 32}" class="lbl" font-weight="700" text-anchor="middle">{label}</text>')


b = []
# synchronous: what the user needs before playback starts
b.append(icon("apigw", 80, Y, label=["Amazon API", "Gateway"]))
b.append(icon("lambda", 220, Y, label="AWS Lambda"))
b.append(service_box(300, 92, 470, 156, "stepfunctions", "AWS Step Functions (Express)"))
for x, text in ((322, "Generate UserID"), (472, "Issue IVS token"), (622, "Send SQS record")):
    b.append(box(x, Y - 24, 130, 48, text))
b += [path([(108, Y), (192, Y)]), path([(248, Y), (298, Y)]),
      path([(452, Y), (470, Y)]), path([(602, Y), (620, Y)])]
b.append(note(150, Y - 10, "integrate", "middle"))
b.append(note(273, Y - 10, "invoke", "middle"))

# asynchronous: everything that can wait
b.append(f'<line x1="{SPLIT}" y1="60" x2="{SPLIT}" y2="270" stroke="{DIM}" stroke-width="1.5"/>')
b.append(path([(752, Y), (842, Y)], dashed=True))
b.append(icon("sqs", 870, Y, label="Amazon SQS"))
b.append(icon("lambda", 1010, Y, label="AWS Lambda"))
b.append(icon("ecs", 1135, Y, label="Amazon ECS"))
b += [path([(898, Y), (982, Y)]), path([(1038, Y), (1107, Y)])]
b.append(note(940, Y - 10, "consume", "middle"))

b.append(brace(40, SPLIT - 20, 300, "synchronous (~100 ms)"))
b.append(brace(SPLIT + 20, 1170, 300, "asynchronous (~10,000 ms)"))

# what the split bought
b.append(note(600, 392, "response time after these changes", "middle"))
b.append(f'<rect x="250" y="410" width="280" height="56" rx="8" fill="{DIM}"/>'
         f'<text x="390" y="444" class="role" fill="#ffffff" text-anchor="middle">Before: max 12,000 ms</text>')
b.append(f'<path d="M560,438 H624 M610,424 L628,438 L610,452" fill="none" stroke="{DIM}" stroke-width="4" '
         f'stroke-linecap="round" stroke-linejoin="round"/>')
b.append(f'<rect x="660" y="410" width="280" height="56" rx="8" fill="#ec7211"/>'
         f'<text x="800" y="444" class="role" fill="#ffffff" text-anchor="middle">After: avg ~150 ms</text>')

write(OUT, svg(1200, 490, "Going async",
               "The participation API split in two. Synchronous, about 100 ms: Amazon API Gateway integrates with AWS "
               "Lambda, which invokes an AWS Step Functions Express workflow that generates the UserID, issues the IVS "
               "token and sends an SQS record. Asynchronous, about 10,000 ms: Amazon SQS is consumed by AWS Lambda, "
               "which calls Amazon ECS. Response time went from a maximum of 12,000 ms to an average of about 150 ms.", b))
