"""Switch 2 GameChat post: the auth webhook flow between client, SFU server and group server."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archdiagram import *  # noqa: E402,F403

OUT = "content/posts/switch-2-gamechat-backend-sfu-dynamodb-consistency/arch-14-webhook-auth.svg"
Y = 270
SW, SFU, GS = 120, 560, 1000

b = ['<text x="40" y="44" class="grp">Auth webhook flow</text>']
b.append(switch(SW, Y))
b.append(icon("ec2", SFU, Y, label="SFU server"))
b.append(icon("fargate", GS, Y, label="Group server"))

b.append(path([(SW + 46, Y - 12), (SFU - 32, Y - 12)]))
b.append(step(200, Y - 34, 1))
b.append(note(218, Y - 29, "WebRTC connection request"))
b.append(path([(SFU - 32, Y + 14), (SW + 46, Y + 14)]))
b.append(step(200, Y + 38, 5))
b.append(note(218, Y + 43, "connected, media starts"))

b.append(path([(SFU + 32, Y - 12), (GS - 32, Y - 12)]))
b.append(step(640, Y - 34, 2))
b.append(note(658, Y - 29, "auth request"))
b.append(path([(GS - 32, Y + 14), (SFU + 32, Y + 14)]))
b.append(step(640, Y + 38, 4))
b.append(note(658, Y + 43, "200 OK"))

# 3: the group server checks the request
b.append(path([(GS + 30, Y - 14), (GS + 70, Y - 14), (GS + 70, Y + 14), (GS + 32, Y + 14)]))
b.append(step(GS + 96, Y, 3))
b.append(note(GS + 113, Y + 5, "check"))

b.append(callout(700, 40, 200, ["user info", "target instance", "timestamp", "access token", "WebRTC settings", "..."],
                 title="auth request carries"))
b.append(line([(760, 204), (760, Y - 14)], dashed=True))

write(OUT, svg(1200, 360, "Auth webhook flow",
               "1: the Switch 2 sends a WebRTC connection request to the SFU server. 2: the SFU server sends an auth "
               "request to the group server, carrying user info, target instance, timestamp, access token and WebRTC "
               "settings. 3: the group server checks it. 4: it answers 200 OK. 5: the SFU server completes the "
               "connection and media starts.", b))
