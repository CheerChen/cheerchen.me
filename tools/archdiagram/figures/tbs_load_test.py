"""TBS Kustamie post: k6 load-test topology plus the sample result shown on the talk's 負荷試験の方法 slide."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archdiagram import *  # noqa: E402,F403

OUT = "content/posts/tbs-kustamie-aws-serverless-large-scale-live-streaming/arch-05-load-test.svg"
MID, W1, W2 = 270, 170, 370
MONO = "ui-monospace,SFMono-Regular,Menlo,monospace"

b = [group(20, 20, 750, 480, "cloud", "AWS Cloud"),
     group(45, 70, 360, 400, "account", "Load-test account"),
     group(435, 70, 310, 400, "account", "Kustamie account")]

# load generators: one manager drives the k6 workers
b.append(icon("ec2", 130, MID, label=["Amazon EC2", "manager, t3.medium"]))
b.append(icon("ec2", 300, W1, label=["Amazon EC2", "k6 worker, c6i.2xlarge"]))
b.append(icon("ec2", 300, W2, label=["Amazon EC2", "k6 worker, c6i.2xlarge"]))
b.append(path([(158, MID), (200, MID), (200, W1), (272, W1)]))
b.append(path([(200, MID), (200, W2), (272, W2)]))
b.append(note(225, 452, "large scale: 5,000 - 60,000 VU", "middle"))

# target: the client API
b.append(icon("apigw", 530, MID, label=["Amazon API", "Gateway"]))
b.append(icon("lambda", 670, MID, label="AWS Lambda"))
b.append(path([(328, W1), (420, W1), (420, MID - 8), (502, MID - 8)]))
b.append(path([(328, W2), (420, W2), (420, MID + 8), (502, MID + 8)]))
b.append(path([(558, MID), (642, MID)]))
b.append(note(470, W1 - 10, "HTTP load", "middle"))

# sample k6 summary from the slide
b.append(f'<rect x="800" y="40" width="380" height="440" rx="10" fill="{INK}"/>')
b.append(f'<text x="824" y="78" class="grp" fill="#ffffff">k6 result sample</text>')
rows = [("http_req_duration", "#ffffff"), ("  avg=9.09ms p(95)=10.8ms", "#c9d1d9"), ("  max=4.09s", "#c9d1d9"), ("", None),
        ("iteration_duration", "#ffffff"), ("  avg=5.04s  p(95)=5.01s", "#c9d1d9"), ("  max=16.36s", "#ff8f7a"), ("", None),
        ("http_req_failed  0.00%", "#c9d1d9"), ("vus_max          30000", "#c9d1d9")]
for i, (text, color) in enumerate(rows):
    if text:
        weight = ' font-weight="700"' if color in ("#ffffff", "#ff8f7a") else ""
        b.append(f'<text x="824" y="{120 + i * 34}" font-size="15" style="font-family:{MONO}" fill="{color}"{weight} '
                 f'xml:space="preserve">{text}</text>')
b.append(note(824, 458, "p95 looks fine; the max is the long tail.", color="#c9d1d9"))

write(OUT, svg(1200, 520, "k6 load-test topology",
               "A load-test account separate from the Kustamie account: a t3.medium EC2 manager drives c6i.2xlarge EC2 "
               "k6 workers that send HTTP load to Amazon API Gateway and AWS Lambda in the Kustamie account, for "
               "large-scale runs of 5,000 to 60,000 virtual users. A sample k6 summary: http_req_duration avg 9.09 ms, "
               "p95 10.8 ms, max 4.09 s; iteration_duration p95 5.01 s but max 16.36 s; 0.00% failed; 30,000 VUs max.", b))
