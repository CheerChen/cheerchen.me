"""Switch 2 GameChat post: system architecture, redrawn from the talk's 構成図 slide."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archdiagram import *  # noqa: E402,F403

OUT = "content/posts/switch-2-gamechat-backend-sfu-dynamodb-consistency/arch-07-system-architecture.svg"
ROW = 150      # group server row
DDB = 340      # DynamoDB / SFU instance manager row
EC2 = 585      # SFU server row


b = []
b.append(group(190, 20, 990, 660, "cloud", "AWS Cloud"))

# Control plane: Admin Region
b.append(group(340, 60, 820, 400, "region", "Admin Region (control plane)"))
b.append(band(225, 100, 90, 120, "purple"))
b.append(band(360, 100, 785, 120, "purple"))
b.append(role(600, 84, "Group server"))
b.append(icon("cloudfront", 270, ROW, label=["Amazon", "CloudFront"]))
b.append(icon("alb", 420, ROW, label=["Application Load", "Balancer"]))
b.append(icon("fargate", 545, ROW, label="AWS Fargate"))
b.append(icon("sqs", 670, ROW, label="Amazon SQS"))
b.append(icon("fargate", 800, ROW, label="AWS Fargate"))
b.append(icon("sqs", 930, ROW, label="Amazon SQS"))
b.append(icon("apigw", 1065, ROW, label=["Amazon API", "Gateway"]))
b += [path([(298, ROW), (392, ROW)]), path([(448, ROW), (517, ROW)]), path([(573, ROW), (642, ROW)]),
      path([(698, ROW), (772, ROW)]), path([(902, ROW), (828, ROW)]), path([(1037, ROW), (958, ROW)])]

b.append(icon("dynamodb", 670, DDB, label="Amazon DynamoDB"))
b.append(path([(545, 214), (545, DDB), (642, DDB)]))
b.append(path([(800, 214), (800, 270), (670, 270), (670, 312)]))

b.append(band(900, 290, 245, 140, "blue"))
b.append(role(916, 270, "SFU instance manager"))
b.append(icon("fargate", 1020, DDB, label="AWS Fargate"))
b.append(path([(992, DDB), (698, DDB)]))

# Media plane: one SFU server per region
b.append(band(335, 495, 830, 170, "pink"))
b.append(role(200, 456, "SFU server"))
b.append(f'<text x="206" y="506" class="note">media plane</text>')
regions = [(345, "Region 1", False), (605, "Region 2", True), (915, "Region N", True)]
for x, name, dashed in regions:
    b.append(group(x, 510, 240, 140, "region", name))
    b.append(icon("ec2", x + 70, EC2, label="Amazon EC2"))
    b.append(icon("transcribe", x + 175, EC2, label=["Amazon", "Transcribe"]))
    b.append(path([(x + 98, EC2), (x + 147, EC2)], dashed=dashed))
b.append("".join(f'<circle cx="{870 + dx}" cy="{EC2}" r="3" fill="{INK}"/>' for dx in (-14, 0, 14)))
# the instance manager watches every SFU server
b.append(line([(1020, 396), (1020, 482), (415, 482)]))
for x, _, _ in regions:
    b.append(path([(x + 70, 482), (x + 70, 508)]))
b.append(f'<text x="1032" y="474" class="note">monitors instances</text>')

# Client
b.append(switch(95, EC2))
b.append(path([(95, EC2 - 24), (95, ROW), (242, ROW)]))
b.append(f'<text x="106" y="{ROW - 10}" class="note">API requests</text>')
b.append(path([(137, EC2), (387, EC2)], both=True))
b.append(f'<text x="200" y="{EC2 - 24}" class="note">voice / video</text>')
b.append(f'<text x="200" y="{EC2 - 9}" class="note">(WebRTC)</text>')
b.append(line([(305, EC2), (305, 668), (985, 668)], dashed=True))
b.append(path([(675, 668), (675, 652)], dashed=True))
b.append(path([(985, 668), (985, 652)], dashed=True))

write(OUT, svg(1200, 700, "Switch 2 GameChat system architecture",
               "Control plane in an Admin Region: CloudFront, an Application Load Balancer and Fargate services "
               "linked by SQS and API Gateway form the group server, backed by DynamoDB; a Fargate SFU instance "
               "manager also writes to DynamoDB and monitors SFU servers. Media plane: in each of Regions 1 to N, "
               "an EC2 SFU server feeds Amazon Transcribe. The Switch 2 calls the API through CloudFront and "
               "exchanges voice and video with an SFU server over WebRTC.", b))
