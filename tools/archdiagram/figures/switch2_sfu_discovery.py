"""Switch 2 GameChat post: how a client is pointed at an SFU server."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archdiagram import *  # noqa: E402,F403

OUT = "content/posts/switch-2-gamechat-backend-sfu-dynamodb-consistency/arch-12-sfu-discovery.svg"
ROW, SFU = 240, 470

b = [group(200, 20, 970, 590, "cloud", "AWS Cloud"),
     group(230, 60, 920, 260, "region", "Admin Region")]

b.append(band(340, 180, 160, 120, "purple"))
b.append(icon("fargate", 420, ROW, label="Group server"))
b.append(icon("dynamodb", 640, ROW, label="Amazon DynamoDB"))
b.append(band(820, 180, 180, 120, "blue"))
b.append(icon("fargate", 910, ROW, label="SFU instance manager"))
b.append(callout(540, 76, 200, ["Instance A: N connections", "Instance B: N-1 connections", "Instance Z: N+1 connections"],
                 title="instances", highlight=1))
b.append(line([(640, 168), (640, 212)], dashed=True))
b.append(path([(882, ROW), (668, ROW)], color=RED))
b.append(note(775, ROW - 10, "updates", "middle", RED))
b.append(path([(448, ROW), (612, ROW)]))
b.append(note(530, ROW - 10, "reads", "middle"))

# SFU servers, watched by the instance manager
regions = [(330, "Region 1", "Instance A"), (600, "Region 2", "Instance B"), (900, "Region N", "Instance Z")]
for x, name, inst in regions:
    picked = inst == "Instance B"
    b.append(group(x, 390, 230, 160, "region", name))
    b.append(icon("ec2", x + 115, SFU, label=["SFU server", inst]))
    if picked:
        b.append(f'<rect x="{x + 81}" y="{SFU - 34}" width="68" height="68" rx="8" fill="none" stroke="{RED}" stroke-width="2.5"/>')
b.append("".join(f'<circle cx="{865 + dx}" cy="{SFU}" r="3" fill="{INK}"/>' for dx in (-14, 0, 14)))
b.append(line([(910, 302), (910, 352), (445, 352)], color=RED))
for x, _, _ in regions:
    b.append(path([(x + 115, 352), (x + 115, 428)], color=RED))
b.append(tag(950, 338, "monitors instances", RED))

# 1 ask, 2 answer, 3 connect
b.append(switch(95, SFU))
b.append(path([(85, SFU - 24), (85, ROW - 12), (392, ROW - 12)]))
b.append(step(252, ROW - 30, 1))
b.append(note(269, ROW - 25, "which instance?"))
b.append(path([(392, ROW + 14), (105, ROW + 14), (105, SFU - 24)]))
b.append(step(252, ROW + 36, 2))
b.append(note(269, ROW + 41, "use instance B"))
b.append(path([(135, SFU), (165, SFU), (165, 590), (715, 590), (715, 552)]))
b.append(step(300, 590, 3))
b.append(note(318, 584, "WebRTC connection to instance B"))

write(OUT, svg(1200, 630, "SFU server discovery",
               "The SFU instance manager monitors SFU servers in every region and keeps their connection counts in "
               "DynamoDB: instance A has N connections, instance B N-1, instance Z N+1. The Switch 2 asks the group "
               "server which instance to use (1); the group server reads DynamoDB and returns instance B, the least "
               "loaded (2); the Switch 2 then opens a WebRTC connection to instance B in Region 2 (3).", b))
