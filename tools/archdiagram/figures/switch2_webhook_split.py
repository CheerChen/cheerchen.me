"""Switch 2 GameChat post: auth webhooks stay synchronous, event webhooks go through a queue."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archdiagram import *  # noqa: E402,F403

OUT = "content/posts/switch-2-gamechat-backend-sfu-dynamodb-consistency/arch-15-webhook-split.svg"
ROW, SFU = 150, 430

b = [group(200, 20, 970, 540, "cloud", "AWS Cloud"),
     group(230, 60, 920, 190, "region", "Admin Region")]
b.append(band(270, 96, 860, 130, "purple"))
b.append(icon("fargate", 400, ROW, label="Group server"))
b.append(icon("dynamodb", 560, ROW, label="Amazon DynamoDB"))
b.append(icon("fargate", 720, ROW, label="Async worker"))
b.append(icon("sqs", 880, ROW, label="Amazon SQS"))
b.append(icon("apigw", 1040, ROW, label=["Amazon API", "Gateway"]))
b += [path([(428, ROW), (532, ROW)]), path([(692, ROW), (588, ROW)]),
      path([(852, ROW), (748, ROW)]), path([(1012, ROW), (908, ROW)])]

regions = [(300, "Region 1"), (570, "Region 2"), (880, "Region N")]
for x, name in regions:
    b.append(group(x, 340, 230, 170, "region", name))
    b.append(icon("ec2", x + 115, SFU, label="SFU server"))
b.append("".join(f'<circle cx="{840 + dx}" cy="{SFU}" r="3" fill="{INK}"/>' for dx in (-14, 0, 14)))

# auth: synchronous, straight to the group server
b.append(path([(400, 402), (400, 218)], color=RED, width=2.4))
b.append(tag(236, 262, "auth: synchronous", RED))
# events: asynchronous, buffered by API Gateway and SQS
b.append(path([(430, 402), (430, 286), (1040, 286), (1040, 218)], color=GREEN, width=2.4))
b.append(tag(700, 296, "events: asynchronous", GREEN))

b.append(switch(95, SFU))
b.append(path([(135, SFU), (387, SFU)]))
b.append(note(150, SFU - 12, "events"))

write(OUT, svg(1200, 580, "Splitting the webhooks",
               "The SFU server sends auth webhooks synchronously straight to the group server, because they gate the "
               "user's join. Event webhooks go asynchronously through Amazon API Gateway and Amazon SQS to a separate "
               "async worker, which writes to DynamoDB, keeping that load off the auth path.", b))
