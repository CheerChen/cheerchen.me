"""Switch 2 GameChat post: tracing with ADOT, Envoy, an OTel Collector and AWS X-Ray."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archdiagram import *  # noqa: E402,F403

OUT = "content/posts/switch-2-gamechat-backend-sfu-dynamodb-consistency/arch-16-observability.svg"
GS, SFU, MID = 130, 310, 220

b = [group(40, 20, 1120, 400, "cloud", "AWS Cloud")]

b.append(band(80, 66, 500, 130, "purple"))
b.append(role(96, 52, "Group server"))
b.append(icon("fargate", 180, GS, label="AWS Fargate"))
b.append(icon("sdk", 400, GS, label=["ADOT SDK", "(Go)"]))
b.append(line([(208, GS), (372, GS)], dashed=True))
b.append(note(290, GS - 10, "runs", "middle"))

b.append(band(80, 246, 500, 130, "pink"))
b.append(role(96, 232, "SFU server"))
b.append(icon("ec2", 180, SFU, label="Amazon EC2"))
b.append(icon("app", 330, SFU, label="SFU"))
b.append(icon("app", 480, SFU, label="Envoy proxy"))
b.append(line([(358, SFU), (452, SFU)]))

b.append(icon("app", 760, MID, label=["OTel Collector", "container"]))
b.append(path([(428, GS), (660, GS), (660, MID - 10), (732, MID - 10)]))
b.append(path([(508, SFU), (660, SFU), (660, MID + 10), (732, MID + 10)]))
b.append(note(600, GS - 10, "traces", "middle"))
b.append(note(600, SFU - 10, "traces", "middle"))

b.append(icon("xray", 1000, MID, label=["AWS X-Ray", "service map"]))
b.append(path([(788, MID), (972, MID)]))

b.append(note(700, 380, "Trace IDs start at the group server and at the SFU's Envoy proxy."))

write(OUT, svg(1200, 440, "Tracing with AWS X-Ray",
               "The group server on Fargate generates traces with the ADOT SDK for Go; the SFU server on EC2 generates "
               "them at its Envoy proxy. Both send traces to an OpenTelemetry Collector container, which exports them to "
               "AWS X-Ray to build the service map.", b))
