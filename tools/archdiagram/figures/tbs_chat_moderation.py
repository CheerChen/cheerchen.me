"""TBS Kustamie post: chat moderation with Nova Micro, redrawn from the talk's Kustamie における AI 活用 slide."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archdiagram import *  # noqa: E402,F403

OUT = "content/posts/tbs-kustamie-aws-serverless-large-scale-live-streaming/arch-10-chat-moderation.svg"
CX = 620                     # the IVS Chat -> Firehose -> DynamoDB column
CHAT, HOSE, DDB = 260, 400, 560

b = [icon("mobile", CX, 62, 52, label="Kustamie app"),
     group(200, 130, 880, 530, "cloud", "AWS Cloud")]

# other interactive features also post into IVS Chat
b.append(service_box(230, 190, 230, 290, None, "Other interactive features"))
b.append(icon("ecs", 345, CHAT, label="Amazon ECS"))
b.append(icon("lambda", 345, HOSE, label="AWS Lambda"))
b.append(path([(373, CHAT), (CX - 28, CHAT)]))
b.append(line([(373, HOSE), (500, HOSE), (500, CHAT)]))

# chat flow: app <-> IVS Chat -> Firehose -> DynamoDB
b.append(path([(CX, 116), (CX, CHAT - 28)], both=True))
b.append(note(CX + 12, 190, "WebSocket"))
b.append(icon("ivs", CX, CHAT, label="Amazon IVS Chat"))
b.append(icon("firehose", CX, HOSE, label="Amazon Data Firehose"))
b.append(icon("dynamodb", CX, DDB, label="Amazon DynamoDB"))
b += [path([(CX, CHAT + 52), (CX, HOSE - 28)]), path([(CX, HOSE + 52), (CX, DDB - 28)])]

# moderation: the stream triggers Lambda, which asks Bedrock and acts on the verdict
b.append(icon("lambda", 830, DDB, label="AWS Lambda"))
b.append(icon("bedrock", 1000, DDB, label="Amazon Bedrock"))
b.append(path([(CX + 28, DDB - 10), (802, DDB - 10)]))
b.append(note(725, DDB - 18, "stream", "middle"))
b.append(path([(802, DDB + 10), (CX + 28, DDB + 10)]))
b.append(note(725, DDB + 28, "status update", "middle"))
b.append(path([(858, DDB), (972, DDB)]))
b.append(note(915, DDB - 10, "invoke model", "middle"))
b.append(path([(830, DDB - 28), (830, CHAT), (CX + 28, CHAT)]))
b.append(note(842, 410, "delete message request"))

# staff check the chat content in DynamoDB
b.append(icon("user", 100, DDB, 52, label="Staff"))
b.append(path([(128, DDB), (CX - 28, DDB)]))
b.append(note(300, DDB - 10, "reviews the chat content", "middle"))

write(OUT, svg(1200, 680, "Chat moderation with Amazon Nova Micro",
               "The Kustamie app talks to Amazon IVS Chat over WebSocket; other interactive features on Amazon ECS and "
               "AWS Lambda post to IVS Chat too. Chat messages flow through Amazon Data Firehose into Amazon DynamoDB, "
               "whose stream triggers an AWS Lambda function that invokes a model on Amazon Bedrock, writes a status "
               "update back to DynamoDB and sends a delete message request to IVS Chat. Staff review the chat content "
               "in DynamoDB.", b))
