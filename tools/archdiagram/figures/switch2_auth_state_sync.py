"""Switch 2 GameChat post: SFU servers authenticate joins and sync user state through the group server."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archdiagram import *  # noqa: E402,F403

OUT = "content/posts/switch-2-gamechat-backend-sfu-dynamodb-consistency/arch-13-auth-state-sync.svg"
ROW, SFU = 170, 430

b = [group(200, 20, 970, 540, "cloud", "AWS Cloud"),
     group(330, 60, 480, 200, "region", "Admin Region")]
b.append(band(360, 100, 420, 140, "purple"))
b.append(icon("fargate", 470, ROW, label="Group server"))
b.append(icon("dynamodb", 680, ROW, label="Amazon DynamoDB"))
b.append(path([(498, ROW), (652, ROW)]))
b.append(tag(392, 110, "authenticate", RED))
b.append(tag(624, 110, "update state", INK))

regions = [(330, "Region 1"), (600, "Region 2"), (900, "Region N")]
for x, name in regions:
    b.append(group(x, 340, 230, 170, "region", name))
    b.append(icon("ec2", x + 115, SFU, label="SFU server"))
b.append("".join(f'<circle cx="{865 + dx}" cy="{SFU}" r="3" fill="{INK}"/>' for dx in (-14, 0, 14)))

# the SFU server reports to the group server
b.append(path([(445, 402), (445, 222)], width=3))
b.append(note(458, 290, "webhooks", bold=True))
b.append(note(458, 308, "join: check instance, group, access token"))
b.append(note(458, 326, "state: join, leave, drop, rejoin"))

b.append(switch(95, SFU))
b.append(path([(135, SFU), (417, SFU)]))
b.append(note(150, SFU - 12, "events"))

write(OUT, svg(1200, 580, "Authentication and state sync",
               "The Switch 2 sends events to its SFU server in Region 1. The SFU server calls the group server in "
               "the Admin Region by webhook: on join it checks the target instance, group membership and access token; "
               "afterwards it forwards state changes such as join, leave, drop and rejoin. The group server writes the "
               "state to DynamoDB.", b))
