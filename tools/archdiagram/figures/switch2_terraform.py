"""Switch 2 GameChat post: one Terraform module plus per-region config deploys every region."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archdiagram import *  # noqa: E402,F403

OUT = "content/posts/switch-2-gamechat-backend-sfu-dynamodb-consistency/arch-17-terraform.svg"
R1, R2, SFU, MOD, BUS = 122, 222, 352, 600, 462

b = [group(120, 20, 1050, 420, "cloud", "AWS Cloud")]
b.append(icon("cloudfront", 190, R1, 40, label=["Amazon", "CloudFront"]))
b.append(group(260, 50, 850, 222, "region", "Admin Region"))
for x, key, label in ((330, "alb", ["Application Load", "Balancer"]), (460, "fargate", "AWS Fargate"),
                      (590, "sqs", "Amazon SQS"), (720, "fargate", "AWS Fargate"), (850, "sqs", "Amazon SQS"),
                      (990, "apigw", ["Amazon API", "Gateway"])):
    b.append(icon(key, x, R1, 40, label=label))
b.append(icon("dynamodb", 590, R2, 40, label="Amazon DynamoDB"))
b.append(icon("fargate", 990, R2, 40, label="AWS Fargate"))

regions = [(150, "Region 1"), (420, "Region 2"), (870, "Region N")]
for x, name in regions:
    b.append(group(x, 292, 230, 130, "region", name))
    b.append(icon("ec2", x + 65, SFU, 40, label="Amazon EC2"))
    b.append(icon("transcribe", x + 165, SFU, 40, label=["Amazon", "Transcribe"]))
b.append("".join(f'<circle cx="{760 + dx}" cy="{SFU}" r="3" fill="{INK}"/>' for dx in (-12, 0, 12)))

# Terraform: per-region configs feed one module, which deploys every region together
b.append(f'<rect x="230" y="490" width="820" height="200" rx="8" fill="none" stroke="{INK}" stroke-width="1.5" stroke-dasharray="6,5"/>')
b.append(f'<text x="246" y="514" class="grp">Terraform</text>')
b.append(icon("json", 330, MOD, label=["sfu-region", "module"]))
confs = [(538, "region-1.conf"), (588, "region-2.conf"), (662, "region-N.conf")]
for y, name in confs:
    b.append(icon("document", 560, y, 30))
    b.append(f'<text x="584" y="{y + 5}" class="lbl">{name}</text>')
    b.append(line([(543, y), (500, y)]))
b.append("".join(f'<circle cx="560" cy="{622 + dy}" r="2.5" fill="{INK}"/>' for dy in (-6, 2, 10)))
b.append(line([(500, confs[0][0]), (500, confs[-1][0])]))
b.append(path([(500, MOD), (360, MOD)]))
b.append(line([(330, MOD - 30), (330, BUS)]))
b.append(line([(265, BUS), (985, BUS)]))
for x, _ in regions:
    b.append(path([(x + 115, BUS), (x + 115, 424)]))

# the Admin Region has its own code, deployed in the same run
b.append(icon("source-code", 800, MOD, label=["Admin Region", "code"]))
b.append(path([(800, MOD - 30), (800, 476), (1140, 476), (1140, 160), (1112, 160)]))
b.append(tag(900, 588, "deploy all at once", RED))
b.append(note(1035, 640, "new region = new config file", "end"))

write(OUT, svg(1200, 710, "One Terraform module for every region",
               "The per-region SFU resources (EC2, Transcribe) are one Terraform module. Each region only adds a "
               "config file, region-1.conf to region-N.conf, which feeds the module; the module deploys Region 1 to N. "
               "The Admin Region's services have their own code, and everything is deployed in one run, so adding or "
               "removing a region is a config change.", b))
