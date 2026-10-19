"""TBS Kustamie post: architecture overview, redrawn from the talk's アーキテクチャ（概要） slide."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archdiagram import *  # noqa: E402,F403

OUT = "content/posts/tbs-kustamie-aws-serverless-large-scale-live-streaming/arch-01-architecture.svg"
TOP, MID, LOW = 150, 230, 310   # Lambda / API row / Lambda
CHAT, VIDEO = 480, 590          # IVS rows

b = [group(190, 20, 990, 650, "cloud", "AWS Cloud"),
     group(400, 60, 760, 340, "vpc", "Amazon VPC")]

b.append(icon("users", 90, 345, 56, label="Users"))

# Event info: API Gateway -> Lambda functions -> ECS -> ElastiCache / RDS
b.append(icon("apigw", 300, MID, label=["Amazon API", "Gateway"]))
b.append(icon("lambda", 530, TOP, label="AWS Lambda"))
b.append(icon("lambda", 530, LOW, label="AWS Lambda"))
b.append("".join(f'<circle cx="530" cy="{MID - 4 + dy}" r="3" fill="{INK}"/>' for dy in (-10, 0, 10)))
b.append(icon("ecs", 720, MID, label=["Amazon Elastic", "Container Service"]))
b.append(icon("elasticache", 960, TOP, label="Amazon ElastiCache"))
b.append(icon("rds", 960, LOW, label=["Amazon RDS", "Aurora Serverless v2"]))
b += [line([(328, MID), (450, MID)]),
      path([(450, MID), (450, TOP), (502, TOP)]), path([(450, MID), (450, LOW), (502, LOW)]),
      line([(558, TOP), (620, TOP), (620, LOW), (558, LOW)]), path([(620, MID), (692, MID)]),
      line([(748, MID), (840, MID)]),
      path([(840, MID), (840, TOP), (932, TOP)]), path([(840, MID), (840, LOW), (932, LOW)])]

# Video, audio and real-time data: IVS Chat and IVS, outside the VPC
b.append(icon("ivs", 480, CHAT, label="Amazon IVS Chat"))
b.append(icon("ivs", 480, VIDEO, label="Amazon IVS"))
b.append(path([(720, 302), (720, CHAT), (508, CHAT)]))
b.append(note(614, CHAT - 10, "interactive data", "middle"))

# Users' three connections
b.append(path([(122, 330), (150, 330), (150, MID), (272, MID)]))
b.append(note(214, MID - 10, "event info", "middle"))
b.append(path([(122, 350), (215, 350), (215, CHAT), (452, CHAT)]))
b.append(note(335, CHAT - 10, "WebSocket", "middle"))
b.append(path([(122, 366), (170, 366), (170, VIDEO), (452, VIDEO)]))
b.append(note(335, VIDEO - 10, "video", "middle"))

write(OUT, svg(1200, 690, "Kustamie architecture overview",
               "Users reach Kustamie on two paths. Event info goes through Amazon API Gateway to AWS Lambda functions "
               "in a VPC, which call application services on Amazon ECS backed by Amazon ElastiCache and Amazon RDS "
               "(Aurora Serverless v2). Real-time data uses Amazon IVS Chat over WebSocket and video streams through "
               "Amazon IVS; ECS pushes interactive data into IVS Chat.", b))
