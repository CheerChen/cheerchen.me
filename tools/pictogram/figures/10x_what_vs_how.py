"""10x post: the "getting to Shinagawa Station" example as a two-panel comic."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pictogram import *  # noqa: E402,F403

OUT = "content/posts/10x-innovation-culture-program-ask-googler/what-vs-how.svg"

b = [f'<text x="600" y="60" class="title" text-anchor="middle">Set the WHAT, not the HOW</text>']

# Left: micromanagement
b.append(panel(40, 90, 540, 480, "MICROMANAGEMENT", RED))
b.append(ground(70, 550, 500))
b.append(bubble(150, 150, 400, 186, (140, 370), [
    ("1. Take the 6:45 Yamanote Line", "t"),
    ("2. Ride in car No. 3", "t"),
    ("3. Get off at Shinagawa", "t"),
    ("4. Leave via the Takanawa Exit", "t"),
    ("5. Then turn left, and...", "t-dim"),
]))
b.append(person(130, 500, "point", GREEN))
b.append(person(430, 500, "stressed", YELLOW, hair="long"))
b.append(spiky(480, 378))
b.append('<text x="310" y="545" class="cap" text-anchor="middle">The manager dictates every step (the HOW)</text>')

# Right: Google's way
b.append(panel(620, 90, 540, 480, "GOOGLE'S WAY", GREEN))
b.append(area(1040, 500, 110))
b.append(ground(650, 1130, 500))
b.append(station(965, 500, "Shinagawa", clock="7:00"))
b.append(bubble(686, 186, 310, 128, (676, 392), [
    ("Shinagawa Station, 7:00 AM!", "b"),
    ("Not sure how to get there?", "t"),
    ("Let's figure it out together.", "t"),
]))
b.append(person(672, 500, "point", GREEN, scale=0.85))
# arrivals, each on their own route
b.append(trail(712, 728, 488))
b.append(person(755, 500, "walk", GREEN, hair="cap", scale=0.85))
b.append(trail(785, 800, 470))
b.append(bicycle(845, 500))
b.append(person(843, 488, "walk", YELLOW, hair="long", scale=0.85, cyclist=True))
b.append(trail(890, 905, 478))
b.append(person(935, 500, "run", GREEN, scale=0.85))
b.append(person(1050, 500, "cheer", YELLOW, scale=0.85))
b.append(sparkle(1000, 430))
b.append('<text x="890" y="545" class="cap" text-anchor="middle">The team agrees on the goal (the WHAT)</text>')

b.append('<text x="600" y="620" class="cap" text-anchor="middle">The company owns the WHAT. Employees own the HOW.</text>')

write(OUT, svg(1200, 660, "Set the WHAT, not the HOW",
               "Two comic panels. Left: a manager reads out every step of the trip to Shinagawa Station and the team "
               "member is overwhelmed. Right: the manager only says meet at Shinagawa Station at 7:00 and offers help; "
               "people arrive on foot, by bike and running, and celebrate at the station.", b))
